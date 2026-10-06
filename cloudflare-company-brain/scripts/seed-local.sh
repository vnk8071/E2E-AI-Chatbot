#!/usr/bin/env bash
# Prepares LOCAL state for `wrangler dev`: D1 schema + knowledge docs in local R2.
# (Vectorize and Workers AI are always remote; create the index once with `npx wrangler vectorize create`.)
set -euo pipefail
npx wrangler d1 execute company-brain --local --file=schema.sql
for f in knowledge/*.md; do
  npx wrangler r2 object put "company-brain-docs/$(basename "$f")" --file "$f" --content-type text/markdown --local
done
echo "Local D1 and R2 are seeded. Next: npx wrangler dev, then POST /api/ingest (see README step 7)."
