export interface Chunk {
  id: string;
  doc: string;
  type: string;
  title: string;
  text: string;
}

/** Parses `---\ntype: x\n---` frontmatter; returns the type and the remaining body. */
export function parseDoc(raw: string): { type: string; body: string } {
  const m = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!m) return { type: "general", body: raw };
  const type = m[1].match(/^type:\s*(.+)$/m)?.[1].trim() ?? "general";
  return { type, body: raw.slice(m[0].length) };
}

/** Splits a markdown doc into one chunk per "## " section, titled with the doc title. */
export function chunkMarkdown(doc: string, raw: string): Chunk[] {
  const { type, body } = parseDoc(raw);
  const docTitle = body.match(/^#\s+(.+)$/m)?.[1].trim() ?? doc;
  const sections = body.split(/^##\s+/m).slice(1);
  return sections
    .map((s, i) => {
      const [heading, ...rest] = s.split("\n");
      const text = rest.join("\n").trim();
      return {
        id: `${doc.replace(/\.md$/, "")}#${i}`,
        doc,
        type,
        title: `${docTitle} › ${heading.trim()}`,
        text: `${heading.trim()}\n${text}`,
      };
    })
    .filter((c) => c.text.length > 20);
}
