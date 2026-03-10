import httpx
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"


async def get_active_markets(limit: int = 50, offset: int = 0) -> list[dict]:
    """Fetch active markets from Polymarket Gamma API."""
    import json as _json

    # Try different sort fields — Gamma API has changed over time
    sort_attempts = [
        {"order": "volume24hr", "ascending": "false"},
        {"order": "volumeNum", "ascending": "false"},
        {},
    ]

    markets = []
    async with httpx.AsyncClient(timeout=30) as client:
        for sort_params in sort_attempts:
            params = {
                "active": "true",
                "closed": "false",
                "limit": limit,
                "offset": offset,
                **sort_params,
            }
            try:
                resp = await client.get(f"{GAMMA_API}/markets", params=params)
                resp.raise_for_status()
                data = resp.json()
                # Gamma API may return a list or {"data": [...], ...}
                if isinstance(data, list):
                    markets = data
                elif isinstance(data, dict):
                    markets = data.get("data") or data.get("markets") or []
                else:
                    markets = []

                if markets:
                    logger.info(f"Gamma API returned {len(markets)} raw markets (sort={sort_params.get('order', 'default')})")
                    break
                logger.warning(f"Gamma API returned 0 markets with sort={sort_params.get('order', 'default')}, retrying...")
            except Exception as e:
                logger.warning(f"Gamma API request failed (sort={sort_params.get('order')}): {e}")
                continue

    if not markets:
        logger.error("Gamma API returned 0 markets on all attempts")
        return []

    result = []
    skipped_no_binary = 0
    skipped_bad_price = 0
    skipped_parse_error = 0

    for m in markets:
        try:
            outcomes = m.get("outcomes", [])
            outcome_prices = m.get("outcomePrices", [])
            if isinstance(outcomes, str):
                outcomes = _json.loads(outcomes)
            if isinstance(outcome_prices, str):
                outcome_prices = _json.loads(outcome_prices)
            clob_token_ids = m.get("clobTokenIds", [])
            if isinstance(clob_token_ids, str):
                clob_token_ids = _json.loads(clob_token_ids)

            # Find YES/NO indices
            yes_idx = next((i for i, o in enumerate(outcomes) if str(o).upper() == "YES"), None)
            no_idx = next((i for i, o in enumerate(outcomes) if str(o).upper() == "NO"), None)

            if yes_idx is None or no_idx is None:
                skipped_no_binary += 1
                continue
            if len(outcome_prices) <= max(yes_idx, no_idx):
                skipped_no_binary += 1
                continue

            yes_price = float(outcome_prices[yes_idx])
            no_price = float(outcome_prices[no_idx])

            # Allow prices very close to 0 or 1 (but not exactly resolved)
            if yes_price < 0.01 or yes_price > 0.99:
                skipped_bad_price += 1
                continue

            yes_token_id = clob_token_ids[yes_idx] if len(clob_token_ids) > yes_idx else None
            no_token_id = clob_token_ids[no_idx] if len(clob_token_ids) > no_idx else None

            result.append({
                "id": m.get("conditionId") or m.get("id"),
                "question": m.get("question", ""),
                "description": m.get("description", ""),
                "category": m.get("groupItemTitle") or m.get("category", ""),
                "yes_price": yes_price,
                "no_price": no_price,
                "volume_24h": float(m.get("volume24hr") or m.get("volume_24hr") or 0),
                "liquidity": float(m.get("liquidity", 0) or 0),
                "end_date": m.get("endDate"),
                "yes_token_id": yes_token_id,
                "no_token_id": no_token_id,
                "clob_token_ids": clob_token_ids,
            })
        except Exception as e:
            logger.warning(f"Failed to parse market: {e}")
            skipped_parse_error += 1
            continue

    logger.info(
        f"Market parsing: {len(result)} valid | "
        f"skipped: {skipped_no_binary} non-binary, {skipped_bad_price} near-resolved, {skipped_parse_error} parse errors"
    )
    return result


async def get_market_orderbook(token_id: str) -> Optional[dict]:
    """Get order book for a token."""
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(f"{CLOB_API}/book", params={"token_id": token_id})
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"Failed to get orderbook for {token_id}: {e}")
            return None


async def place_market_order(token_id: str, side: str, amount_usdc: float) -> Optional[dict]:
    """
    Place a market order on Polymarket.
    Returns transaction info or None on failure.

    Requires POLYMARKET_PRIVATE_KEY to be set.
    """
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import MarketOrderArgs, OrderType
        from py_clob_client.constants import POLYGON

        client = ClobClient(
            host=CLOB_API,
            key=settings.polymarket_private_key,
            chain_id=POLYGON,
            signature_type=1,  # POLY_GNOSIS_SAFE
        )

        # Create and sign the order
        order_args = MarketOrderArgs(
            token_id=token_id,
            amount=amount_usdc,
        )
        signed_order = client.create_market_order(order_args)
        resp = client.post_order(signed_order, OrderType.FOK)

        return {
            "success": True,
            "order_id": resp.get("orderID"),
            "status": resp.get("status"),
            "tx_hash": resp.get("transactionHash"),
        }
    except Exception as e:
        logger.error(f"Failed to place order: {e}")
        return {"success": False, "error": str(e)}
