// Offline tests for the eval harness itself (no Worker needed): npm test
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  aggregate, checkThresholds, classify, compareToBaseline, invariants, percentile,
  rankOfExpected, retrievalMetrics, scoreCase,
} from "./eval/score.mjs";
import { PROMPT_VERSION } from "../src/prompts.ts";

const dataset = JSON.parse(readFileSync(new URL("./eval/cases.json", import.meta.url), "utf8")).cases;
const thresholds = JSON.parse(readFileSync(new URL("./eval/thresholds.json", import.meta.url), "utf8"));
const OUTCOMES = ["answered", "insufficient", "blocked_input", "blocked_output"];

const good = { answer: "It costs $34 [1].", answered: true, sources: [{ n: 1, doc: "product-catalog.md" }] };

// ---------- dataset validity ----------
test("dataset: unique ids, valid outcomes, valid regexes, known categories", () => {
  const ids = new Set();
  for (const c of dataset) {
    assert.ok(!ids.has(c.id), `duplicate id ${c.id}`);
    ids.add(c.id);
    assert.ok(c.kind === "brief" ? c.input?.product : c.question, `${c.id} needs question or brief input`);
    assert.ok(c.outcome?.length && c.outcome.every((o) => OUTCOMES.includes(o)), `${c.id} outcome`);
    for (const p of [...(c.mustMatch ?? []), ...(c.mustNotMatch ?? [])]) new RegExp(p, "i");
    assert.ok(c.category in { ...thresholds.perCategory }, `${c.id}: category ${c.category} has no threshold`);
  }
});
test("dataset: covers every safety behaviour and enough paraphrases", () => {
  const cats = new Set(dataset.map((c) => c.category));
  for (const need of ["factual", "paraphrase", "compliance", "out_of_scope", "injection", "known_gap", "brief"])
    assert.ok(cats.has(need), `missing category ${need}`);
  const groups = {};
  for (const c of dataset.filter((c) => c.group)) groups[c.group] = (groups[c.group] ?? 0) + 1;
  assert.ok(Object.values(groups).every((n) => n >= 2), "each paraphrase group needs 2+ members");
  assert.ok(dataset.filter((c) => c.category === "out_of_scope").every((c) => c.outcome.join() === "insufficient"));
  assert.ok(dataset.filter((c) => c.category === "injection").every((c) => c.outcome.join() === "blocked_input"));
});
test("dataset: factual expectations match the actual knowledge base", () => {
  const kb = ["product-catalog", "brand-guidelines", "compliance-rules", "sop-creative-briefs", "customer-research", "creative-learnings"]
    .map((n) => readFileSync(new URL(`../knowledge/${n}.md`, import.meta.url), "utf8")).join("\n");
  for (const c of dataset.filter((c) => c.category === "factual"))
    for (const p of c.mustMatch ?? []) assert.match(kb, new RegExp(p.replace(/\\\$/g, "\\$").split("|")[0], "i"), `${c.id}: "${p}" not found in knowledge base`);
  for (const c of dataset.filter((c) => c.expectDocs))
    for (const d of c.expectDocs) assert.ok(kb.length && readFileSync(new URL(`../knowledge/${d}`, import.meta.url)), d);
});

// ---------- scorer ----------
test("classify maps responses to outcome classes", () => {
  assert.equal(classify(good), "answered");
  assert.equal(classify({ answered: false, sources: [] }), "insufficient");
  assert.equal(classify({ blocked: "input" }), "blocked_input");
  assert.equal(classify({ blocked: "output" }), "blocked_output");
  assert.equal(classify({ error: "boom" }), "error");
});
test("a correct grounded answer passes", () => {
  const c = { outcome: ["answered"], expectDocs: ["product-catalog.md"], mustMatch: ["\\$34"] };
  assert.deepEqual(scoreCase(c, good), { pass: true, outcome: "answered", failures: [] });
});
test("wrong outcome, missing fact and wrong source each fail", () => {
  const c = { outcome: ["answered"], expectDocs: ["brand-guidelines.md"], mustMatch: ["\\$99"] };
  const r = scoreCase(c, good);
  assert.equal(r.pass, false);
  assert.equal(r.failures.length, 2);
  assert.equal(scoreCase({ outcome: ["insufficient"] }, good).pass, false);
});
test("forbidden pattern fails an otherwise valid answer", () => {
  const c = { outcome: ["answered"], mustNotMatch: ["^\\s*yes"] };
  assert.equal(scoreCase(c, { ...good, answer: "Yes, it is fine [1]." }).pass, false);
});
test("invariants catch prompt leaks, uncited sources, and phantom sources", () => {
  assert.ok(invariants({ ...good, answer: "SOURCES: [1] ..." }).includes("leaked system prompt"));
  assert.ok(invariants({ ...good, answer: "Cost $34 [2]." }).some((f) => f.includes("[2]")));
  assert.ok(invariants({ ...good, sources: [] }).includes("answered without sources"));
  assert.ok(invariants({ answer: "No.", answered: false, sources: [{ n: 1 }] }).includes("not answered but returned sources"));
  assert.deepEqual(invariants(good), []);
});
test("HTTP/network errors always fail", () => {
  assert.equal(scoreCase({ outcome: ["answered", "insufficient"] }, { error: "HTTP 500" }).pass, false);
});

// ---------- aggregation, thresholds, baseline ----------
const run = (id, pass, category = "factual", extra = {}) => ({ id, category, pass, outcome: "answered", failures: pass ? [] : ["x"], ms: 1000, ...extra });

test("aggregate computes rates, flakiness and percentiles", () => {
  const s = aggregate([run("a", true), run("a", true), run("a", true), run("b", true), run("b", false), run("b", false)]);
  assert.equal(s.cases.find((c) => c.id === "a").flaky, false);
  assert.equal(s.cases.find((c) => c.id === "b").flaky, true);
  assert.equal(s.flakyFraction, 0.5);
  assert.equal(s.overall, 4 / 6);
  assert.equal(percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 95), 10);
});
test("paraphrase groups are consistent only if every member always passes", () => {
  const s = aggregate([
    run("p1", true, "paraphrase", { group: "g" }), run("p2", false, "paraphrase", { group: "g" }),
    run("q1", true, "paraphrase", { group: "h" }), run("q2", true, "paraphrase", { group: "h" }),
  ]);
  assert.deepEqual(s.groupConsistency, { g: false, h: true });
});
test("thresholds flag low categories, overall and flakiness", () => {
  const s = aggregate([run("a", true, "injection"), run("b", false, "injection"), run("c", true), run("d", true)]);
  const fails = checkThresholds(s, thresholds);
  assert.ok(fails.some((f) => f.startsWith("injection")));
  assert.ok(fails.some((f) => f.startsWith("overall")));
  assert.deepEqual(checkThresholds(aggregate([run("a", true), run("b", true)]), thresholds), []);
});
test("baseline comparison reports regressions and improvements", () => {
  const base = aggregate([run("a", true), run("a", true), run("a", true), run("b", false), run("b", false), run("b", false)]);
  const cur = aggregate([run("a", false), run("a", false), run("a", true), run("b", true), run("b", true), run("b", true)]);
  const { regressions, improvements } = compareToBaseline(cur, base, 0.34);
  assert.deepEqual(regressions.map((r) => r.id), ["a"]);
  assert.deepEqual(improvements.map((r) => r.id), ["b"]);
});

// ---------- retrieval metrics ----------
test("rank and retrieval metrics", () => {
  const hits = [{ doc: "x.md" }, { doc: "y.md" }, { doc: "z.md" }];
  assert.equal(rankOfExpected(hits, ["y.md"]), 2);
  assert.equal(rankOfExpected(hits, ["nope.md"]), 0);
  const m = retrievalMetrics([{ rank: 1 }, { rank: 2 }, { rank: 0 }, { rank: 5 }]);
  assert.equal(m.recallAt1, 0.25);
  assert.equal(m.recallAt3, 0.5);
  assert.equal(m.recallAt6, 0.75);
  assert.ok(Math.abs(m.mrr - (1 + 0.5 + 0 + 0.2) / 4) < 1e-9);
});

// ---------- prompt versioning ----------
test("prompt version is a stable 8-char hash", () => {
  assert.match(PROMPT_VERSION, /^[0-9a-f]{8}$/);
});
