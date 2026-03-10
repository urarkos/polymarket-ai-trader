import anthropic
import json
import logging
from config import get_secret

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a world-class prediction market analyst and probabilistic forecaster.
Your analysis must be rigorous, calibrated, and actionable.

Core principles:
- NEVER anchor to the current market price — form your own independent probability estimate first
- Apply proper base rates before updating on specific evidence
- Consider what sophisticated market participants might be missing or mispricing
- Be explicit about your uncertainty and the key cruxes of the question
- Think carefully about resolution criteria and edge cases

You have deep expertise in:
- Political science, electoral systems, and geopolitics
- Economics, monetary policy, and market dynamics
- Statistics, Bayesian reasoning, and forecasting methodology
- Current world events and historical base rates
- Crowd psychology and prediction market microstructure

ALWAYS respond with valid JSON only. No markdown, no explanations outside the JSON."""

ANALYSIS_PROMPT = """Analyze this prediction market with deep rigor:

═══ MARKET DATA ═══
Question: {question}
Description: {description}
Category: {category}
Current market price YES: {yes_price:.1%}
Current market price NO:  {no_price:.1%}
Market resolves: {end_date}
24h Volume: {volume_24h}
Liquidity: {liquidity}

═══ YOUR TASK ═══
Step 1 — BASE RATE: What is the historical base rate for this type of question IGNORING the specific context?
Step 2 — SPECIFIC EVIDENCE: What specific factors update you away from the base rate?
Step 3 — MARKET EFFICIENCY CHECK: Why might the market be mispriced at {yes_price:.1%}? What might sophisticated traders be missing?
Step 4 — RESOLUTION RISK: Are there ambiguity or edge cases in how this resolves?
Step 5 — FINAL ESTIMATE: What is your calibrated probability?

Respond ONLY with this JSON structure:
{{
  "probability_yes": <float 0.0-1.0>,
  "confidence": "<HIGH|MEDIUM|LOW>",
  "base_rate": <float 0.0-1.0>,
  "base_rate_rationale": "<brief explanation of the reference class>",
  "factors_yes": ["<specific factor>", "<specific factor>", "<specific factor>"],
  "factors_no": ["<specific factor>", "<specific factor>", "<specific factor>"],
  "key_uncertainty": "<the single most important unknown that could swing this>",
  "market_mispricing_hypothesis": "<why might the crowd be wrong at {yes_price:.1%}?>",
  "resolution_risks": "<any ambiguity in resolution criteria>",
  "reasoning": "<3-5 sentence synthesis of your full analysis>",
  "confidence_interval_low": <float — pessimistic scenario probability>,
  "confidence_interval_high": <float — optimistic scenario probability>
}}"""


async def analyze_market(market: dict) -> dict:
    """Analyze a market using Claude Opus with extended thinking."""
    api_key = get_secret("anthropic_api_key")
    if not api_key:
        return {"success": False, "error": "Anthropic API key not configured"}

    client = anthropic.AsyncAnthropic(api_key=api_key)

    prompt = ANALYSIS_PROMPT.format(
        question=market["question"],
        description=market.get("description", "No additional description provided."),
        category=market.get("category", "General"),
        yes_price=market["yes_price"],
        no_price=market["no_price"],
        end_date=market.get("end_date", "Unknown"),
        volume_24h=f"${market.get('volume_24h', 0):,.0f}" if market.get("volume_24h") else "N/A",
        liquidity=f"${market.get('liquidity', 0):,.0f}" if market.get("liquidity") else "N/A",
    )

    try:
        message = await client.messages.create(
            model="claude-opus-4-6",
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip() if message.content else ""

        # Strip markdown fences if present
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        result = json.loads(raw)
        result["model"] = "claude-opus-4-6"
        result["success"] = True
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Claude returned invalid JSON: {e}\nRaw: {raw[:200]}")
        return {"success": False, "error": f"JSON parse error: {e}"}
    except Exception as e:
        logger.error(f"Claude analysis failed: {e}")
        return {"success": False, "error": str(e)}
