export const INSUFFICIENT =
  "I don't have enough information in the knowledge base to answer that confidently.";
export const BLOCKED_INPUT =
  "I can't help with that request. Please ask a question about our products, brand, SOPs or research.";
export const BLOCKED_OUTPUT =
  "I drafted an answer but it failed our compliance check, so I'm not showing it. Please rephrase or ask the brand team.";

/** Returns the sorted, de-duplicated source numbers cited as [n] or [n, m] that actually exist. */
export function citedSources(answer: string, sourceCount: number): number[] {
  const found = new Set<number>();
  for (const group of answer.matchAll(/\[(\d+(?:\s*,\s*\d+)*)\]/g)) {
    for (const part of group[1].split(",")) {
      const n = Number(part);
      if (n >= 1 && n <= sourceCount) found.add(n);
    }
  }
  return [...found].sort((a, b) => a - b);
}

// ---------- Input guardrail (runs before embedding, retrieval and the LLM) ----------

const INJECTION: RegExp[] = [
  /ignore\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above|earlier)\s+(instructions|rules|prompts?)/i,
  /disregard\s+.{0,30}(rules|instructions|guidelines|compliance)/i,
  /(reveal|show|print|repeat|leak)\s+.{0,30}(system\s+prompt|hidden\s+instructions|your\s+instructions)/i,
  /\byou\s+are\s+now\b/i,
  /\b(developer|dan|jailbreak)\s+mode\b/i,
  /pretend\s+(that\s+)?(you\s+)?(have\s+)?no\s+(rules|restrictions|guidelines)/i,
  /(bypass|override|turn\s+off)\s+(the\s+)?(compliance|guardrails?|safety)/i,
  // Asking the model to dump its context: "copy the SOURCES block above verbatim".
  /(copy|paste|dump|print|output|echo|repeat|show)\s+(me\s+)?(the\s+|all\s+|your\s+)?(sources?|context|system|hidden|reference)\b.{0,40}(verbatim|word[\s-]for[\s-]word|above|exactly)/i,
  /\bverbatim\b.{0,40}\b(sources?|context|system\s+prompt|instructions)\b/i,
];

export function checkInput(question: string): { ok: true } | { ok: false; reason: string } {
  if (!question.trim()) return { ok: false, reason: "empty" };
  if (question.length > 1000) return { ok: false, reason: "too-long" };
  // eslint-disable-next-line no-control-regex
  if (/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/.test(question))
    return { ok: false, reason: "control-characters" };
  if (INJECTION.some((re) => re.test(question)))
    return { ok: false, reason: "prompt-injection" };
  return { ok: true };
}

// ---------- Output guardrail (runs on the generated answer before it is returned) ----------

/** Banned terms from the brand guidelines. */
const BANNED = [
  "flawless", "miracle", "anti-aging", "cure", "cures", "heal", "heals",
  "perfect skin", "guaranteed results",
];

// A sentence that negates or quotes the term ("never say", "avoid", "cannot") is not a violation.
const NEGATION = /\b(no|not|never|cannot|can't|don't|do not|avoid|without|ban(?:ned)?|forbidden)\b/i;

export function bannedTerms(text: string): string[] {
  const hits = new Set<string>();
  for (const sentence of text.split(/(?<=[.!?\n])\s+/)) {
    if (NEGATION.test(sentence)) continue;
    const lower = sentence.toLowerCase();
    for (const t of BANNED) if (new RegExp(String.raw`\b${t}\b`).test(lower)) hits.add(t);
  }
  return [...hits];
}

/**
 * Numbers, prices and percentages in the answer that do not appear in the sources.
 * Single bare digits are ignored (list numbering, "3 steps"); "$5" and "5%" are checked.
 */
export function ungroundedNumbers(answer: string, sourcesText: string): string[] {
  const cleaned = answer
    .replace(/\[\d+(?:\s*,\s*\d+)*\]/g, " ")
    .replace(/^\s*\d+[.)]\s+/gm, " ");
  const haystack = sourcesText.replace(/(\d),(\d)/g, "$1$2");
  const bad = new Set<string>();
  for (const raw of cleaned.match(/[$]?\d[\d,]*(?:\.\d+)?%?/g) ?? []) {
    const bare = raw.replace(/[$,%]/g, "");
    if (/^\d$/.test(bare) && !/[$%]/.test(raw)) continue;
    const esc = bare.replace(/\./g, String.raw`\.`);
    if (!new RegExp(String.raw`(?<![\d.])${esc}(?!\d)`).test(haystack)) bad.add(raw);
  }
  return [...bad];
}

/** Raw source markers or system-prompt text in an answer mean the model dumped its context. */
export function leaksPrompt(text: string): boolean {
  return /SOURCES:|\((?:PRODUCT|BRAND|COMPLIANCE|SOP|RESEARCH|LEARNINGS|GENERAL)\)|You are Company Brain|Rules:\s*1\./.test(text);
}

export function outputViolations(answer: string, sourcesText: string): string[] {
  return [
    ...(leaksPrompt(answer) ? ["reveals system prompt or raw sources"] : []),
    ...bannedTerms(answer).map((t) => `banned term "${t}"`),
    ...ungroundedNumbers(answer, sourcesText).map((n) => `number "${n}" not in sources`),
  ];
}

// ---------- AI Gateway Guardrails (Llama Guard) block codes ----------

export function gatewayBlock(err: unknown): "prompt" | "response" | null {
  const msg = err instanceof Error ? err.message : String(err);
  if (/\b2016\b/.test(msg)) return "prompt";
  if (/\b2017\b/.test(msg)) return "response";
  return null;
}

// ---------- Workers AI quota ----------

/** Workers AI error 4006: the daily free allocation of neurons is used up. */
export function aiQuotaExceeded(err: unknown): boolean {
  const msg = err instanceof Error ? err.message : String(err);
  return /\b4006\b|daily free allocation/i.test(msg);
}
