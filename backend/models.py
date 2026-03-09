from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, Integer, JSON
from sqlalchemy.sql import func
from database import Base


class MarketSnapshot(Base):
    """Raw market data saved on every scan."""
    __tablename__ = "market_snapshots"

    id = Column(String, primary_key=True)
    scan_id = Column(String, index=True)
    market_id = Column(String, nullable=False, index=True)
    question = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(String)
    yes_price = Column(Float)
    no_price = Column(Float)
    volume_24h = Column(Float)
    liquidity = Column(Float)
    end_date = Column(String)
    yes_token_id = Column(String)
    no_token_id = Column(String)
    raw_data = Column(JSON)                     # Full raw response from Polymarket API
    scanned_at = Column(DateTime, server_default=func.now(), index=True)


class AIAnalysis(Base):
    """Every AI model response, stored in full."""
    __tablename__ = "ai_analyses"

    id = Column(String, primary_key=True)
    market_id = Column(String, nullable=False, index=True)
    snapshot_id = Column(String, index=True)
    scan_id = Column(String, index=True)
    model = Column(String, nullable=False)      # "claude-opus-4-6" / "gemini-1.5-pro"
    probability_yes = Column(Float)
    confidence = Column(String)
    factors_yes = Column(JSON)
    factors_no = Column(JSON)
    reasoning = Column(Text)
    market_insight = Column(Text)
    raw_response = Column(Text)                 # Raw JSON string returned by the model
    success = Column(Boolean, default=True)
    error = Column(Text)
    latency_ms = Column(Integer)
    created_at = Column(DateTime, server_default=func.now(), index=True)


class Signal(Base):
    """
    Every trading signal generated (profitable or not).
    Superset of Opportunity — keeps full history including rejected ones.
    """
    __tablename__ = "signals"

    id = Column(String, primary_key=True)
    scan_id = Column(String, index=True)
    snapshot_id = Column(String, index=True)
    market_id = Column(String, nullable=False, index=True)
    market_question = Column(Text, nullable=False)
    outcome = Column(String, nullable=False)          # YES / NO

    yes_price = Column(Float)
    no_price = Column(Float)
    market_price = Column(Float)                      # Price for the recommended outcome

    claude_probability = Column(Float)
    gemini_probability = Column(Float)
    consensus_probability = Column(Float)
    claude_confidence = Column(String)
    gemini_confidence = Column(String)
    consensus_confidence = Column(String)
    ai_agreement = Column(String)                     # STRONG / MODERATE / WEAK

    edge = Column(Float)
    kelly_full = Column(Float)
    kelly_bet_usdc = Column(Float)

    is_profitable = Column(Boolean)                   # edge >= min_edge
    action_taken = Column(String, default="none")     # none / manual_bet / auto_bet / skipped
    created_at = Column(DateTime, server_default=func.now(), index=True)


class Opportunity(Base):
    """Profitable signals surfaced in the UI."""
    __tablename__ = "opportunities"

    id = Column(String, primary_key=True)
    signal_id = Column(String, index=True)
    market_id = Column(String, nullable=False, index=True)
    market_question = Column(Text, nullable=False)
    outcome = Column(String, nullable=False)
    current_price = Column(Float, nullable=False)
    claude_probability = Column(Float)
    gemini_probability = Column(Float)
    consensus_probability = Column(Float)
    edge = Column(Float)
    kelly_bet_usdc = Column(Float)
    claude_reasoning = Column(Text)
    gemini_reasoning = Column(Text)
    confidence = Column(String)
    status = Column(String, default="pending")   # pending / executed / skipped / expired / failed
    created_at = Column(DateTime, server_default=func.now(), index=True)
    expires_at = Column(DateTime)


class Bet(Base):
    """Executed bets placed on Polymarket."""
    __tablename__ = "bets"

    id = Column(String, primary_key=True)
    opportunity_id = Column(String, index=True)
    signal_id = Column(String, index=True)
    market_id = Column(String, nullable=False, index=True)
    market_question = Column(Text, nullable=False)
    outcome = Column(String, nullable=False)
    amount_usdc = Column(Float, nullable=False)
    price_at_bet = Column(Float, nullable=False)
    tx_hash = Column(String)
    order_id = Column(String)
    status = Column(String, default="placed")    # placed / won / lost / cancelled / failed
    pnl_usdc = Column(Float)
    placed_at = Column(DateTime, server_default=func.now(), index=True)
    resolved_at = Column(DateTime)


class AppSecret(Base):
    """API keys and secrets stored in DB (overrides env vars)."""
    __tablename__ = "app_secrets"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ScanRun(Base):
    """Log of every scan execution."""
    __tablename__ = "scan_runs"

    id = Column(String, primary_key=True)
    markets_fetched = Column(Integer, default=0)
    markets_analyzed = Column(Integer, default=0)
    signals_generated = Column(Integer, default=0)
    opportunities_found = Column(Integer, default=0)
    bets_placed = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    duration_seconds = Column(Float)
    status = Column(String, default="running")   # running / completed / failed
    started_at = Column(DateTime, server_default=func.now(), index=True)
    finished_at = Column(DateTime)
