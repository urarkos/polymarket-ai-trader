from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from database import get_db
from models import Bet

router = APIRouter(prefix="/api/bets", tags=["bets"])


@router.get("")
async def list_bets(limit: int = 100, db: AsyncSession = Depends(get_db)):
    q = select(Bet).order_by(desc(Bet.placed_at)).limit(limit)
    result = await db.execute(q)
    bets = result.scalars().all()
    return {"bets": [_serialize(b) for b in bets]}


@router.get("/stats")
async def bet_stats(db: AsyncSession = Depends(get_db)):
    total_q = await db.execute(select(func.count(Bet.id)))
    total = total_q.scalar()

    won_q = await db.execute(select(func.count(Bet.id)).where(Bet.status == "won"))
    won = won_q.scalar()

    pnl_q = await db.execute(select(func.sum(Bet.pnl_usdc)).where(Bet.pnl_usdc.isnot(None)))
    total_pnl = pnl_q.scalar() or 0

    staked_q = await db.execute(select(func.sum(Bet.amount_usdc)))
    total_staked = staked_q.scalar() or 0

    return {
        "total_bets": total,
        "won": won,
        "lost": (await db.execute(select(func.count(Bet.id)).where(Bet.status == "lost"))).scalar(),
        "pending": (await db.execute(select(func.count(Bet.id)).where(Bet.status == "placed"))).scalar(),
        "total_pnl_usdc": round(total_pnl, 2),
        "total_staked_usdc": round(total_staked, 2),
        "roi_pct": round((total_pnl / total_staked * 100) if total_staked > 0 else 0, 2),
        "win_rate": round((won / total * 100) if total > 0 else 0, 2),
    }


def _serialize(b: Bet) -> dict:
    return {
        "id": b.id,
        "opportunity_id": b.opportunity_id,
        "market_id": b.market_id,
        "question": b.market_question,
        "outcome": b.outcome,
        "amount_usdc": b.amount_usdc,
        "price_at_bet": b.price_at_bet,
        "tx_hash": b.tx_hash,
        "status": b.status,
        "pnl_usdc": b.pnl_usdc,
        "placed_at": b.placed_at.isoformat() if b.placed_at else None,
        "resolved_at": b.resolved_at.isoformat() if b.resolved_at else None,
    }
