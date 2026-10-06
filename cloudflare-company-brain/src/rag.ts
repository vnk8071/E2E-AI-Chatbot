import type { Chunk } from "./chunk";
import { chunkMarkdown } from "./chunk";
import type { ChatSession } from "./session";

export interface Env {
  AI: Ai;
  ASSETS: Fetcher;
  VECTORS: VectorizeIndex;
  DOCS: R2Bucket;
  DB: D1Database;
  CACHE: KVNamespace;
  SESSION: DurableObjectNamespace<ChatSession>;
  ADMIN_TOKEN: string;
  GATEWAY_ID: string;
  CHAT_MODEL: string;
  EMBED_MODEL: string;
  MIN_SCORE: string;
  RATE_LIMIT_PER_MIN: string;
  CACHE_TTL_SECONDS: string;
}

export interface Hit extends Chunk {
  score: number;
}

// AI calls go through AI Gateway (caching, rate limits, logs) when GATEWAY_ID is set; empty = direct.
const gw = (env: Env) => (env.GATEWAY_ID ? { gateway: { id: env.GATEWAY_ID } } : {});

export async function embed(env: Env, texts: string[]): Promise<number[][]> {
  const out: number[][] = [];
  for (let i = 0; i < texts.length; i += 50) {
    const res = (await env.AI.run(
      env.EMBED_MODEL as any,
      { text: texts.slice(i, i + 50) },
      gw(env),
    )) as unknown as { data: number[][] };
    out.push(...res.data);
  }
  return out;
}

export async function chat(
  env: Env,
  messages: { role: string; content: string }[],
  maxTokens = 700,
): Promise<string> {
  const res = (await env.AI.run(
    env.CHAT_MODEL as any,
    { messages, temperature: 0.2, max_tokens: maxTokens },
    gw(env),
  )) as { response?: string };
  return (res.response ?? "").trim();
}

/** R2 -> chunks -> embeddings -> Vectorize (vectors) + D1 (text and metadata). */
export async function ingest(env: Env): Promise<{ docs: number; chunks: number }> {
  const listing = await env.DOCS.list();
  const chunks: Chunk[] = [];
  for (const obj of listing.objects.filter((o) => o.key.endsWith(".md"))) {
    const body = await (await env.DOCS.get(obj.key))!.text();
    chunks.push(...chunkMarkdown(obj.key, body));
  }
  if (!chunks.length) return { docs: 0, chunks: 0 };

  const vectors = await embed(env, chunks.map((c) => c.text));
  await env.VECTORS.upsert(
    chunks.map((c, i) => ({
      id: c.id,
      values: vectors[i],
      metadata: { doc: c.doc, type: c.type },
    })),
  );
  await env.DB.batch([
    env.DB.prepare("DELETE FROM chunks"),
    ...chunks.map((c) =>
      env.DB.prepare(
        "INSERT INTO chunks (id, doc, type, title, text) VALUES (?, ?, ?, ?, ?)",
      ).bind(c.id, c.doc, c.type, c.title, c.text),
    ),
  ]);
  // Bump the knowledge-base version so cached answers from the old docs are never served.
  await env.CACHE.put("kb:version", String(Date.now()));
  return { docs: listing.objects.length, chunks: chunks.length };
}

export async function retrieve(env: Env, query: string, topK = 6): Promise<Hit[]> {
  const [qv] = await embed(env, [query]);
  const res = await env.VECTORS.query(qv, { topK });
  if (!res.matches.length) return [];
  const ids = res.matches.map((m) => m.id);
  const rows = await env.DB.prepare(
    `SELECT * FROM chunks WHERE id IN (${ids.map(() => "?").join(",")})`,
  )
    .bind(...ids)
    .all<Chunk>();
  const byId = new Map(rows.results.map((r) => [r.id, r]));
  return res.matches
    .filter((m) => byId.has(m.id))
    .map((m) => ({ ...byId.get(m.id)!, score: m.score }));
}

/** Compliance and brand rules are always injected, regardless of retrieval score. */
export async function mandatoryRules(env: Env): Promise<Chunk[]> {
  const rows = await env.DB.prepare(
    "SELECT * FROM chunks WHERE type IN ('compliance','brand') ORDER BY id",
  ).all<Chunk>();
  return rows.results;
}

export async function rateLimited(env: Env, key: string): Promise<boolean> {
  const limit = Number(env.RATE_LIMIT_PER_MIN);
  const bucket = `rl:${key}:${Math.floor(Date.now() / 60000)}`;
  const n = Number((await env.CACHE.get(bucket)) ?? 0);
  if (n >= limit) return true;
  await env.CACHE.put(bucket, String(n + 1), { expirationTtl: 120 });
  return false;
}

export async function logQuery(
  env: Env,
  question: string,
  answered: boolean,
  topScore: number | null,
  reason: string,
) {
  await env.DB.prepare(
    "INSERT INTO query_log (question, answered, top_score, reason) VALUES (?, ?, ?, ?)",
  )
    .bind(question.slice(0, 500), answered ? 1 : 0, topScore, reason)
    .run();
}

// ---------- Answer cache (KV) ----------

async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** Same question => same key: case, spacing and trailing punctuation are ignored. */
export const normalize = (q: string) =>
  q.toLowerCase().replace(/\s+/g, " ").replace(/[?!.\s]+$/, "").trim();

export async function cacheKey(env: Env, kind: string, text: string): Promise<string> {
  const version = (await env.CACHE.get("kb:version")) ?? "0";
  return `${kind}:${version}:${await sha256(normalize(text))}`;
}

export async function cacheGet<T>(env: Env, key: string): Promise<T | null> {
  return env.CACHE.get<T>(key, "json");
}

export async function cacheSet(env: Env, key: string, value: unknown) {
  await env.CACHE.put(key, JSON.stringify(value), {
    expirationTtl: Math.max(60, Number(env.CACHE_TTL_SECONDS) || 3600),
  });
}
