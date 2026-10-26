// ModelAdapters. The harness never depends on a vendor SDK:
//   StubModel    deterministic; used by the smoke test and by `run --model stub`.
//   CommandModel shells out to any CLI that reads a JSON ModelInput on stdin and prints a JSON
//                ModelOutput on stdout (e.g. a wrapper around `claude -p`). See references/graph-spec.md.

import { spawnSync } from "node:child_process";
import type { ModelAdapter, ModelInput, ModelOutput, ToolCall } from "./types.ts";

export class StubModel implements ModelAdapter {
  private extraCalls: ToolCall[];
  constructor(opts: { extraCalls?: ToolCall[] } = {}) { this.extraCalls = opts.extraCalls ?? []; }
  route(): string { return "stub"; }

  async propose(input: ModelInput): Promise<ModelOutput> {
    const usage = { input_tokens: 0, output_tokens: 0, usd: 0 };
    const out = input.contract?.output.path ?? "harness-output.txt";
    switch (input.node_type) {
      case "plan":
        return { plan: [`write ${out} satisfying: ${input.contract?.goal ?? "goal"}`, "run sensors"], usage };
      case "act": {
        const content = [
          `# ${input.contract?.goal ?? "output"}`,
          `attempt: ${input.attempt}`,
          ...(input.last_failures.length ? ["repaired after:", ...input.last_failures.map((f) => `- ${f}`)] : []),
          "",
        ].join("\n");
        return { calls: [{ tool: "write_file", args: { path: out, content, kind: input.contract?.output.kind ?? "file" } }, ...this.extraCalls], usage };
      }
      case "repair":
        return { notes: `rewrite ${out}; failures: ${input.last_failures.join("; ") || "none reported"}`, usage };
      default:
        return { usage };
    }
  }
}

export class CommandModel implements ModelAdapter {
  private cmd: string;
  constructor(cmd: string) { this.cmd = cmd; }
  route(): string { return `command:${this.cmd}`; }

  async propose(input: ModelInput): Promise<ModelOutput> {
    const r = spawnSync("sh", ["-c", this.cmd], { input: JSON.stringify(input), encoding: "utf8", timeout: 600000, maxBuffer: 50 * 1024 * 1024 });
    if (r.error) throw new Error(`model command failed: ${r.error.message}`);
    if (r.status !== 0) throw new Error(`model command exited ${r.status}: ${r.stderr.slice(-2000)}`);
    const text = r.stdout.trim();
    const start = text.indexOf("{");
    if (start < 0) throw new Error("model command printed no JSON object");
    const parsed = JSON.parse(text.slice(start));
    return { plan: parsed.plan, calls: parsed.calls, notes: parsed.notes, usage: parsed.usage };
  }
}

export function makeModel(spec: string, opts: { extraCalls?: ToolCall[] } = {}): ModelAdapter {
  if (spec === "stub") return new StubModel(opts);
  if (spec.startsWith("command:")) return new CommandModel(spec.slice("command:".length));
  throw new Error(`unknown model adapter "${spec}" (use stub or command:<shell command>)`);
}
