from fastapi import APIRouter
from services.polymarket import get_active_markets

router = APIRouter(prefix="/api/markets", tags=["markets"])


@router.get("")
async def list_markets(limit: int = 30, offset: int = 0):
    markets = await get_active_markets(limit=limit, offset=offset)
    return {"markets": markets, "count": len(markets)}
