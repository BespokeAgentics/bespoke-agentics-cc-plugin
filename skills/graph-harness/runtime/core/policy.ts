// PolicyEngine over policy.yaml. The model never sees this; it only sees the decision in the trace.
// MODEL SUGGESTS -> POLICY CHECKS -> TOOL EXECUTES.

import { existsSync, readFileSync } from "node:fs";
import { isAbsolute, relative, resolve, sep } from "node:path";
import { loadSchema } from "./graph.ts";
import { validate } from "./schema.ts";
import type { Approval, Policy, PolicyDecision, PolicyEngine, Tier } from "./types.ts";

const PATH_ARGS = ["path", "file", "dir", "target_path", "dest", "src"];

export function validatePolicy(policy: unknown): { ok: boolean; errors: { path: string; message: string }[] } {
  const errors = validate(loadSchema("policy.schema.json"), policy);
  return { ok: errors.length === 0, errors };
}

export class FilePolicyEngine implements PolicyEngine {
  private policy: Policy;
  private workspace: string;
  private approvalsPath: string | undefined;

  constructor(policy: Policy, workspace: string, approvalsPath?: string) {
    const v = validatePolicy(policy);
    if (!v.ok) throw new Error("policy.yaml is invalid:\n" + v.errors.map((e) => `  ${e.path}: ${e.message}`).join("\n"));
    this.policy = policy;
    this.workspace = resolve(workspace);
    this.approvalsPath = approvalsPath ?? (policy.approvals_file ? resolve(workspace, policy.approvals_file) : undefined);
  }

  version(): string { return this.policy.version; }
  toolTier(tool: string): Tier | undefined { return this.policy.tools[tool]?.tier; }

  approvals(): Approval[] {
    if (!this.approvalsPath || !existsSync(this.approvalsPath)) return [];
    try { const v = JSON.parse(readFileSync(this.approvalsPath, "utf8")); return Array.isArray(v) ? v : []; }
    catch { return []; }
  }

  private insideWorkspace(p: string): { inside: boolean; denied?: string } {
    const abs = isAbsolute(p) ? p : resolve(this.workspace, p);
    const rel = relative(this.workspace, abs);
    if (rel.startsWith("..") || isAbsolute(rel)) return { inside: false };
    for (const d of this.policy.deny_paths ?? []) {
      const dn = d.replace(/\/+$/, "");
      if (rel === dn || rel.startsWith(dn + sep)) return { inside: true, denied: d };
    }
    return { inside: true };
  }

  decide(req: { tool: string; args: Record<string, unknown>; node: string; run_id: string }): PolicyDecision {
    const def = this.policy.tools[req.tool];
    if (!def) return { decision: "deny", rule: "tool.unknown", reason: `tool "${req.tool}" has no contract in policy.yaml`, tier: "approve" };
    const tier = def.tier;
    const rule = this.policy.tiers[tier];
    const base = { tier, rule: `${tier}:${rule}` };

    // Path boundary applies to every tier that takes a path (a read outside the workspace is still a leak).
    for (const k of PATH_ARGS) {
      const v = req.args[k];
      if (typeof v !== "string") continue;
      const r = this.insideWorkspace(v);
      if (!r.inside) return { ...base, decision: "deny", reason: `${k}="${v}" is outside the workspace ${this.workspace}` };
      if (r.denied && tier !== "read") return { ...base, decision: "deny", reason: `${k}="${v}" is under deny_paths entry "${r.denied}"` };
    }

    switch (rule) {
      case "allow": return { ...base, decision: "allow", reason: "tier allows" };
      case "deny": return { ...base, decision: "deny", reason: "tier is denied by policy" };
      case "allow_in_workspace": return { ...base, decision: "allow", reason: "all paths inside workspace" };
      case "allow_listed": {
        if (tier === "sandbox") {
          const cmd = String(req.args.cmd ?? "");
          const hit = (this.policy.sandbox_allow ?? []).find((p) => cmd === p || cmd.startsWith(p + " "));
          return hit ? { ...base, decision: "allow", reason: `command prefix "${hit}" is listed` } : { ...base, decision: "deny", reason: `command "${cmd}" is not in sandbox_allow` };
        }
        if (tier === "network") {
          let host = "";
          try { host = new URL(String(req.args.url ?? "")).host; } catch { return { ...base, decision: "deny", reason: "url is not parseable" }; }
          const hit = (this.policy.network_allow ?? []).find((h) => host === h || host.endsWith("." + h));
          return hit ? { ...base, decision: "allow", reason: `host "${host}" is listed` } : { ...base, decision: "deny", reason: `host "${host}" is not in network_allow` };
        }
        return { ...base, decision: "deny", reason: `allow_listed has no list for tier ${tier}` };
      }
      case "require_approval": {
        const a = this.approvals().find((x) => (x.tool === req.tool || x.tool === "*") && (!x.run_id || x.run_id === req.run_id));
        if (a) return { ...base, decision: "allow", rule: `approval:${a.granted_by}`, reason: `approved by ${a.granted_by} at ${a.ts}${a.note ? ` (${a.note})` : ""}` };
        return { ...base, decision: "needs_approval", reason: `tier ${tier} requires an approval record in ${this.approvalsPath ?? "approvals_file (unset)"}` };
      }
    }
    return { ...base, decision: "deny", reason: `unknown tier rule ${rule}` };
  }
}
