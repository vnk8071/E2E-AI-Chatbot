# Company Brain Assistant (Cloudflare, custom RAG)

An internal knowledge assistant for a fictional DTC skincare brand ("Glowkind"). It answers from a sample knowledge base, cites its sources, follows brand and compliance rules, says so when it doesn't know, and generates a creative brief.

**Contents:** [Quick start (local)](#quick-start-local) · [ADMIN_TOKEN guide](#admin_token-guide) · [Architecture](#architecture) · [Reliability design](#reliability-design) · [Tests and benchmarks](#tests-and-benchmarks) · [Deploy](#deploy) · [API](#api) · [Status](#status)

## Quick start (local)

Everything below runs from this folder (`cloudflare-company-brain/`). D1, KV, R2 and the Durable Object run locally. **Workers AI and Vectorize are always remote**, so you need a free Cloudflare account and usage may be billed (very small for this demo).

**Prerequisites:** Node 20+, a Cloudflare account, Git Bash or another bash shell (the helper scripts are bash).

1. **Install dependencies**
   ```bash
   npm install
   ```
2. **Log in to Cloudflare** (opens a browser)
   ```bash
   npx wrangler login
   ```
3. **Create your `.env`** from the template
   ```bash
   cp .env.example .env
   ```
4. **Generate an `ADMIN_TOKEN` and put it in `.env`** (details in the [guide below](#admin_token-guide))
   ```bash
   node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
   ```
   Open `.env` and set `ADMIN_TOKEN=<the value printed above>`. Leave `GATEWAY_ID=` empty for local runs.
5. **Create the Vectorize index** (once per account; 768 dims matches the embedding model)
   ```bash
   npx wrangler vectorize create company-brain --dimensions 768 --metric cosine
   ```
   When it asks to add the binding to your config, answer no: `wrangler.jsonc` already has it.
6. **Seed local D1 and R2**
   ```bash
   bash scripts/seed-local.sh
   ```
7. **Start the Worker, then ingest the knowledge base** (in a second terminal)
   ```bash
   npx wrangler dev                      # terminal 1: serves http://127.0.0.1:8787
   ```
   ```bash
   # terminal 2: use the same token as in .env
   curl -X POST http://127.0.0.1:8787/api/ingest -H "Authorization: Bearer <ADMIN_TOKEN>"
   # expected: {"docs":6,"chunks":25}
   ```
8. **Wait about a minute.** Vectorize indexes asynchronously. Check with `npx wrangler vectorize info company-brain` until `vectorCount` is 25.
9. **Open http://127.0.0.1:8787** and try:
   - "What is the price of the Starter Bundle?" (answered, cited)
   - "Can I say Dew Drop Serum cures acne?" (refused under the compliance rules)
   - "What is our TikTok ad budget?" (not enough information)
   - Use the form at the bottom to generate a creative brief.
10. **Run the tests** (see [Tests and benchmarks](#tests-and-benchmarks))
    ```bash
    npm test               # offline, no Worker needed
    npm run eval           # live eval against the running Worker
    ```

Troubleshooting:

| Symptom | Cause and fix |
| --- | --- |
| `POST /api/ingest` returns `401 unauthorized` | The token in the header doesn't match `.env`, `ADMIN_TOKEN` is empty, or you edited `.env` without restarting `wrangler dev`. |
| Everything is answered with "not enough information" right after ingest | Vectorize hasn't finished indexing. Wait and recheck `vectorCount`. |
| `Please configure AI Gateway in the Cloudflare dashboard` (error 2001) | `GATEWAY_ID` is set but that gateway doesn't exist. Empty it in `.env`, or run `scripts/configure-gateway.sh`. |
| `Cannot reach http://127.0.0.1:8787` from `npm run eval` | `wrangler dev` isn't running. |

## ADMIN_TOKEN guide

`ADMIN_TOKEN` is a shared secret (a long random string you invent) that unlocks the operator-only parts of the Worker. Without it those parts return `401`. If it is empty or unset, they are **always** locked.

**What it protects**

| Where | Why it is admin-only |
| --- | --- |
| `POST /api/ingest` | Rebuilds the whole knowledge index (cost, and it replaces D1 chunk data). |
| `POST /api/retrieve` | Debug endpoint that exposes raw retrieval scores (used by the retrieval benchmark). |
| `x-no-cache: 1` header | Lets the eval bypass the answer cache and the per-IP rate limit. Ignored without a valid token. |

Normal chat (`/api/chat`, `/api/brief`) never needs it.

**How to create one.** Any long random value works (32 bytes or more). Use one of:

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"   # any OS with Node
openssl rand -hex 32                                                       # macOS / Linux / Git Bash
```
```powershell
# Windows PowerShell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
```

**Where to put it**

| Environment | How |
| --- | --- |
| Local (`wrangler dev`) | `ADMIN_TOKEN=...` in `.env`. Restart `wrangler dev` after changing it. `.env` is git-ignored; never commit it. |
| Deployed Worker | `npx wrangler secret put ADMIN_TOKEN` (paste the value when prompted). Do not put it in `wrangler.jsonc`. Use a **different** value from local. |

**How to use it**

```bash
# ingest
curl -X POST "$URL/api/ingest" -H "Authorization: Bearer $ADMIN_TOKEN"
# or, for a deployed Worker: bash scripts/ingest.sh "$URL" "$ADMIN_TOKEN"

# retrieval debug
curl -X POST "$URL/api/retrieve" -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "content-type: application/json" -d '{"question":"price of the serum"}'
```

`npm run eval` reads `ADMIN_TOKEN` from the environment or from `.env` automatically.

**Rotating or leaking:** set a new value (`.env` locally, `wrangler secret put` when deployed) and restart or redeploy. The old value stops working immediately. The token is sent in a header, so only use it over `https://` for a deployed Worker.

## Architecture

```
Browser ──► Worker (src/index.ts)
              ├─ KV ................ per-IP rate limit + answer cache
              ├─ Durable Object .... ChatSession: last 8 turns per session
              ├─ AI Gateway ──► Workers AI (bge-base embeddings + Llama 3.3 chat)
              ├─ Vectorize ......... chunk embeddings (768 dim, cosine)
              ├─ D1 ................ chunk text/metadata + query_log (audit)
              └─ R2 ................ source markdown docs (knowledge/)
```

Ingest: `knowledge/*.md` → R2 → `POST /api/ingest` chunks by `##` section → embeds → Vectorize + D1.

Query: input guardrail → cache lookup → embed question → Vectorize top-6 → drop hits under `MIN_SCORE` → add the always-on COMPLIANCE and BRAND chunks → LLM with numbered sources → output guardrail → cache.

Prompts live in `src/prompts.ts`; their hash is reported as `promptVersion` by `GET /api/health`.

## Reliability design

| Requirement | How it is enforced |
| --- | --- |
| Citations | Prompt requires `[n]` after claims. Server parses them (including `[1, 2]`), discards invalid numbers, and returns only the sources actually cited, with excerpts. |
| Not enough info | (1) If no chunk scores above `MIN_SCORE`, the LLM is never called. (2) If the model answers without any valid citation, the answer is replaced by the "not enough information" message. Both cases are logged to D1 `query_log`. |
| Brand and compliance rules | Compliance and brand chunks are injected into every prompt regardless of retrieval score. The output guardrail enforces them after generation. |
| Input guardrail | Before any embedding, retrieval or LLM call, `checkInput` rejects empty, oversized and control-character input and common prompt-injection phrasing ("ignore previous instructions", "reveal your system prompt", "developer mode"...). Returns `blocked: "input"`. Heuristic only: it is a first filter, not a complete defence. |
| Output guardrail | After generation, the answer is blocked (`blocked: "output"`, with `violations`) if it contains a banned term used as a claim, or a number, price or percentage that is not in the sources. Briefs get one rewrite attempt with the violations fed back before being blocked. |
| AI Gateway Guardrails | `scripts/configure-gateway.sh` enables Llama Guard 3 on prompts and responses (injection plus violence, crime, hate, self-harm and similar categories). The Worker maps gateway errors 2016 (prompt) and 2017 (response) to a 422 `blocked` response. Adds about 500 ms per call and needs the gateway to exist. |
| Answer cache | Repeated questions are served from KV (`CACHE_TTL_SECONDS`, default 1 hour) without calling Vectorize or the LLM. The key is the normalised question (case, spacing and trailing punctuation ignored) plus a knowledge-base version that changes on every ingest. Only first-turn questions with clean, cited answers are cached; follow-ups depend on chat history so they skip it. Briefs are cached per product, audience and goal. Cached responses carry `cached: true`. |
| Abuse and cost | KV rate limit (checked before the cache), AI Gateway caching and analytics, question length cap, `ADMIN_TOKEN` on ingest (rejected if unset). |

Known limits: `MIN_SCORE` (0.55) is a starting point and cannot separate in-scope from out-of-scope questions on its own (see the retrieval benchmark), so refusal of unknown topics relies on the model and the output guardrail. The banned-term list is hard-coded in `src/guard.ts` and must be kept in sync with the brand doc. Citation checks prove a source was referenced, not that the claim matches it.

## Tests and benchmarks

Three layers, from cheapest to most realistic:

| Command | Needs Worker? | LLM calls? | What it tells you |
| --- | --- | --- | --- |
| `npm test` | no | no | Logic: guardrails, citation parsing, cache key, **and the eval harness itself** (scorer, aggregation, dataset validity against the knowledge base). Safe for CI. |
| `npm run eval:retrieval` | yes + `ADMIN_TOKEN` | no | Retrieval quality: recall@1/3/6, MRR, and where `MIN_SCORE` sits between in-scope and out-of-scope scores. Independent of prompts, so use it to tell retrieval regressions from prompt regressions. |
| `npm run eval` | yes + `ADMIN_TOKEN` | yes | End-to-end behaviour on `scripts/eval/cases.json`: every case runs `--runs` times (default 3) to expose flakiness. |

**Dataset** (`scripts/eval/cases.json`): factual questions, paraphrase groups (same question, different wording), compliance traps, out-of-scope questions (must be refused), known gaps (over-45 and men's skincare must not get invented numbers), hard and soft prompt injections, multi-source questions and creative briefs. Each case lists the allowed outcomes (`answered`, `insufficient`, `blocked_input`, `blocked_output`), required and forbidden patterns, and which source document must be cited.

**Checks applied to every response**, whatever the case: no error, no leaked system prompt, answered ⇒ sources returned and every `[n]` has a source, not answered ⇒ no sources.

**Pass criteria** (`scripts/eval/thresholds.json`): overall at least 90%; per-category minimums (out-of-scope and injection must be 100%); at most 15% flaky cases (a case that passes some runs but not all); retrieval recall@3 and MRR minimums. Exit code is 1 if any fails, so it can gate a release.

**Changing a prompt safely**

```bash
npm run eval -- --save-baseline        # once, on the known-good prompt (writes scripts/eval/baseline.json)
# ...edit src/prompts.ts, let wrangler dev reload...
npm run eval:compare                   # re-runs and reports per-case regressions and improvements
```

The report prints the prompt version before and after (`promptVersion` hash), per-category rates, p50/p95 latency, the failing runs with a sample answer, and any case whose pass rate dropped by a third or more. Useful flags: `--runs 5`, `--category factual,injection`, `--id fact-serum-price`, `--concurrency 1`, `--base https://your-worker.workers.dev`.

Eval runs bypass the cache and rate limit (admin token), call the real models, and are non-deterministic, so expect small run-to-run differences; that is what the repeated runs measure. Results are written to `scripts/eval/results/` (git-ignored).

**Free-tier cost warning.** The full eval (about 50 cases x 3 runs, each running one embedding call and one or two LLM calls) consumed most of the 10,000-neuron daily Workers AI allowance on the free plan; two full runs plus debugging exhausted it. When that happens Workers AI returns error 4006, the Worker answers `503 ai_quota_exceeded`, and the runner aborts with exit code 3 instead of scoring the failures. On the free plan use `--runs 1`, `--category ...` or `--id ...`, run `npm run eval:retrieval` (embeddings only) freely, or use a Workers Paid plan. The allowance resets at 00:00 UTC.

## Deploy

1. `npm install` and `npx wrangler login`.
2. `npm run setup` creates Vectorize, R2, D1 and KV. Paste the printed D1 `database_id` and KV `id` into `wrangler.jsonc`.
3. `npx wrangler d1 execute company-brain --remote --file=schema.sql`
4. `npx wrangler secret put ADMIN_TOKEN` (generate a value as in the [guide](#admin_token-guide); use a different one from local).
5. AI Gateway with Guardrails (needs an API token with *AI Gateway: Edit*; export it in your shell rather than writing it to `.env`):
   ```bash
   CLOUDFLARE_ACCOUNT_ID=... CLOUDFLARE_API_TOKEN=... bash scripts/configure-gateway.sh
   ```
   `wrangler.jsonc` already sets `GATEWAY_ID` to `company-brain`.
6. `npm run deploy`
7. `bash scripts/ingest.sh https://company-brain.<you>.workers.dev <ADMIN_TOKEN>` uploads `knowledge/` to R2 and indexes it.
8. `npm run eval -- --base https://company-brain.<you>.workers.dev` to verify the deployment.

## API

| Endpoint | Auth | Body | Notes |
| --- | --- | --- | --- |
| `POST /api/chat` | none | `{question, sessionId?}` | Returns `answer`, `answered`, `sources[]`, plus `blocked` / `cached` / `violations` when relevant. |
| `POST /api/brief` | none | `{product, audience, goal}` | Creative brief with fixed headings, cited. |
| `POST /api/reset` | none | `{sessionId}` | Clears a session's chat history. |
| `POST /api/ingest` | `ADMIN_TOKEN` | none | Chunks, embeds and indexes `knowledge/` from R2. |
| `POST /api/retrieve` | `ADMIN_TOKEN` | `{question, topK?}` | Raw retrieval hits and scores. |
| `GET /api/health` | none | none | `{ok, promptVersion, minScore}`. |

## Status

Verified locally against live Workers AI and Vectorize (`wrangler dev`, D1/KV/R2/Durable Object local):

- `npm test`: 32 offline tests pass (guardrails, injection and context-dump screening, leak detection, number grounding, quota and gateway error codes, cache key, eval scorer, dataset validity).
- Retrieval benchmark: recall@3 100%, MRR 0.96. `MIN_SCORE` cannot separate in-scope from out-of-scope questions (highest out-of-scope score 0.76 vs lowest in-scope 0.66), so refusing unknown topics depends on the model and the output guardrail.
- End-to-end eval, final prompt (`6d86c291`): 98% overall on 50 cases x 1 run, with factual, paraphrase, compliance, out-of-scope, known-gap, injection and multi-source all at 100%; then brief and soft-injection cases x 3 runs: all thresholds passed. `brief-bundle` is still occasionally flaky (it sometimes omits the $66 price).
- The eval drove these fixes: the number check rejecting facts that appear only in a document title; hard blocks on invented numbers (now one rewrite attempt, as for briefs); brief retrieval drifting away from the product chunk (now a separate product query); a prompt leak when asked to copy the SOURCES block (now blocked at input and checked on output).

Not verified: **AI Gateway and its Llama Guard Guardrails** have never been exercised, and `scripts/configure-gateway.sh` has not run against a real account (the available API tokens lacked AI Gateway permission). Local runs skip the gateway (`GATEWAY_ID=`). No baseline is saved yet; run `npm run eval -- --save-baseline` on a known-good prompt. A fresh Vectorize index can return nothing or an upstream error for the first queries, so retry once before debugging.

Not used: Browser Rendering and the Agents framework. They aren't needed for this demo.
