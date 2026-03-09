#!/usr/bin/env bash
# Polymarket AI Trader — Railway deploy script
set -e

echo "=== Polymarket AI Trader Deploy ==="

# Check token
if [ -z "$RAILWAY_TOKEN" ]; then
  echo "ERROR: RAILWAY_TOKEN not set"
  exit 1
fi

# Init project if needed
if ! railway status 2>/dev/null | grep -q "Project"; then
  echo "Creating new Railway project..."
  railway init --name polymarket-ai-trader
fi

echo "Adding PostgreSQL..."
railway add --plugin postgresql || echo "(PostgreSQL may already exist)"

echo "Setting environment variables..."
railway variables set \
  ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
  GEMINI_API_KEY="${GEMINI_API_KEY}" \
  POLYMARKET_PRIVATE_KEY="${POLYMARKET_PRIVATE_KEY}" \
  BANKROLL_USDC="${BANKROLL_USDC:-1000}" \
  MAX_BET_USDC="${MAX_BET_USDC:-50}" \
  MIN_EDGE="${MIN_EDGE:-0.05}" \
  KELLY_FRACTION="${KELLY_FRACTION:-0.25}" \
  AUTO_BET_ENABLED="${AUTO_BET_ENABLED:-false}" \
  SCAN_INTERVAL_MINUTES="${SCAN_INTERVAL_MINUTES:-15}"

echo "Deploying..."
railway up --detach

echo ""
echo "=== Deploy started! ==="
echo "Check status: railway status"
echo "View logs:    railway logs"
echo "Open app:     railway open"
