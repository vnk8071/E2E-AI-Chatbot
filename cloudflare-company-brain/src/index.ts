import {
  aiQuotaExceeded, BLOCKED_INPUT, BLOCKED_OUTPUT, checkInput, citedSources, gatewayBlock,
  INSUFFICIENT, outputViolations,
} from "./guard";
import {
  cacheGet, cacheKey, cacheSet, chat, ingest, logQuery, mandatoryRules,
  rateLimited, retrieve, type Env, type Hit,
} from "./rag";
import { BRIEF_INSTRUCTIONS, PROMPT_VERSION, SYSTEM } from "./prompts";
import { ChatSession } from "./session";

export { ChatSession };

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  });

type Source = { title: string; type: string; doc: string; text: string };
type Result = {
  answer: string;
  answered: boolean;
  blocked?: "input" | "output";
  cached?: boolean;
  violations?: string[];
  draft?: string; // blocked answer text; only included for admin eval/debug requests
  sources: unknown[];
};

function sourceBlock(sources: Source[]) {
  return sources
    .map((s, i) => `[${i + 1}] (${s.type.toUpperCase()}) ${s.title}\n${s.text}`)
    .join("\n\n");
}

/** Merge retrieved hits with always-on rules, de-duplicated, hits first. */
async function buildSources(env: Env, hits: Hit[]): Promise<Source[]> {
  const rules = await mandatoryRules(env);
  const seen = new Set(hits.map((h) => h.id));
  return [...hits, ...rules.filter((r) => !seen.has(r.id))];
}

const toSources = (sources: Source[], cited: number[]) =>
  cited.map((n) => ({
    n,
    title: sources[n - 1].title,
    type: sources[n - 1].type,
    doc: sources[n - 1].doc,
    excerpt: sources[n - 1].text.slice(0, 280),
  }));

const inputBlocked = (): Result => ({
  answer: BLOCKED_INPUT, answered: false, blocked: "input", sources: [],
});
const outputBlocked = (violations: string[], draft?: string): Result => ({
  answer: BLOCKED_OUTPUT, answered: false, blocked: "output", violations, sources: [],
  ...(draft ? { draft } : {}),
});

/** Text a claim may be grounded in: chunk bodies plus their titles (titles carry facts like "survey of 214"). */
const groundingText = (sources: Source[]) =>
  sources.map((s) => [s.title, s.text].join(" ")).join(" ");

/**
 * Generates an answer and checks it against the output guardrail. On a violation the model gets
 * the exact problems fed back for one rewrite; whatever remains is returned for the caller to block.
 */
async function generateChecked(
  env: Env,
  messages: { role: string; content: string }[],
  grounding: string,
  maxTokens?: number,
): Promise<{ answer: string; violations: string[] }> {
  let answer = await chat(env, messages, maxTokens);
  let violations = outputViolations(answer, grounding);
  if (violations.length) {
    answer = await chat(
      env,
      [
        ...messages,
        { role: "assistant", content: answer },
        {
          role: "user",
          content: `Your draft broke these rules: ${violations.join("; ")}. Rewrite it using only facts and numbers that appear in the SOURCES, keeping the [n] citations.`,
        },
      ],
      maxTokens,
    );
    violations = outputViolations(answer, grounding);
  }
  return { answer, violations };
}

async function ask(env: Env, question: string, sessionId: string, noCache = false): Promise<Result> {
  // Guardrail 1: screen the prompt before any embedding, retrieval or LLM call.
  const gate = checkInput(question);
  if (!gate.ok) {
    await logQuery(env, question, false, null, `input-guardrail:${gate.reason}`);
    return inputBlocked();
  }

  // Cache: only first-turn questions, since later answers depend on chat history.
  const session = env.SESSION.get(env.SESSION.idFromName(sessionId));
  const history = await session.history();
  const key = history.length === 0 && !noCache ? await cacheKey(env, "ans", question) : null;
  if (key) {
    const hit = await cacheGet<Result>(env, key);
    if (hit) {
      await logQuery(env, question, true, null, "cache-hit");
      return { ...hit, cached: true };
    }
  }

  const minScore = Number(env.MIN_SCORE);
  const hits = (await retrieve(env, question)).filter((h) => h.score >= minScore);
  const top = hits[0]?.score ?? null;

  // Reliability gate: no LLM call if retrieval found nothing relevant enough.
  if (!hits.length) {
    await logQuery(env, question, false, top, "below-threshold");
    return { answer: INSUFFICIENT, sources: [], answered: false };
  }

  const sources = await buildSources(env, hits);
  // Guardrail 2 (inside generateChecked): banned terms and numbers not in the sources,
  // with one rewrite attempt before giving up.
  const { answer, violations } = await generateChecked(
    env,
    [
      { role: "system", content: `${SYSTEM}\n\nSOURCES:\n${sourceBlock(sources)}` },
      ...history,
      { role: "user", content: question },
    ],
    groundingText(sources),
  );

  const cited = citedSources(answer, sources.length);
  const refused = answer.includes(INSUFFICIENT);
  // A grounded answer must cite at least one real source; otherwise treat as unsupported.
  if (!violations.length && (refused || cited.length === 0)) {
    await logQuery(env, question, false, top, refused ? "model-refused" : "no-citations");
    return { answer: INSUFFICIENT, sources: [], answered: false };
  }

  if (violations.length) {
    await logQuery(env, question, false, top, `output-guardrail:${violations.join("; ")}`);
    return outputBlocked(violations, noCache ? answer : undefined);
  }

  await session.append(
    { role: "user", content: question },
    { role: "assistant", content: answer },
  );
  await logQuery(env, question, true, top, "ok");
  const result: Result = {
    answer, answered: true, sources: toSources(sources, cited),
  };
  if (key) await cacheSet(env, key, result);
  return result;
}

async function brief(env: Env, product: string, audience: string, goal: string, noCache = false): Promise<Result> {
  const request = `Product: ${product}\nAudience: ${audience}\nGoal: ${goal}`;
  const gate = checkInput(request);
  if (!gate.ok) {
    await logQuery(env, request, false, null, `input-guardrail:${gate.reason}`);
    return inputBlocked();
  }

  const key = noCache ? null : await cacheKey(env, "brief", request);
  const hit = key ? await cacheGet<Result>(env, key) : null;
  if (hit) return { ...hit, cached: true };

  // Two retrievals: the product's own facts, plus audience/goal context. A single combined query
  // drifts toward research and learnings docs and can drop the product chunk.
  const minScore = Number(env.MIN_SCORE);
  const [productHits, contextHits] = await Promise.all([
    retrieve(env, product, 3),
    retrieve(env, `${audience} ${goal} customer insights creative learnings`, 6),
  ]);
  const seenIds = new Set<string>();
  const hits = [...productHits, ...contextHits].filter((h) => {
    if (h.score < minScore || seenIds.has(h.id)) return false;
    seenIds.add(h.id);
    return true;
  });
  if (!hits.length) return { answer: INSUFFICIENT, sources: [], answered: false };

  const sources = await buildSources(env, hits);
  const sourcesText = groundingText(sources);
  const messages = [
    {
      role: "system",
      content: `${SYSTEM}\n\n${BRIEF_INSTRUCTIONS}\n\nSOURCES:\n${sourceBlock(sources)}`,
    },
    { role: "user", content: request },
  ];

  const { answer, violations } = await generateChecked(env, messages, sourcesText, 1100);
  if (violations.length) {
    await logQuery(env, request, false, null, `output-guardrail:${violations.join("; ")}`);
    return outputBlocked(violations, noCache ? answer : undefined);
  }

  const cited = citedSources(answer, sources.length);
  const result: Result = {
    answer, answered: cited.length > 0, sources: toSources(sources, cited),
  };
  if (result.answered && key) await cacheSet(env, key, result);
  return result;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(req);

    try {
      const admin =
        !!env.ADMIN_TOKEN && req.headers.get("authorization") === `Bearer ${env.ADMIN_TOKEN}`;

      if (url.pathname === "/api/ingest" && req.method === "POST") {
        if (!admin) return json({ error: "unauthorized" }, 401);
        return json(await ingest(env));
      }

      if (url.pathname === "/api/health") {
        return json({ ok: true, promptVersion: PROMPT_VERSION, minScore: Number(env.MIN_SCORE) });
      }

      // Admin-only retrieval debug endpoint used by the retrieval benchmark (no LLM call).
      if (url.pathname === "/api/retrieve" && req.method === "POST") {
        if (!admin) return json({ error: "unauthorized" }, 401);
        const { question, topK } = (await req.json()) as { question?: string; topK?: number };
        if (!question?.trim()) return json({ error: "question required" }, 400);
        const hits = await retrieve(env, question, Math.min(topK ?? 6, 20));
        return json({ hits: hits.map((h) => ({ id: h.id, doc: h.doc, type: h.type, score: h.score })) });
      }

      const ip = req.headers.get("cf-connecting-ip") ?? "anon";
      // Admin evals bypass the rate limit and the answer cache so every run hits the full pipeline.
      if (!admin && (await rateLimited(env, ip))) return json({ error: "rate limited" }, 429);

      if (url.pathname === "/api/chat" && req.method === "POST") {
        const { question, sessionId } = (await req.json()) as {
          question?: string;
          sessionId?: string;
        };
        if (!question?.trim() || question.length > 1000)
          return json({ error: "question required (max 1000 chars)" }, 400);
        return json(await ask(env, question.trim(), sessionId || ip, admin && req.headers.get("x-no-cache") === "1"));
      }

      if (url.pathname === "/api/brief" && req.method === "POST") {
        const { product, audience, goal } = (await req.json()) as Record<string, string>;
        if (!product || !audience || !goal)
          return json({ error: "product, audience, goal required" }, 400);
        return json(await brief(env, product, audience, goal, admin && req.headers.get("x-no-cache") === "1"));
      }

      if (url.pathname === "/api/reset" && req.method === "POST") {
        const { sessionId } = (await req.json()) as { sessionId?: string };
        await env.SESSION.get(env.SESSION.idFromName(sessionId || ip)).clear();
        return json({ ok: true });
      }

      return json({ error: "not found" }, 404);
    } catch (err) {
      // AI Gateway Guardrails (Llama Guard) reject with error 2016 (prompt) or 2017 (response).
      const blocked = gatewayBlock(err);
      if (blocked) {
        return json(
          {
            answer: blocked === "prompt" ? BLOCKED_INPUT : BLOCKED_OUTPUT,
            answered: false,
            blocked: blocked === "prompt" ? "input" : "output",
            by: "ai-gateway-guardrails",
            sources: [],
          },
          422,
        );
      }
      if (aiQuotaExceeded(err)) {
        return json(
          { error: "ai_quota_exceeded", message: "Workers AI daily free allocation is used up. Retry after it resets (00:00 UTC) or use a Workers Paid plan." },
          503,
        );
      }
      console.error(err);
      return json({ error: "internal error" }, 500);
    }
  },
} satisfies ExportedHandler<Env>;
