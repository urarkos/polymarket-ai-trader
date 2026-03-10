from config import settings


def kelly_bet(
    probability: float,
    market_price: float,
    bankroll: float,
    fraction: float = None,
    max_bet: float = None,
) -> dict:
    """
    Calculate optimal bet size using fractional Kelly criterion.

    Args:
        probability: Estimated true probability of YES (0-1)
        market_price: Current market price for YES (0-1)
        bankroll: Total bankroll in USDC
        fraction: Kelly fraction (default from config)
        max_bet: Max bet cap in USDC (default from config)

    Returns:
        dict with bet_usdc, edge, kelly_full, kelly_fraction
    """
    if fraction is None:
        fraction = settings.kelly_fraction
    if max_bet is None:
        max_bet = settings.max_bet_usdc

    # Edge = estimated prob - market price
    edge = probability - market_price

    if edge <= 0:
        return {
            "bet_usdc": 0,
            "edge": edge,
            "kelly_full": 0,
            "kelly_fraction_pct": fraction,
            "reasoning": "No positive edge",
        }

    # Odds: if you bet $1 at price p, you win $(1/p - 1) on top of your $1
    # b = (1 - market_price) / market_price  (decimal odds - 1)
    b = (1 - market_price) / market_price
    p = probability
    q = 1 - probability

    # Kelly formula: f* = (b*p - q) / b
    kelly_full = (b * p - q) / b
    kelly_fractional = kelly_full * fraction

    # Raw bet amount
    raw_bet = bankroll * kelly_fractional

    # Cap at max_bet
    bet_usdc = min(raw_bet, max_bet)
    bet_usdc = max(0, round(bet_usdc, 2))

    return {
        "bet_usdc": bet_usdc,
        "edge": round(edge, 4),
        "kelly_full": round(kelly_full, 4),
        "kelly_fraction_pct": fraction,
        "b_odds": round(b, 4),
        "reasoning": (
            f"Edge: {edge:.1%} | Full Kelly: {kelly_full:.1%} | "
            f"Fractional ({fraction:.0%}): {kelly_fractional:.1%} of bankroll | "
            f"Raw: ${raw_bet:.2f} → Capped: ${bet_usdc:.2f}"
        ),
    }


def confidence_multiplier(confidence: str) -> float:
    """Reduce bet size based on AI confidence level."""
    return {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}.get(confidence, 0.5)


def calculate_consensus(claude_result: dict, gemini_result: dict) -> dict:
    """
    Combine Claude and Gemini probability estimates.
    Weight by confidence: HIGH=3, MEDIUM=2, LOW=1
    """
    weight_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

    claude_prob = claude_result.get("probability_yes")
    gemini_prob = gemini_result.get("probability_yes")
    claude_conf = claude_result.get("confidence", "LOW")
    gemini_conf = gemini_result.get("confidence", "LOW")

    if claude_prob is None and gemini_prob is None:
        return {"success": False}

    if claude_prob is None:
        return {"success": True, "probability": gemini_prob, "confidence": gemini_conf, "source": "gemini_only"}

    if gemini_prob is None:
        return {"success": True, "probability": claude_prob, "confidence": claude_conf, "source": "claude_only"}

    w_claude = weight_map.get(claude_conf, 1)
    w_gemini = weight_map.get(gemini_conf, 1)
    total_weight = w_claude + w_gemini

    consensus_prob = (claude_prob * w_claude + gemini_prob * w_gemini) / total_weight

    # Agreement check
    diff = abs(claude_prob - gemini_prob)
    if diff < 0.05:
        agreement = "STRONG"
        consensus_conf = "HIGH" if claude_conf == "HIGH" or gemini_conf == "HIGH" else "MEDIUM"
    elif diff < 0.15:
        agreement = "MODERATE"
        consensus_conf = "MEDIUM"
    else:
        agreement = "WEAK"
        consensus_conf = "LOW"

    return {
        "probability": round(consensus_prob, 4),
        "confidence": consensus_conf,
        "agreement": agreement,
        "claude_probability": claude_prob,
        "gemini_probability": gemini_prob,
        "difference": round(diff, 4),
        "source": "consensus",
        "success": True,
    }
