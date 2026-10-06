#!/usr/bin/env node
// Eval + benchmark runner. Needs a running Worker (wrangler dev or deployed) with ingested docs.
//
//   node scripts/eval/run.mjs                      # retrieval + e2e, 3 runs per case
//   node scripts/eval/run.mjs --mode retrieval     # no LLM calls, fast, prompt-independent
//   node scripts/eval/run.mjs --runs 5 --category factual,injection
//   node scripts/eval/run.mjs --save-baseline      # store results as the baseline
//   node scripts/eval/run.mjs --baseline scripts/eval/baseline.json   # compare after a prompt change
//
// Env/flags: --base (default http://127.0.0.1:8787), ADMIN_TOKEN (env or ../.env) for cache/rate-limit bypass.
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  aggregate, checkThresholds, compareToBaseline, pct, rankOfExpected,
  retrievalMetrics, scoreCase,
} from "./score.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, all) => {
    if (a.startsWith("--")) acc.push([a.slice(2), all[i + 1]?.startsWith("--") || all[i + 1] === undefined ? true : all[i + 1]]);
    return acc;
  }, []),
);

const BASE = (args.base ?? process.env.EVAL_BASE ?? "http://127.0.0.1:8787").replace(/\/$/, "");
const RUNS = Number(args.runs ?? 3);
const MODE = args.mode ?? "all";
const CONCURRENCY = Number(args.concurrency ?? 2);

function loadToken() {
  if (process.env.ADMIN_TOKEN) return process.env.ADMIN_TOKEN;
  const envFile = join(here, "../../.env");
  if (existsSync(envFile)) {
    const m = readFileSync(envFile, "utf8").match(/^ADMIN_TOKEN=(.+)$/m);
    if (m) return m[1].trim();
  }
  return "";
}
const TOKEN = loadToken();
if (!TOKEN) console.warn("! No ADMIN_TOKEN: cache and rate limit are NOT bypassed, and retrieval mode is unavailable.");

const cases = JSON.parse(readFileSync(join(here, "cases.json"), "utf8")).cases
  .filter((c) => !args.category || String(args.category).split(",").includes(c.category))
  .filter((c) => !args.id || String(args.id).split(",").includes(c.id));
const thresholds = JSON.parse(readFileSync(join(here, "thresholds.json"), "utf8"));

const headers = {
  "content-type": "application/json",
  ...(TOKEN ? { authorization: `Bearer ${TOKEN}`, "x-no-cache": "1" } : {}),
};

async function post(path, body) {
  const t = performance.now();
  try {
    const res = await fetch(BASE + path, { method: "POST", headers, body: JSON.stringify(body) });
    const data = await res.json().catch(() => ({ error: `non-JSON response (HTTP ${res.status})` }));
    if (!res.ok && !data.blocked) data.error ??= `HTTP ${res.status}`;
    return { data, ms: performance.now() - t };
  } catch (e) {
    return { data: { error: `network: ${e.message}` }, ms: performance.now() - t };
  }
}

let quotaHit = false;
async function pool(items, worker) {
  const results = new Array(items.length);
  let next = 0;
  await Promise.all(Array.from({ length: CONCURRENCY }, async () => {
    while (next < items.length && !quotaHit) { const i = next++; results[i] = await worker(items[i], i); }
  }));
  return results;
}

// ---------- retrieval benchmark ----------
async function retrievalBenchmark() {
  const targets = cases.filter((c) => !c.kind && c.expectDocs?.length);
  const oos = cases.filter((c) => c.category === "out_of_scope");
  const rows = await pool([...targets, ...oos], async (c) => {
    let { data } = await post("/api/retrieve", { question: c.question, topK: 6 });
    // A fresh Vectorize index can return nothing for the first queries; retry once before scoring.
    if (!data.error && !(data.hits ?? []).length) ({ data } = await post("/api/retrieve", { question: c.question, topK: 6 }));
    return { c, hits: data.hits ?? [], error: data.error };
  });
  const bad = rows.find((r) => r.error);
  if (bad) { console.error(`Retrieval benchmark unavailable: ${bad.error}`); return { skipped: true }; }

  const inScope = rows.filter((r) => r.c.expectDocs?.length).map((r) => ({
    id: r.c.id, rank: rankOfExpected(r.hits, r.c.expectDocs), top: r.hits[0]?.score ?? 0,
  }));
  const m = retrievalMetrics(inScope);
  const minScore = (await (await fetch(BASE + "/api/health")).json()).minScore;
  const topOut = rows.filter((r) => r.c.category === "out_of_scope").map((r) => r.hits[0]?.score ?? 0);
  const belowThreshold = inScope.filter((r) => r.top < minScore).map((r) => r.id);

  console.log("\n=== Retrieval benchmark (no LLM) ===");
  console.log(`questions: ${m.n}   recall@1 ${pct(m.recallAt1)}   recall@3 ${pct(m.recallAt3)}   recall@6 ${pct(m.recallAt6)}   MRR ${m.mrr.toFixed(2)}`);
  const minIn = Math.min(...inScope.map((r) => r.top));
  const maxOut = Math.max(0, ...topOut);
  console.log(`MIN_SCORE ${minScore}: lowest in-scope top score ${minIn.toFixed(3)}, highest out-of-scope top score ${maxOut.toFixed(3)}`);
  console.log(belowThreshold.length ? `! in-scope questions that would be refused by the threshold: ${belowThreshold.join(", ")}` : "in-scope questions all clear the threshold");
  console.log(`out-of-scope passing the threshold (must be refused by the model): ${topOut.filter((s) => s >= minScore).length}/${topOut.length}`);
  for (const r of inScope.filter((r) => r.rank === 0 || r.rank > 3)) console.log(`  miss: ${r.id} rank=${r.rank}`);

  const failures = [];
  if (m.recallAt3 < thresholds.retrieval.recallAt3) failures.push(`recall@3 ${pct(m.recallAt3)} < ${pct(thresholds.retrieval.recallAt3)}`);
  if (m.mrr < thresholds.retrieval.mrr) failures.push(`MRR ${m.mrr.toFixed(2)} < ${thresholds.retrieval.mrr}`);
  if (belowThreshold.length) failures.push(`${belowThreshold.length} in-scope question(s) below MIN_SCORE`);
  return { metrics: m, minScore, minIn, maxOut, failures };
}

// ---------- end-to-end eval ----------
async function e2e() {
  const jobs = cases.flatMap((c) => Array.from({ length: RUNS }, (_, run) => ({ c, run })));
  console.log(`\nRunning ${cases.length} cases x ${RUNS} runs = ${jobs.length} calls against ${BASE} ...`);
  let done = 0;
  const runs = await pool(jobs, async ({ c, run }) => {
    const { data, ms } = c.kind === "brief"
      ? await post("/api/brief", c.input)
      : await post("/api/chat", { question: c.question, sessionId: `eval-${c.id}-${run}-${Date.now()}` });
    if (data.error === "ai_quota_exceeded") quotaHit = true;
    const s = scoreCase(c, data);
    process.stdout.write(s.pass ? "." : "F");
    if (++done % 60 === 0) process.stdout.write("\n");
    return { id: c.id, category: c.category, group: c.group, ...s, ms, answer: (data.answer ?? data.error ?? "").slice(0, 300) };
  });
  console.log("\n");
  return runs;
}

function report(runs, summary) {
  console.log("=== End-to-end eval ===");
  console.log(`overall ${pct(summary.overall)}   flaky cases ${pct(summary.flakyFraction)}   latency p50 ${(summary.latency.p50 / 1000).toFixed(1)}s  p95 ${(summary.latency.p95 / 1000).toFixed(1)}s  max ${(summary.latency.max / 1000).toFixed(1)}s`);
  console.log("by category:");
  for (const [cat, r] of Object.entries(summary.categories)) {
    const min = thresholds.perCategory[cat];
    console.log(`  ${cat.padEnd(15)} ${pct(r).padStart(5)}${min !== undefined ? `   (min ${pct(min)})${r < min ? "  <-- FAIL" : ""}` : ""}`);
  }
  const inconsistent = Object.entries(summary.groupConsistency).filter(([, ok]) => !ok).map(([g]) => g);
  if (inconsistent.length) console.log(`paraphrase groups with inconsistent answers: ${inconsistent.join(", ")}`);
  const bad = summary.cases.filter((c) => c.rate < 1).sort((a, b) => a.rate - b.rate);
  if (bad.length) {
    console.log("\ncases that did not pass every run:");
    for (const c of bad) {
      console.log(`  ${c.flaky ? "FLAKY" : "FAIL "} ${c.id} ${c.passes}/${c.runs}`);
      for (const [f, n] of Object.entries(c.failures)) console.log(`        ${n}x ${f}`);
      const sample = runs.find((r) => r.id === c.id && !r.pass);
      if (sample) console.log(`        e.g. "${sample.answer.replace(/\s+/g, " ").slice(0, 160)}"`);
    }
  }
}

// ---------- main ----------
const health = await fetch(BASE + "/api/health").then((r) => r.json()).catch(() => null);
if (!health) { console.error(`Cannot reach ${BASE}. Start the Worker first (npx wrangler dev).`); process.exit(2); }
console.log(`Target ${BASE}   prompt version ${health.promptVersion}   MIN_SCORE ${health.minScore}`);

const failures = [];
let summary = null;
if (MODE === "all" || MODE === "retrieval") {
  if (TOKEN) { const r = await retrievalBenchmark(); failures.push(...(r.failures ?? [])); }
  else console.log("Skipping retrieval benchmark (needs ADMIN_TOKEN).");
}
if (MODE === "all" || MODE === "e2e") {
  const runs = await e2e();
  summary = aggregate(runs);
  report(runs, summary);
  failures.push(...checkThresholds(summary, thresholds));

  if (args.baseline && args.baseline !== true) {
    const base = JSON.parse(readFileSync(args.baseline, "utf8"));
    const { regressions, improvements } = compareToBaseline(summary, base.summary, thresholds.regressionDrop);
    console.log(`\n=== vs baseline (prompt ${base.promptVersion} -> ${health.promptVersion}) ===`);
    console.log(`overall ${pct(base.summary.overall)} -> ${pct(summary.overall)}`);
    for (const r of improvements) console.log(`  improved  ${r.id} ${pct(r.before)} -> ${pct(r.after)}`);
    for (const r of regressions) {
      console.log(`  REGRESSED ${r.id} ${pct(r.before)} -> ${pct(r.after)}`);
      failures.push(`regression: ${r.id} ${pct(r.before)} -> ${pct(r.after)}`);
    }
    if (!regressions.length) console.log("  no per-case regressions");
  }

  const out = args.out && args.out !== true ? args.out : join(here, "results", `${new Date().toISOString().replace(/[:.]/g, "-")}.json`);
  mkdirSync(dirname(out), { recursive: true });
  const payload = { date: new Date().toISOString(), base: BASE, promptVersion: health.promptVersion, runsPerCase: RUNS, summary, runs };
  writeFileSync(out, JSON.stringify(payload, null, 1));
  console.log(`\nresults: ${out}`);
  if (args["save-baseline"]) {
    const bp = join(here, "baseline.json");
    writeFileSync(bp, JSON.stringify({ ...payload, runs: undefined }, null, 1));
    console.log(`baseline saved: ${bp}`);
  }
}

console.log(failures.length ? `\nFAILED:\n - ${failures.join("\n - ")}` : "\nPASSED all thresholds.");
process.exit(failures.length ? 1 : 0);
