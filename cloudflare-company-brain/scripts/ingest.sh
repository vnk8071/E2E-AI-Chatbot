#!/usr/bin/env bash
# Usage: bash scripts/ingest.sh <worker-url> <admin-token>
# Uploads knowledge/*.md to R2, then asks the Worker to chunk, embed and index them.
set -euo pipefail
URL="${1:?worker url}"; TOKEN="${2:?admin token}"
for f in knowledge/*.md; do
  npx wrangler r2 object put "company-brain-docs/$(basename "$f")" --file "$f" --content-type text/markdown --remote
done
curl -fsS -X POST "$URL/api/ingest" -H "Authorization: Bearer $TOKEN"
echo
