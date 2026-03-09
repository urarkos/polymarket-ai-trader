from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings, _secrets
import config

from database import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Names of secrets manageable via UI
SECRET_KEYS = ["anthropic_api_key", "gemini_api_key", "polymarket_private_key"]


def _mask(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 12:
        return "***"
    return value[:8] + "..." + value[-4:]


class SettingsUpdate(BaseModel):
    max_bet_usdc: float | None = None
    min_edge: float | None = None
    kelly_fraction: float | None = None
    bankroll_usdc: float | None = None
    auto_bet_enabled: bool | None = None
    scan_interval_minutes: int | None = None


class KeysUpdate(BaseModel):
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    polymarket_private_key: str | None = None


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


@router.get("/keys")
async def get_keys():
    """Return masked versions of stored API keys."""
    result = {}
    for k in SECRET_KEYS:
        value = config.get_secret(k)
        result[k] = _mask(value)
    return result


@router.patch("/keys")
async def update_keys(data: KeysUpdate, db: AsyncSession = Depends(get_db)):
    """Save API keys to DB and update runtime store."""
    from models import AppSecret
    from sqlalchemy import select

    updated = []
    for k in SECRET_KEYS:
        value = getattr(data, k)
        if value is None or value.strip() == "":
            continue
        value = value.strip()

        # Upsert into DB
        existing = await db.get(AppSecret, k)
        if existing:
            existing.value = value
        else:
            db.add(AppSecret(key=k, value=value))

        # Update runtime store immediately
        config._secrets[k] = value
        updated.append(k)

    await db.commit()
    return {"updated": updated}


@router.post("/keys/test/{key_name}")
async def test_key(key_name: str):
    """Test that a stored API key is valid by making a minimal real call."""
    from config import get_secret

    if key_name not in SECRET_KEYS:
        return {"ok": False, "error": "Unknown key"}

    value = get_secret(key_name)
    if not value:
        return {"ok": False, "error": "Key not set"}

    if key_name == "anthropic_api_key":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=value)
            client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                messages=[{"role": "user", "content": "hi"}],
            )
            return {"ok": True, "detail": "Anthropic API — OK"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:120]}

    if key_name == "gemini_api_key":
        try:
            import google.generativeai as genai
            genai.configure(api_key=value)
            m = genai.GenerativeModel("gemini-1.5-flash")
            m.generate_content("hi", generation_config=genai.types.GenerationConfig(max_output_tokens=5))
            return {"ok": True, "detail": "Gemini API — OK"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:120]}

    if key_name == "polymarket_private_key":
        try:
            from eth_account import Account
            acct = Account.from_key(value)
            return {"ok": True, "detail": f"Wallet: {acct.address[:10]}..."}
        except Exception as e:
            return {"ok": False, "error": f"Invalid private key: {str(e)[:80]}"}
