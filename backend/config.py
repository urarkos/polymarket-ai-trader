from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # AI APIs
    anthropic_api_key: str
    gemini_api_key: str

    # Polymarket
    polymarket_private_key: str  # Wallet private key for trading
    polymarket_api_key: Optional[str] = None
    polymarket_api_secret: Optional[str] = None
    polymarket_api_passphrase: Optional[str] = None

    # Trading settings
    max_bet_usdc: float = 100.0        # Max per bet in USDC
    min_edge: float = 0.05             # Min edge (5%) to consider a bet
    kelly_fraction: float = 0.25       # Fractional Kelly (25% of full Kelly)
    bankroll_usdc: float = 1000.0      # Total bankroll for Kelly calculation
    auto_bet_enabled: bool = False     # Safety: disabled by default
    scan_interval_minutes: int = 15    # How often to scan markets

    # DB
    database_url: str = "sqlite+aiosqlite:///./polymarket.db"

    class Config:
        env_file = ".env"


settings = Settings()
