import json
import logging
from config import get_secret

logger = logging.getLogger(__name__)

# Model priority list — try best available, fall back gracefully
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

ANALYSIS_PROMPT = """You are a world-class prediction market analyst and probabilistic forecaster.

Your analysis must be independent and rigorous. You are NOT an assistant — you are a calibrated forecaster whose job is to beat the crowd.

═══ MARKET DATA ═══
Question: {question}
Description: {description}
Category: {category}
Current market price YES: {yes_price:.1%}
Current market price NO:  {no_price:.1%}
Market resolves: {end_date}
24h Volume: {volume_24h}
Liquidity: {liquidity}

═══ ANALYSIS FRAMEWORK ═══
Apply this structured thinking:

1. REFERENCE CLASS: What is the base rate for this type of event, ignoring this specific case?
2. SPECIFIC EVIDENCE: What unique factors adjust you from the base rate?
3. MARKET CRITIQUE: The market says {yes_price:.1%}. What information asymmetry might explain a mispricing?
4. SCENARIO ANALYSIS: Walk through the most likely YES scenario and most likely NO scenario.
5. CALIBRATION CHECK: Are you being appropriately uncertain? Avoid overconfidence.

═══ CRITICAL RULES ═══
- Do NOT simply echo {yes_price:.1%} as your answer — form an independent view
- Provide at least 3 concrete factors for each side
- Your probability MUST be between 0.05 and 0.95 unless the evidence is overwhelming
- Be specific, not vague

Respond ONLY with valid JSON (no markdown):
{{
  "probability_yes": <float 0.0-1.0>,
  "confidence": "<HIGH|MEDIUM|LOW>",
  "base_rate": <float 0.0-1.0>,
  "base_rate_rationale": "<reference class and historical frequency>",
  "factors_yes": ["<specific factor>", "<specific factor>", "<specific factor>"],
  "factors_no": ["<specific factor>", "<specific factor>", "<specific factor>"],
  "key_uncertainty": "<the single most important unknown>",
  "market_insight": "<specific hypothesis about why market may be mispriced>",
  "scenario_yes": "<brief most likely path to YES resolution>",
  "scenario_no": "<brief most likely path to NO resolution>",
  "reasoning": "<3-5 sentence synthesis>",
  "confidence_interval_low": <float>,
  "confidence_interval_high": <float>
}}"""


async def analyze_market(market: dict) -> dict:
    """Analyze a market using the best available Gemini model."""
    api_key = get_secret("gemini_api_key")
    if not api_key:
        return {"success": False, "error": "Gemini API key not configured"}

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
    except ImportError:
        return {"success": False, "error": "google-generativeai package not installed"}

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

    last_error = "No models available"
    for model_name in GEMINI_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=8192,
                ),
            )
            raw = response.text.strip()

            # Strip markdown fences
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
            result["model"] = model_name
            result["success"] = True
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Gemini ({model_name}) returned invalid JSON: {e}")
            last_error = f"JSON parse error: {e}"
            break  # Don't retry other models for parse errors
        except Exception as e:
            err = str(e)
            if "not found" in err.lower() or "404" in err:
                logger.info(f"Gemini model {model_name} not available, trying next")
                last_error = err
                continue
            if "429" in err or "quota" in err.lower() or "resource_exhausted" in err.lower():
                logger.warning(f"Gemini ({model_name}) rate limited, trying next model")
                last_error = err
                continue
            logger.error(f"Gemini ({model_name}) failed: {e}")
            last_error = err
            break

    return {"success": False, "error": last_error[:200]}
