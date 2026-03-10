import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db
from models import Opportunity
from services.scanner import run_scan, execute_bet, request_stop, get_scan_state
from config import settings

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


@router.get("")
async def list_opportunities(
    status: str = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    q = select(Opportunity).order_by(desc(Opportunity.created_at)).limit(limit)
    if status:
        q = q.where(Opportunity.status == status)
    result = await db.execute(q)
    items = result.scalars().all()
    return {"opportunities": [_serialize(o) for o in items]}


@router.post("/scan")
async def trigger_scan():
    """Manually trigger a market scan (runs in background)."""
    state = get_scan_state()
    if state["running"]:
        raise HTTPException(status_code=409, detail="Scan already running")
    asyncio.create_task(run_scan())
    return {"started": True}


@router.get("/scan/status")
async def scan_status():
    """Return current scan state."""
    return get_scan_state()


@router.post("/scan/stop")
async def stop_scan():
    """Request the running scan to stop."""
    state = get_scan_state()
    if not state["running"]:
        raise HTTPException(status_code=400, detail="No scan running")
    request_stop()
    return {"stopping": True}


@router.post("/{opportunity_id}/bet")
async def manual_bet(opportunity_id: str, db: AsyncSession = Depends(get_db)):
    """Manually execute a bet for a given opportunity."""
    opp_record = await db.get(Opportunity, opportunity_id)
    if not opp_record:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if opp_record.status != "pending":
        raise HTTPException(status_code=400, detail=f"Opportunity status is '{opp_record.status}', not pending")

    # Rebuild opp dict for executor
    from services.polymarket import get_active_markets
    markets = await get_active_markets(limit=100)
    market = next((m for m in markets if m["id"] == opp_record.market_id), None)

    if not market:
        raise HTTPException(status_code=404, detail="Market no longer active")

    opp_dict = {
        "market_id": opp_record.market_id,
        "question": opp_record.market_question,
        "outcome": opp_record.outcome,
        "current_price": opp_record.current_price,
        "kelly_bet_usdc": opp_record.kelly_bet_usdc,
        "yes_token_id": market.get("yes_token_id"),
        "no_token_id": market.get("no_token_id"),
    }

    result = await execute_bet(opportunity_id, opp_dict)
    return result


def _serialize(o: Opportunity) -> dict:
    return {
        "id": o.id,
        "market_id": o.market_id,
        "question": o.market_question,
        "outcome": o.outcome,
        "current_price": o.current_price,
        "claude_probability": o.claude_probability,
        "gemini_probability": o.gemini_probability,
        "consensus_probability": o.consensus_probability,
        "edge": o.edge,
        "kelly_bet_usdc": o.kelly_bet_usdc,
        "claude_reasoning": o.claude_reasoning,
        "gemini_reasoning": o.gemini_reasoning,
        "confidence": o.confidence,
        "status": o.status,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "expires_at": o.expires_at.isoformat() if o.expires_at else None,
    }
