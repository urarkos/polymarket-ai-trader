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
    scan_markets_limit: int | None = None


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
        "scan_markets_limit": settings.scan_markets_limit,
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
    if data.scan_markets_limit is not None:
        settings.scan_markets_limit = data.scan_markets_limit
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
        # Normalize Polymarket key: ensure 0x prefix
        if k == "polymarket_private_key" and not value.startswith("0x"):
            value = "0x" + value

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
        import google.generativeai as genai
        genai.configure(api_key=value)
        models_to_try = [
            "gemini-2.5-pro-preview-05-06",
            "gemini-2.5-pro-preview-03-25",
            "gemini-2.0-pro-exp",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
        ]
        last_err = "No models available"
        for model_name in models_to_try:
            try:
                m = genai.GenerativeModel(model_name)
                m.generate_content("hi", generation_config=genai.types.GenerationConfig(max_output_tokens=5))
                return {"ok": True, "detail": f"Gemini API — OK (model: {model_name})"}
            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower() or "resource_exhausted" in err.lower():
                    return {"ok": True, "detail": f"Key valid ✓ — free tier quota exceeded ({model_name}). Add billing at aistudio.google.com to unlock."}
                if "not found" in err.lower() or "404" in err:
                    last_err = err
                    continue
                return {"ok": False, "error": err[:120]}
        return {"ok": False, "error": last_err[:120]}

    if key_name == "polymarket_private_key":
        try:
            from eth_account import Account
            key = value.strip()
            if not key.startswith("0x"):
                key = "0x" + key
            hex_part = key[2:]
            # Pad to 64 chars if leading zeros were stripped (some exporters do this)
            if len(hex_part) < 64:
                hex_part = hex_part.zfill(64)
                key = "0x" + hex_part
            if len(hex_part) == 40:
                return {"ok": False, "error": "This looks like a wallet address (20 bytes), not a private key (32 bytes). Export the private key from your wallet app."}
            if len(hex_part) != 64:
                return {"ok": False, "error": f"Expected 64 hex chars (32 bytes), got {len(hex_part)}. Export the private key from your wallet — not the address."}
            acct = Account.from_key(key)
            return {"ok": True, "detail": f"Wallet: {acct.address[:10]}...{acct.address[-4:]}"}
        except ValueError:
            return {"ok": False, "error": "Invalid private key — must be 64 hexadecimal characters (0-9, a-f). Not a seed phrase or address."}
        except Exception as e:
            return {"ok": False, "error": str(e)[:120]}
