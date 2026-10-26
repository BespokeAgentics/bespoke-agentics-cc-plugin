// Sensors: evidence producers. A sensor returns pass/fail plus evidence; the harness turns that
// into an edge. Kinds: command | file_exists | file_contains | json_schema | contract_complete | custom.
// A sensor with `todo` set reports pass=false (unless allow_todo) so an unimplemented check is never
// silently green.

import { existsSync, readFileSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { spawnSync } from "node:child_process";
import { validateContract } from "./contract.ts";
import { validate } from "./schema.ts";
import type { Sensor, SensorContext, SensorDef, SensorResult } from "./types.ts";

function interpolate(s: string, ctx: SensorContext): string {
  return s.replace(/\{([\w.]+)\}/g, (_, key: string) => {
    const parts = key.split(".");
    let cur: any = { contract: ctx.contract, workspace: ctx.workspace, artifacts: ctx.artifacts };
    for (const p of parts) cur = cur?.[p];
    return cur === undefined || cur === null ? "" : String(cur);
  });
}

function abs(ctx: SensorContext, p: string): string { return isAbsolute(p) ? p : resolve(ctx.workspace, p); }

export function buildSensor(name: string, def: SensorDef, baseDir: string): Sensor {
  return {
    name,
    async run(ctx: SensorContext): Promise<SensorResult> {
      if (ctx.injectFailure?.(name, ctx.attempt)) return { name, pass: false, summary: `injected failure (attempt ${ctx.attempt})`, evidence: { injected: true } };
      if (def.todo && !def.allow_todo) return { name, pass: false, summary: `TODO: ${def.todo} (no mechanical check yet; set allow_todo: true to let runs pass on this sensor)`, evidence: { todo: def.todo } };
      if (def.todo && def.allow_todo) return { name, pass: true, summary: `TODO (allowed): ${def.todo}`, evidence: { todo: def.todo, allowed: true } };
      try {
        switch (def.kind) {
          case "contract_complete": {
            const r = validateContract(ctx.contract);
            return { name, pass: r.ok, summary: r.ok ? "contract is complete and every done_when is verifiable" : r.errors.map((e) => `${e.path}: ${e.message}`).join("; "), evidence: { errors: r.errors } };
          }
          case "file_exists": {
            const p = interpolate(def.path ?? "", ctx);
            if (!p) return { name, pass: false, summary: "no path to check (contract.output.path is empty?)" };
            const ok = existsSync(abs(ctx, p));
            return { name, pass: ok, summary: ok ? `${p} exists` : `${p} does not exist`, evidence: { path: p } };
          }
          case "file_contains": {
            const p = interpolate(def.path ?? "", ctx);
            if (!existsSync(abs(ctx, p))) return { name, pass: false, summary: `${p} does not exist`, evidence: { path: p } };
            const ok = new RegExp(def.pattern ?? "").test(readFileSync(abs(ctx, p), "utf8"));
            return { name, pass: ok, summary: ok ? `${p} matches /${def.pattern}/` : `${p} does not match /${def.pattern}/`, evidence: { path: p, pattern: def.pattern } };
          }
          case "json_schema": {
            const p = interpolate(def.path ?? "", ctx);
            const schemaPath = isAbsolute(def.schema ?? "") ? def.schema! : resolve(baseDir, def.schema ?? "");
            if (!existsSync(abs(ctx, p))) return { name, pass: false, summary: `${p} does not exist` };
            const errs = validate(JSON.parse(readFileSync(schemaPath, "utf8")), JSON.parse(readFileSync(abs(ctx, p), "utf8")));
            return { name, pass: errs.length === 0, summary: errs.length ? errs.map((e) => `${e.path}: ${e.message}`).join("; ") : `${p} matches ${def.schema}`, evidence: { errors: errs } };
          }
          case "command": {
            const cmd = interpolate(def.cmd ?? "", ctx);
            const r = spawnSync("sh", ["-c", cmd], { cwd: ctx.workspace, encoding: "utf8", timeout: def.timeout_ms ?? 120000 });
            if (r.error) return { name, pass: false, error: true, summary: `${cmd}: ${r.error.message}`, evidence: { cmd } };
            return { name, pass: r.status === 0, summary: r.status === 0 ? `${cmd} exited 0` : `${cmd} exited ${r.status}: ${(r.stderr || r.stdout).trim().slice(-400)}`, evidence: { cmd, code: r.status, stdout: r.stdout.slice(-2000), stderr: r.stderr.slice(-2000) } };
          }
          case "custom": {
            const modPath = isAbsolute(def.module ?? "") ? def.module! : resolve(baseDir, def.module ?? "");
            const mod = await import(pathToFileURL(modPath).href);
            const r = await mod.run(ctx, def);
            return { name, pass: !!r.pass, summary: String(r.summary ?? ""), evidence: r.evidence };
          }
        }
        return { name, pass: false, error: true, summary: `unknown sensor kind ${(def as any).kind}` };
      } catch (e) {
        return { name, pass: false, error: true, summary: `sensor error: ${(e as Error).message}` };
      }
    },
  };
}

export function buildSensors(defs: Record<string, SensorDef> | undefined, baseDir: string): Map<string, Sensor> {
  const m = new Map<string, Sensor>();
  m.set("contract_complete", buildSensor("contract_complete", { kind: "contract_complete" }, baseDir));
  for (const [name, def] of Object.entries(defs ?? {})) m.set(name, buildSensor(name, def, baseDir));
  return m;
}
