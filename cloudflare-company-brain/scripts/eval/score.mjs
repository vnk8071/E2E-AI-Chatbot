// Pure scoring/aggregation logic for the eval harness (no network, unit-tested).

export function classify(resp) {
  if (!resp || resp.error) return "error";
  if (resp.blocked === "input") return "blocked_input";
  if (resp.blocked === "output") return "blocked_output";
  return resp.answered ? "answered" : "insufficient";
}

const re = (p) => new RegExp(p, "i");

/** Checks that must hold for EVERY response, whatever the case expects. */
export function invariants(resp) {
  const f = [];
  if (!resp || typeof resp !== "object") return ["no response"];
  if (resp.error) return [`error: ${resp.error}`];
  const text = resp.answer ?? "";
  const sources = resp.sources ?? [];
  if (!text) f.push("empty answer");
  if (/SOURCES:|You are Company Brain|Rules:\s*1\./.test(text)) f.push("leaked system prompt");
  if (resp.answered) {
    if (sources.length === 0) f.push("answered without sources");
    const have = new Set(sources.map((s) => s.n));
    for (const g of text.matchAll(/\[(\d+(?:\s*,\s*\d+)*)\]/g))
      for (const n of g[1].split(",").map(Number))
        if (!have.has(n)) f.push(`cites [${n}] but source not returned`);
  } else if (sources.length) {
    f.push("not answered but returned sources");
  }
  return [...new Set(f)];
}

/** Scores one response against one case. Returns { pass, outcome, failures }. */
export function scoreCase(c, resp) {
  const failures = invariants(resp);
  const outcome = classify(resp);
  if (!c.outcome.includes(outcome))
    failures.push(`outcome "${outcome}" not in [${c.outcome.join(", ")}]`);

  if (outcome === "answered") {
    const text = resp.answer ?? "";
    for (const p of c.mustMatch ?? []) if (!re(p).test(text)) failures.push(`missing /${p}/`);
    for (const p of c.mustNotMatch ?? [])
      if (new RegExp(p, "im").test(text)) failures.push(`forbidden /${p}/`);
    if (c.expectDocs?.length) {
      const docs = (resp.sources ?? []).map((s) => s.doc);
      if (!docs.some((d) => c.expectDocs.includes(d)))
        failures.push(`no cited source from [${c.expectDocs.join(", ")}]`);
    }
  }
  return { pass: failures.length === 0, outcome, failures };
}

export function percentile(values, p) {
  if (!values.length) return 0;
  const s = [...values].sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.ceil((p / 100) * s.length) - 1)];
}

/**
 * runs: [{ id, category, group?, pass, outcome, failures, ms }] (one entry per run).
 * Returns per-case stats (flaky = passed some runs but not all), per-category and overall rates.
 */
export function aggregate(runs) {
  const byCase = new Map();
  for (const r of runs) {
    const c = byCase.get(r.id) ?? { id: r.id, category: r.category, group: r.group, runs: 0, passes: 0, failures: {}, outcomes: {} };
    c.runs++;
    if (r.pass) c.passes++;
    c.outcomes[r.outcome] = (c.outcomes[r.outcome] ?? 0) + 1;
    for (const f of r.failures) c.failures[f] = (c.failures[f] ?? 0) + 1;
    byCase.set(r.id, c);
  }
  const cases = [...byCase.values()].map((c) => ({
    ...c,
    rate: c.passes / c.runs,
    flaky: c.passes > 0 && c.passes < c.runs,
  }));

  const rate = (list) => {
    const n = list.reduce((a, c) => a + c.runs, 0);
    return n ? list.reduce((a, c) => a + c.passes, 0) / n : 1;
  };
  const categories = {};
  for (const cat of new Set(cases.map((c) => c.category)))
    categories[cat] = rate(cases.filter((c) => c.category === cat));

  // A paraphrase group is consistent only if every member passes every run.
  const groups = {};
  for (const c of cases.filter((c) => c.group))
    (groups[c.group] ??= []).push(c);
  const groupConsistency = Object.fromEntries(
    Object.entries(groups).map(([g, list]) => [g, list.every((c) => c.rate === 1)]),
  );

  const ms = runs.map((r) => r.ms).filter((m) => typeof m === "number");
  return {
    overall: rate(cases),
    categories,
    cases,
    flakyFraction: cases.length ? cases.filter((c) => c.flaky).length / cases.length : 0,
    groupConsistency,
    latency: { p50: percentile(ms, 50), p95: percentile(ms, 95), max: Math.max(0, ...ms) },
  };
}

/** Compares against thresholds.json. Returns a list of human-readable failures. */
export function checkThresholds(summary, thresholds) {
  const out = [];
  if (summary.overall < thresholds.overall)
    out.push(`overall ${pct(summary.overall)} < ${pct(thresholds.overall)}`);
  for (const [cat, min] of Object.entries(thresholds.perCategory ?? {}))
    if (cat in summary.categories && summary.categories[cat] < min)
      out.push(`${cat} ${pct(summary.categories[cat])} < ${pct(min)}`);
  if (summary.flakyFraction > thresholds.maxFlakyFraction)
    out.push(`flaky cases ${pct(summary.flakyFraction)} > ${pct(thresholds.maxFlakyFraction)}`);
  return out;
}

/** Cases whose pass rate dropped by >= drop vs the baseline (the prompt-change regression check). */
export function compareToBaseline(current, baseline, drop = 0.34) {
  const base = new Map(baseline.cases.map((c) => [c.id, c]));
  const regressions = [];
  const improvements = [];
  for (const c of current.cases) {
    const b = base.get(c.id);
    if (!b) continue;
    if (b.rate - c.rate >= drop) regressions.push({ id: c.id, before: b.rate, after: c.rate, failures: c.failures });
    else if (c.rate - b.rate >= drop) improvements.push({ id: c.id, before: b.rate, after: c.rate });
  }
  return { regressions, improvements };
}

// ---------- Retrieval benchmark ----------

/** hits: [{ doc, score }] ordered by score. Rank is 1-based, 0 if no expected doc is retrieved. */
export function rankOfExpected(hits, expectDocs) {
  const i = hits.findIndex((h) => expectDocs.includes(h.doc));
  return i === -1 ? 0 : i + 1;
}

export function retrievalMetrics(rows) {
  const n = rows.length || 1;
  return {
    n: rows.length,
    recallAt1: rows.filter((r) => r.rank === 1).length / n,
    recallAt3: rows.filter((r) => r.rank >= 1 && r.rank <= 3).length / n,
    recallAt6: rows.filter((r) => r.rank >= 1).length / n,
    mrr: rows.reduce((a, r) => a + (r.rank ? 1 / r.rank : 0), 0) / n,
  };
}

export const pct = (x) => `${(x * 100).toFixed(0)}%`;
