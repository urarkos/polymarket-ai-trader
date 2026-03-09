import httpx
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"


async def get_active_markets(limit: int = 50, offset: int = 0) -> list[dict]:
    """Fetch active markets from Polymarket Gamma API."""
    async with httpx.AsyncClient(timeout=30) as client:
        params = {
            "active": "true",
            "closed": "false",
            "limit": limit,
            "offset": offset,
            "order": "volume24hr",
            "ascending": "false",
        }
        resp = await client.get(f"{GAMMA_API}/markets", params=params)
        resp.raise_for_status()
        markets = resp.json()

    result = []
    for m in markets:
        try:
            tokens = m.get("tokens", [])
            if len(tokens) < 2:
                continue

            # Find YES token price
            yes_token = next((t for t in tokens if t.get("outcome", "").upper() == "YES"), None)
            no_token = next((t for t in tokens if t.get("outcome", "").upper() == "NO"), None)

            if not yes_token or not no_token:
                continue

            yes_price = float(yes_token.get("price", 0))
            no_price = float(no_token.get("price", 0))

            if yes_price <= 0 or yes_price >= 1:
                continue

            result.append({
                "id": m.get("conditionId") or m.get("id"),
                "question": m.get("question", ""),
                "description": m.get("description", ""),
                "category": m.get("groupItemTitle") or m.get("category", ""),
                "yes_price": yes_price,
                "no_price": no_price,
                "volume_24h": float(m.get("volume24hr", 0)),
                "liquidity": float(m.get("liquidity", 0)),
                "end_date": m.get("endDate"),
                "yes_token_id": yes_token.get("token_id"),
                "no_token_id": no_token.get("token_id"),
                "clob_token_ids": m.get("clobTokenIds", []),
            })
        except Exception as e:
            logger.warning(f"Failed to parse market: {e}")
            continue

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
