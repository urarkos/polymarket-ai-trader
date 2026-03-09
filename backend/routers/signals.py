from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db
from models import Signal, ScanRun

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("")
async def list_signals(
    profitable_only: bool = False,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    q = select(Signal).order_by(desc(Signal.created_at)).limit(limit)
    if profitable_only:
        q = q.where(Signal.is_profitable == True)  # noqa
    result = await db.execute(q)
    items = result.scalars().all()
    return {"signals": [_s(s) for s in items]}


@router.get("/scans")
async def list_scan_runs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    q = select(ScanRun).order_by(desc(ScanRun.started_at)).limit(limit)
    result = await db.execute(q)
    items = result.scalars().all()
    return {"scans": [_r(r) for r in items]}


def _s(s: Signal) -> dict:
    return {
        "id": s.id,
        "scan_id": s.scan_id,
        "market_id": s.market_id,
        "question": s.market_question,
        "outcome": s.outcome,
        "yes_price": s.yes_price,
        "no_price": s.no_price,
        "market_price": s.market_price,
        "claude_probability": s.claude_probability,
        "gemini_probability": s.gemini_probability,
        "consensus_probability": s.consensus_probability,
        "claude_confidence": s.claude_confidence,
        "gemini_confidence": s.gemini_confidence,
        "consensus_confidence": s.consensus_confidence,
        "ai_agreement": s.ai_agreement,
        "edge": s.edge,
        "kelly_full": s.kelly_full,
        "kelly_bet_usdc": s.kelly_bet_usdc,
        "is_profitable": s.is_profitable,
        "action_taken": s.action_taken,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _r(r: ScanRun) -> dict:
    return {
        "id": r.id,
        "markets_fetched": r.markets_fetched,
        "markets_analyzed": r.markets_analyzed,
        "signals_generated": r.signals_generated,
        "opportunities_found": r.opportunities_found,
        "bets_placed": r.bets_placed,
        "errors": r.errors,
        "duration_seconds": r.duration_seconds,
        "status": r.status,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
    }
