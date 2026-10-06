#!/usr/bin/env bash
# Creates (or updates) the AI Gateway with caching, rate limiting, logging and Guardrails.
# Usage: CLOUDFLARE_ACCOUNT_ID=... CLOUDFLARE_API_TOKEN=... bash scripts/configure-gateway.sh [gateway-id]
set -euo pipefail

ID="${1:-company-brain}"
: "${CLOUDFLARE_ACCOUNT_ID:?export CLOUDFLARE_ACCOUNT_ID}"
: "${CLOUDFLARE_API_TOKEN:?export CLOUDFLARE_API_TOKEN (AI Gateway: Edit)}"
API="https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/ai-gateway/gateways"

# Guardrails run Llama Guard 3 on prompts and responses (~500ms each).
# P1 = prompt injection; S1..S11 = Llama Guard hazard categories (violence, crime, hate, self-harm...).
# Prompt blocks surface in the Worker as error 2016, response blocks as 2017.
read -r -d '' BODY <<JSON || true
{
  "id": "$ID",
  "collect_logs": true,
  "cache_ttl": 3600,
  "cache_invalidate_on_update": true,
  "rate_limiting_interval": 60,
  "rate_limiting_limit": 60,
  "rate_limiting_technique": "sliding",
  "guardrails": {
    "prompt":   { "P1": "BLOCK", "S1": "BLOCK", "S2": "BLOCK", "S3": "BLOCK", "S4": "BLOCK", "S9": "BLOCK", "S10": "BLOCK", "S11": "BLOCK" },
    "response": { "S1": "BLOCK", "S2": "BLOCK", "S3": "BLOCK", "S4": "BLOCK", "S9": "BLOCK", "S10": "BLOCK", "S11": "BLOCK" }
  }
}
JSON

auth=(-H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H "Content-Type: application/json")

# Try create; if it already exists, update in place.
if ! curl -fsS "${auth[@]}" -X POST "$API" -d "$BODY" >/dev/null 2>&1; then
  curl -fsS "${auth[@]}" -X PUT "$API/$ID" -d "$BODY" >/dev/null
  echo "Updated gateway '$ID'."
else
  echo "Created gateway '$ID'."
fi
echo "Set GATEWAY_ID=$ID in .env (local) or wrangler.jsonc vars (deployed)."
