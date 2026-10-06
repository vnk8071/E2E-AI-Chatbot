import { DurableObject } from "cloudflare:workers";

export interface Turn {
  role: "user" | "assistant";
  content: string;
}

const MAX_TURNS = 8;

/** One Durable Object per chat session: keeps the last few turns for multi-turn context. */
export class ChatSession extends DurableObject {
  async history(): Promise<Turn[]> {
    return (await this.ctx.storage.get<Turn[]>("turns")) ?? [];
  }

  async append(...turns: Turn[]): Promise<void> {
    const all = [...(await this.history()), ...turns].slice(-MAX_TURNS);
    await this.ctx.storage.put("turns", all);
  }

  async clear(): Promise<void> {
    await this.ctx.storage.delete("turns");
  }
}
