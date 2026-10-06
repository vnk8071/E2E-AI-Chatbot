#!/usr/bin/env bash
# One-time resource creation. Copy the printed D1/KV ids into wrangler.jsonc.
set -euo pipefail
npx wrangler vectorize create company-brain --dimensions 768 --metric cosine
npx wrangler r2 bucket create company-brain-docs
npx wrangler d1 create company-brain
npx wrangler kv namespace create CACHE
echo "Now paste the D1 database_id and KV id into wrangler.jsonc, then run:"
echo "  npx wrangler d1 execute company-brain --remote --file=schema.sql"
echo "  npx wrangler secret put ADMIN_TOKEN"
echo "  npx wrangler deploy && bash scripts/ingest.sh <worker-url> <admin-token>"
echo "AI Gateway: create a gateway named 'company-brain' in the dashboard (AI > AI Gateway)."
