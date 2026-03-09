from pydantic_settings import BaseSettings
from typing import Optional

# Runtime secret store — loaded from DB on startup, updated via /api/keys
_secrets: dict[str, str] = {}


def get_secret(name: str) -> str | None:
    """Return secret from DB-loaded store, falling back to env/settings."""
    if name in _secrets:
        return _secrets[name]
    raw = getattr(settings, name, None)
    # Ignore placeholder values set by deploy scripts
    if raw and raw != "REPLACE_ME":
        return raw
    return None


class Settings(BaseSettings):
    # AI APIs — optional at startup; can be set via UI
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # Polymarket
    polymarket_private_key: Optional[str] = None
    polymarket_api_key: Optional[str] = None
    polymarket_api_secret: Optional[str] = None
    polymarket_api_passphrase: Optional[str] = None

    # Trading settings
    max_bet_usdc: float = 100.0
    min_edge: float = 0.05
    kelly_fraction: float = 0.25
    bankroll_usdc: float = 1000.0
    auto_bet_enabled: bool = False
    scan_interval_minutes: int = 15

    # DB
    database_url: str = "sqlite+aiosqlite:///./polymarket.db"

    class Config:
        env_file = ".env"


settings = Settings()
