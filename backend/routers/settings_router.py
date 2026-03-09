from fastapi import APIRouter
from pydantic import BaseModel
from config import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    max_bet_usdc: float | None = None
    min_edge: float | None = None
    kelly_fraction: float | None = None
    bankroll_usdc: float | None = None
    auto_bet_enabled: bool | None = None
    scan_interval_minutes: int | None = None


@router.get("")
async def get_settings():
    return {
        "max_bet_usdc": settings.max_bet_usdc,
        "min_edge": settings.min_edge,
        "kelly_fraction": settings.kelly_fraction,
        "bankroll_usdc": settings.bankroll_usdc,
        "auto_bet_enabled": settings.auto_bet_enabled,
        "scan_interval_minutes": settings.scan_interval_minutes,
    }


@router.patch("")
async def update_settings(data: SettingsUpdate):
    """Update runtime settings (persists until restart)."""
    if data.max_bet_usdc is not None:
        settings.max_bet_usdc = data.max_bet_usdc
    if data.min_edge is not None:
        settings.min_edge = data.min_edge
    if data.kelly_fraction is not None:
        settings.kelly_fraction = data.kelly_fraction
    if data.bankroll_usdc is not None:
        settings.bankroll_usdc = data.bankroll_usdc
    if data.auto_bet_enabled is not None:
        settings.auto_bet_enabled = data.auto_bet_enabled
    if data.scan_interval_minutes is not None:
        settings.scan_interval_minutes = data.scan_interval_minutes
    return {"updated": True, **data.model_dump(exclude_none=True)}
