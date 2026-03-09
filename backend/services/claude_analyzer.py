import anthropic
import json
import logging
from config import get_secret

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert prediction market analyst with deep knowledge of:
- Political science, economics, geopolitics
- Statistics and probability theory
- Current world events (up to your knowledge cutoff)
- Market psychology and crowd behavior

Your task: analyze prediction market questions and estimate the TRUE probability of the YES outcome.
Be calibrated — if you're uncertain, reflect that in your probability estimate.
Consider base rates, recent trends, and any relevant context.

ALWAYS respond with valid JSON only."""

ANALYSIS_PROMPT = """Analyze this prediction market:

Question: {question}
Description: {description}
Category: {category}
Current market price (YES): {yes_price:.1%}
Current market price (NO): {no_price:.1%}
Market ends: {end_date}

Provide:
1. Your estimated probability for YES outcome (0.0 to 1.0)
2. Key factors supporting YES
3. Key factors supporting NO
4. Your confidence level (HIGH/MEDIUM/LOW)
5. Brief reasoning summary

Respond ONLY with this JSON:
{{
  "probability_yes": 0.XX,
  "confidence": "HIGH|MEDIUM|LOW",
  "factors_yes": ["factor1", "factor2"],
  "factors_no": ["factor1", "factor2"],
  "reasoning": "concise 2-3 sentence analysis",
  "data_quality": "note if information is limited or outdated"
}}"""


async def analyze_market(market: dict) -> dict:
    """Analyze a market using Claude and return probability estimate."""
    api_key = get_secret("anthropic_api_key")
    if not api_key:
        return {"success": False, "error": "Anthropic API key not configured"}

    client = anthropic.Anthropic(api_key=api_key)

    prompt = ANALYSIS_PROMPT.format(
        question=market["question"],
        description=market.get("description", "No description provided"),
        category=market.get("category", "General"),
        yes_price=market["yes_price"],
        no_price=market["no_price"],
        end_date=market.get("end_date", "Unknown"),
    )

    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()

        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw)
        result["model"] = "claude-opus-4-6"
        result["success"] = True
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Claude returned invalid JSON: {e}")
        return {"success": False, "error": f"JSON parse error: {e}"}
    except Exception as e:
        logger.error(f"Claude analysis failed: {e}")
        return {"success": False, "error": str(e)}
