"""
Market scanner: fetch → snapshot → AI analyze → signal → opportunity → (optional) bet
Everything is persisted to the database at every step.
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta

from config import settings
from services.polymarket import get_active_markets, place_market_order
from services.claude_analyzer import analyze_market as claude_analyze
from services.kelly import kelly_bet, confidence_multiplier
from database import AsyncSessionLocal
from models import MarketSnapshot, AIAnalysis, Signal, Opportunity, Bet, ScanRun

logger = logging.getLogger(__name__)


async def _save_snapshot(market: dict, scan_id: str) -> str:
    snapshot_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as db:
        db.add(MarketSnapshot(
            id=snapshot_id,
            scan_id=scan_id,
            market_id=market["id"],
            question=market["question"],
            description=market.get("description"),
            category=market.get("category"),
            yes_price=market["yes_price"],
            no_price=market["no_price"],
            volume_24h=market.get("volume_24h", 0),
            liquidity=market.get("liquidity", 0),
            end_date=market.get("end_date"),
            yes_token_id=market.get("yes_token_id"),
            no_token_id=market.get("no_token_id"),
            raw_data=market,
        ))
        await db.commit()
    return snapshot_id


async def _save_ai_analysis(market_id, snapshot_id, scan_id, result, latency_ms):
    async with AsyncSessionLocal() as db:
        db.add(AIAnalysis(
            id=str(uuid.uuid4()),
            market_id=market_id,
            snapshot_id=snapshot_id,
            scan_id=scan_id,
            model=result.get("model", "unknown"),
            probability_yes=result.get("probability_yes"),
            confidence=result.get("confidence"),
            factors_yes=result.get("factors_yes"),
            factors_no=result.get("factors_no"),
            reasoning=result.get("reasoning"),
            market_insight=result.get("market_insight"),
            raw_response=json.dumps(result),
            success=result.get("success", False),
            error=result.get("error"),
            latency_ms=latency_ms,
        ))
        await db.commit()


async def _save_signal(signal_data: dict) -> str:
    signal_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as db:
        db.add(Signal(
            id=signal_id,
            scan_id=signal_data["scan_id"],
            snapshot_id=signal_data.get("snapshot_id"),
            market_id=signal_data["market_id"],
            market_question=signal_data["question"],
            outcome=signal_data["outcome"],
            yes_price=signal_data.get("yes_price"),
            no_price=signal_data.get("no_price"),
            market_price=signal_data["current_price"],
            claude_probability=signal_data.get("claude_probability"),
            consensus_probability=signal_data.get("consensus_probability"),
            claude_confidence=signal_data.get("claude_confidence"),
            consensus_confidence=signal_data.get("confidence"),
            edge=signal_data.get("edge", 0),
            kelly_full=signal_data.get("kelly_details", {}).get("kelly_full"),
            kelly_bet_usdc=signal_data.get("kelly_bet_usdc", 0),
            is_profitable=signal_data.get("is_profitable", False),
            action_taken="none",
        ))
        await db.commit()
    return signal_id


async def _save_opportunity(opp: dict):
    async with AsyncSessionLocal() as db:
        record = Opportunity(
            id=str(uuid.uuid4()),
            signal_id=opp.get("signal_id"),
            market_id=opp["market_id"],
            market_question=opp["question"],
            outcome=opp["outcome"],
            current_price=opp["current_price"],
            claude_probability=opp.get("claude_probability"),
            consensus_probability=opp["consensus_probability"],
            edge=opp["edge"],
            kelly_bet_usdc=opp["kelly_bet_usdc"],
            claude_reasoning=opp.get("claude_reasoning"),
            confidence=opp["confidence"],
            status="pending",
            expires_at=datetime.utcnow() + timedelta(hours=6),
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record


async def analyze_single_market(market: dict, scan_id: str):
    snapshot_id = await _save_snapshot(market, scan_id)

    t0 = time.monotonic()
    claude_result = await claude_analyze(market)
    latency_ms = int((time.monotonic() - t0) * 1000)

    if isinstance(claude_result, Exception):
        claude_result = {"success": False, "error": str(claude_result), "model": "claude-opus-4-6"}

    await _save_ai_analysis(market["id"], snapshot_id, scan_id, claude_result, latency_ms)

    if not claude_result.get("success") or claude_result.get("probability_yes") is None:
        return None

    prob = claude_result["probability_yes"]
    confidence = claude_result.get("confidence", "LOW")

    edge_yes = prob - market["yes_price"]
    outcome = "YES" if edge_yes >= 0 else "NO"
    bet_price = market["yes_price"] if outcome == "YES" else market["no_price"]
    bet_prob = prob if outcome == "YES" else 1 - prob
    edge = abs(edge_yes)

    conf_mult = confidence_multiplier(confidence)
    kelly = kelly_bet(
        probability=bet_prob,
        market_price=bet_price,
        bankroll=settings.bankroll_usdc,
        fraction=settings.kelly_fraction * conf_mult,
    )

    is_profitable = edge >= settings.min_edge and kelly["bet_usdc"] >= 1.0

    opp_data = {
        "scan_id": scan_id,
        "snapshot_id": snapshot_id,
        "market_id": market["id"],
        "question": market["question"],
        "outcome": outcome,
        "yes_price": market["yes_price"],
        "no_price": market["no_price"],
        "current_price": bet_price,
        "claude_probability": prob,
        "consensus_probability": prob,
        "claude_confidence": confidence,
        "confidence": confidence,
        "edge": edge,
        "kelly_bet_usdc": kelly["bet_usdc"],
        "kelly_details": kelly,
        "claude_reasoning": claude_result.get("reasoning", ""),
        "yes_token_id": market.get("yes_token_id"),
        "no_token_id": market.get("no_token_id"),
        "is_profitable": is_profitable,
    }

    signal_id = await _save_signal(opp_data)
    opp_data["signal_id"] = signal_id

    if not is_profitable:
        return None

    return opp_data


async def execute_bet(opportunity_id: str, opp: dict) -> dict:
    token_id = opp["yes_token_id"] if opp["outcome"] == "YES" else opp["no_token_id"]
    result = await place_market_order(token_id=token_id, side="BUY", amount_usdc=opp["kelly_bet_usdc"])

    async with AsyncSessionLocal() as db:
        opp_record = await db.get(Opportunity, opportunity_id)
        if opp_record:
            opp_record.status = "executed" if result.get("success") else "failed"

        if opp.get("signal_id"):
            from sqlalchemy import select
            q = await db.execute(select(Signal).where(Signal.id == opp["signal_id"]))
            sig = q.scalar_one_or_none()
            if sig:
                sig.action_taken = "auto_bet" if settings.auto_bet_enabled else "manual_bet"

        db.add(Bet(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity_id,
            signal_id=opp.get("signal_id"),
            market_id=opp["market_id"],
            market_question=opp["question"],
            outcome=opp["outcome"],
            amount_usdc=opp["kelly_bet_usdc"],
            price_at_bet=opp["current_price"],
            tx_hash=result.get("tx_hash"),
            order_id=result.get("order_id"),
            status="placed" if result.get("success") else "failed",
        ))
        await db.commit()

    return result


async def run_scan() -> list[dict]:
    scan_id = str(uuid.uuid4())
    t_start = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        db.add(ScanRun(id=scan_id, status="running"))
        await db.commit()

    logger.info(f"[scan:{scan_id[:8]}] Starting...")
    errors = 0
    markets = []
    results = []
    opportunities_found = []

    try:
        markets = await get_active_markets(limit=50)
        logger.info(f"[scan:{scan_id[:8]}] {len(markets)} markets fetched")

        sem = asyncio.Semaphore(3)  # Limit concurrent Claude calls

        async def safe(m):
            nonlocal errors
            async with sem:
                try:
                    return await analyze_single_market(m, scan_id)
                except Exception as e:
                    logger.error(f"Error: {e}")
                    errors += 1
                    return None

        results = await asyncio.gather(*[safe(m) for m in markets])

        for opp in results:
            if opp is None:
                continue
            record = await _save_opportunity(opp)
            opp["opportunity_id"] = record.id
            opportunities_found.append(opp)
            logger.info(
                f"[scan:{scan_id[:8]}] OPPORTUNITY: {opp['question'][:50]} | "
                f"{opp['outcome']} | Edge {opp['edge']:.1%} | ${opp['kelly_bet_usdc']:.2f}"
            )
            if settings.auto_bet_enabled:
                await execute_bet(record.id, opp)

        status = "completed"
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        status = "failed"
        raise
    finally:
        duration = (datetime.utcnow() - t_start).total_seconds()
        async with AsyncSessionLocal() as db:
            run = await db.get(ScanRun, scan_id)
            if run:
                run.status = status
                run.markets_fetched = len(markets)
                run.markets_analyzed = len([r for r in results if r is not None])
                run.signals_generated = len(markets)
                run.opportunities_found = len(opportunities_found)
                run.bets_placed = len(opportunities_found) if settings.auto_bet_enabled else 0
                run.errors = errors
                run.duration_seconds = duration
                run.finished_at = datetime.utcnow()
            await db.commit()

    logger.info(f"[scan:{scan_id[:8]}] Done in {duration:.1f}s | opportunities={len(opportunities_found)}")
    return opportunities_found
