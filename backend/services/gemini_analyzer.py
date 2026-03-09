import google.generativeai as genai
import json
import logging
from config import get_secret

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert prediction market analyst with deep knowledge of:
- Political science, economics, geopolitics
- Statistics and probability theory
- Current world events
- Market psychology and crowd behavior

Your task: analyze prediction market questions and estimate the TRUE probability of the YES outcome.
Be calibrated — reflect uncertainty in your probability estimate.
Consider base rates, recent trends, and context from your latest training data.

ALWAYS respond with valid JSON only."""

ANALYSIS_PROMPT = """Analyze this prediction market:

Question: {question}
Description: {description}
Category: {category}
Current market price (YES): {yes_price:.1%}
Current market price (NO): {no_price:.1%}
Market ends: {end_date}

Provide an independent probability estimate. Do NOT simply echo the market price.
Consider what the market might be missing or mispricing.

Respond ONLY with this JSON:
{{
  "probability_yes": 0.XX,
  "confidence": "HIGH|MEDIUM|LOW",
  "factors_yes": ["factor1", "factor2"],
  "factors_no": ["factor1", "factor2"],
  "reasoning": "concise 2-3 sentence analysis",
  "market_insight": "what the market might be missing or getting right"
}}"""


async def analyze_market(market: dict) -> dict:
    """Analyze a market using Gemini and return probability estimate."""
    api_key = get_secret("gemini_api_key")
    if not api_key:
        return {"success": False, "error": "Gemini API key not configured"}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")

    prompt = SYSTEM_PROMPT + "\n\n" + ANALYSIS_PROMPT.format(
        question=market["question"],
        description=market.get("description", "No description provided"),
        category=market.get("category", "General"),
        yes_price=market["yes_price"],
        no_price=market["no_price"],
        end_date=market.get("end_date", "Unknown"),
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )
        raw = response.text.strip()

        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                if part.startswith("json"):
                    raw = part[4:].strip()
                    break
                elif "{" in part:
                    raw = part.strip()
                    break

        result = json.loads(raw)
        result["model"] = "gemini-1.5-pro"
        result["success"] = True
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned invalid JSON: {e}")
        return {"success": False, "error": f"JSON parse error: {e}"}
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return {"success": False, "error": str(e)}
