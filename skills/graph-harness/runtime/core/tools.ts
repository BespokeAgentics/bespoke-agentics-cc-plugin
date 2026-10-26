// Reference ToolAdapter: local filesystem + sandboxed commands. Policy has already decided by
// the time execute() runs; the adapter still refuses to leave the workspace as defence in depth.

import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, isAbsolute, join, relative, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import type { ToolAdapter, ToolCall, ToolResult } from "./types.ts";

function inside(workspace: string, p: string): string {
  const abs = isAbsolute(p) ? p : resolve(workspace, p);
  const rel = relative(workspace, abs);
  if (rel.startsWith("..") || isAbsolute(rel)) throw new Error(`path ${p} is outside the workspace`);
  return abs;
}

export class LocalTools implements ToolAdapter {
  private deployLog: string | undefined;
  constructor(opts: { deployLog?: string } = {}) { this.deployLog = opts.deployLog; }

  has(tool: string): boolean { return ["read_file", "list_files", "write_file", "run_command", "delete_path", "deploy", "fetch"].includes(tool); }

  async execute(call: ToolCall, ctx: { workspace: string; run_id: string }): Promise<ToolResult> {
    const ws = resolve(ctx.workspace);
    try {
      switch (call.tool) {
        case "read_file": {
          const p = inside(ws, String(call.args.path));
          if (!existsSync(p)) return { ok: false, error: "not found" };
          return { ok: true, output: { content: readFileSync(p, "utf8") } };
        }
        case "list_files": {
          const p = inside(ws, String(call.args.dir ?? "."));
          const files: string[] = [];
          const walk = (d: string, depth: number) => {
            if (depth > 6) return;
            for (const e of readdirSync(d, { withFileTypes: true })) {
              if (e.name === "node_modules" || e.name === ".git") continue;
              const f = join(d, e.name);
              if (e.isDirectory()) walk(f, depth + 1); else files.push(relative(ws, f));
            }
          };
          walk(p, 0);
          return { ok: true, output: { files: files.slice(0, 500) } };
        }
        case "write_file": {
          const p = inside(ws, String(call.args.path));
          mkdirSync(dirname(p), { recursive: true });
          const content = String(call.args.content ?? "");
          writeFileSync(p, content);
          return { ok: true, output: { path: relative(ws, p), bytes: Buffer.byteLength(content) }, artifact: { path: relative(ws, p), kind: String(call.args.kind ?? "file") } };
        }
        case "run_command": {
          const cmd = String(call.args.cmd ?? "");
          const r = spawnSync("sh", ["-c", cmd], { cwd: ws, encoding: "utf8", timeout: Number(call.args.timeout_ms ?? 120000) });
          if (r.error) return { ok: false, error: r.error.message };
          return { ok: r.status === 0, output: { code: r.status, stdout: r.stdout.slice(-4000), stderr: r.stderr.slice(-4000) }, error: r.status === 0 ? undefined : `exit ${r.status}` };
        }
        case "delete_path": {
          const p = inside(ws, String(call.args.path));
          if (!existsSync(p)) return { ok: false, error: "not found" };
          const isDir = statSync(p).isDirectory();
          rmSync(p, { recursive: isDir, force: false });
          return { ok: true, output: { path: relative(ws, p) } };
        }
        case "deploy": {
          // Reference stub: records the deploy request. Wire your real deploy here.
          const line = `${new Date().toISOString()} run=${ctx.run_id} target=${call.args.target ?? "default"}\n`;
          if (this.deployLog) { mkdirSync(dirname(this.deployLog), { recursive: true }); writeFileSync(this.deployLog, line, { flag: "a" }); }
          return { ok: true, output: { target: call.args.target ?? "default", ref: "stub" } };
        }
        case "fetch": {
          const res = await fetch(String(call.args.url), { signal: AbortSignal.timeout(Number(call.args.timeout_ms ?? 15000)) });
          return { ok: res.ok, output: { status: res.status, body: (await res.text()).slice(0, 20000) }, error: res.ok ? undefined : `status ${res.status}` };
        }
      }
      return { ok: false, error: `unknown tool ${call.tool}` };
    } catch (e) {
      return { ok: false, error: (e as Error).message };
    }
  }
}
