// Graph loading and the mechanical checks that make a graph a reviewable artifact.
// validateGraph fails on: schema violations, unreachable nodes, dead ends, missing outcome edges,
// loops without a retry cap, risky nodes without a gate in front, act/verify nodes with no sensor,
// undeclared sensors or tools, and node tiers below the tools they grant.

import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { parseYaml } from "./yaml.ts";
import { validate } from "./schema.ts";
import { OUTCOMES, TIER_ORDER, type Graph, type NodeDef, type Policy, type Tier } from "./types.ts";

// In the skill: runtime/core/../../templates. Vendored into a project: harness/runtime/core/../../schemas.
export const TEMPLATES_DIR = [join(import.meta.dirname, "..", "..", "templates"), join(import.meta.dirname, "..", "..", "schemas")].find((p) => existsSync(join(p, "graph.schema.json")))
  ?? join(import.meta.dirname, "..", "..", "templates");
export const BUILTIN_SENSORS = new Set(["contract_complete"]);
export const GATE_TYPES = new Set(["policy_gate", "human_review"]);

export interface GraphIssue { code: string; node?: string; message: string }
export interface GraphReport { ok: boolean; graph: string; errors: GraphIssue[]; warnings: GraphIssue[]; stats: { nodes: number; edges: number; cycles: number; sensors: number } }

export function loadSchema(name: string): any {
  return JSON.parse(readFileSync(join(TEMPLATES_DIR, name), "utf8"));
}

export function loadStructured(path: string): unknown {
  const text = readFileSync(path, "utf8");
  return path.endsWith(".json") ? JSON.parse(text) : parseYaml(text);
}

export function loadGraph(path: string): Graph { return loadStructured(path) as Graph; }
export function loadPolicy(path: string): Policy { return loadStructured(path) as Policy; }

export function isTerminal(n: NodeDef): boolean { return n.terminal === true || n.type === "receipt"; }

function tierIndex(t: Tier | undefined): number { return t ? TIER_ORDER.indexOf(t) : 0; }

export function isRisky(name: string, node: NodeDef, policy?: Policy): boolean {
  if (node.risk === "irreversible") return true;
  if (node.tier === "approve") return true;
  if (policy) for (const t of node.tools ?? []) if (policy.tools[t]?.tier === "approve") return true;
  return false;
}

/** Enumerate elementary cycles (graphs are small; Johnson's algorithm is overkill). */
export function findCycles(adj: Record<string, string[]>): string[][] {
  const cycles: string[][] = [];
  const seen = new Set<string>();
  const nodes = Object.keys(adj).sort();
  for (const start of nodes) {
    const stack: string[] = [];
    const onStack = new Set<string>();
    const dfs = (n: string) => {
      stack.push(n); onStack.add(n);
      for (const m of adj[n] ?? []) {
        if (m === start) {
          const cyc = [...stack];
          const sig = [...cyc].sort().join(">");
          if (!seen.has(sig)) { seen.add(sig); cycles.push(cyc); }
        } else if (!onStack.has(m) && m > start) {
          dfs(m);
        }
      }
      stack.pop(); onStack.delete(n);
    };
    dfs(start);
  }
  return cycles;
}

export function validateGraph(graph: unknown, policy?: Policy, graphName = "graph"): GraphReport {
  const errors: GraphIssue[] = [];
  const warnings: GraphIssue[] = [];
  const stats = { nodes: 0, edges: 0, cycles: 0, sensors: 0 };
  const report = (): GraphReport => ({ ok: errors.length === 0, graph: graphName, errors, warnings, stats });

  for (const e of validate(loadSchema("graph.schema.json"), graph)) errors.push({ code: "SCHEMA", message: `${e.path}: ${e.message}` });
  if (errors.length) return report();

  const g = graph as Graph;
  const names = Object.keys(g.nodes);
  stats.nodes = names.length;
  stats.sensors = Object.keys(g.sensors ?? {}).length;
  const adj: Record<string, string[]> = {};

  if (!(g.entry in g.nodes)) errors.push({ code: "ENTRY_MISSING", message: `entry node "${g.entry}" does not exist` });

  for (const [name, node] of Object.entries(g.nodes)) {
    const targets = new Set<string>();
    for (const [outcome, to] of Object.entries(node.edges ?? {})) {
      stats.edges++;
      if (!(to in g.nodes)) errors.push({ code: "EDGE_TARGET", node: name, message: `edge ${outcome} -> "${to}" points at a node that does not exist` });
      else targets.add(to);
      const known = [...OUTCOMES[node.type].required, ...OUTCOMES[node.type].optional, "*"];
      if (!known.includes(outcome)) errors.push({ code: "OUTCOME_UNKNOWN", node: name, message: `"${outcome}" is not an outcome a ${node.type} node can produce (${known.join(", ")})` });
    }
    if (node.retry) {
      if (!(node.retry.on_exhausted in g.nodes)) errors.push({ code: "EDGE_TARGET", node: name, message: `retry.on_exhausted -> "${node.retry.on_exhausted}" does not exist` });
      else targets.add(node.retry.on_exhausted);
    }
    adj[name] = [...targets];

    if (!isTerminal(node)) {
      if (targets.size === 0) errors.push({ code: "DEAD_END", node: name, message: `non-terminal ${node.type} node has no edges` });
      const hasWildcard = "*" in (node.edges ?? {});
      for (const outcome of OUTCOMES[node.type].required) {
        if (!hasWildcard && !(outcome in (node.edges ?? {}))) errors.push({ code: "OUTCOME_UNCOVERED", node: name, message: `no edge for outcome "${outcome}" (a ${node.type} node can produce it; add edges.${outcome} or edges."*")` });
      }
    } else if (Object.keys(node.edges ?? {}).length) {
      warnings.push({ code: "TERMINAL_EDGES", node: name, message: "terminal node declares edges that will never be taken" });
    }

    if (node.type === "repair" && !node.retry) errors.push({ code: "REPAIR_NO_RETRY", node: name, message: "repair node has no retry: { max, on_exhausted } — the loop belongs to the harness, not the model" });
    if (node.type === "verify" && !(node.sensors?.length)) errors.push({ code: "VERIFY_NO_SENSOR", node: name, message: "verify node declares no sensors; it would pass on the model's word" });
    if (node.type === "act") {
      const okTarget = node.edges?.ok ?? node.edges?.["*"];
      const followedByVerify = okTarget !== undefined && g.nodes[okTarget]?.type === "verify";
      if (!(node.sensors?.length) && !followedByVerify) errors.push({ code: "UNSENSED_ACT", node: name, message: "act node has no sensor on its output and its ok edge does not lead to a verify node" });
    }
    for (const s of node.sensors ?? []) {
      if (!BUILTIN_SENSORS.has(s) && !(g.sensors && s in g.sensors)) errors.push({ code: "SENSOR_UNDECLARED", node: name, message: `sensor "${s}" is not declared under sensors:` });
    }
    if (policy) {
      for (const t of node.tools ?? []) {
        const def = policy.tools[t];
        if (!def) { errors.push({ code: "TOOL_UNDECLARED", node: name, message: `tool "${t}" has no contract in policy.yaml (purpose, tier, output, failure, boundary)` }); continue; }
        if (tierIndex(def.tier) > tierIndex(node.tier)) errors.push({ code: "TIER_MISMATCH", node: name, message: `tool "${t}" is tier ${def.tier} but the node is tier ${node.tier ?? "read"}` });
      }
    } else if (node.tools?.length) {
      warnings.push({ code: "NO_POLICY", node: name, message: "tools declared but no policy supplied; tool contracts and tiers were not checked" });
    }
    if (node.tools?.length && node.type !== "act" && node.type !== "load_context" && node.type !== "repair") {
      warnings.push({ code: "TOOLS_ON_NON_ACT", node: name, message: `${node.type} nodes do not execute tools; the list is ignored` });
    }
  }

  // Reachability and terminal
  const reach = new Set<string>();
  const queue = g.entry in g.nodes ? [g.entry] : [];
  while (queue.length) { const n = queue.shift()!; if (reach.has(n)) continue; reach.add(n); queue.push(...(adj[n] ?? [])); }
  for (const n of names) if (!reach.has(n)) errors.push({ code: "UNREACHABLE", node: n, message: "node is not reachable from the entry node" });
  if (!names.some((n) => reach.has(n) && isTerminal(g.nodes[n]))) errors.push({ code: "NO_TERMINAL", message: "no terminal (receipt) node is reachable; every run would end on the budget" });

  // Loops need a cap: a retry budget, or a human in the loop (human_review bounds a cycle by a decision).
  const cycles = findCycles(adj);
  stats.cycles = cycles.length;
  for (const cyc of cycles) {
    if (!cyc.some((n) => g.nodes[n].retry || g.nodes[n].type === "human_review")) errors.push({ code: "UNCAPPED_LOOP", message: `cycle ${cyc.join(" -> ")} -> ${cyc[0]} has no node with retry.max and no human_review; it would spin until max_steps` });
  }

  // Risky nodes need a gate directly in front
  for (const [name, node] of Object.entries(g.nodes)) {
    if (!isRisky(name, node, policy)) continue;
    const incoming = names.filter((m) => (adj[m] ?? []).includes(name));
    for (const from of incoming) {
      if (!GATE_TYPES.has(g.nodes[from].type)) errors.push({ code: "UNGATED_RISK", node: name, message: `risky node is entered from "${from}" (${g.nodes[from].type}); only policy_gate or human_review may lead into it` });
    }
    if (incoming.length === 0 && name !== g.entry) { /* already UNREACHABLE */ }
    if (name === g.entry) errors.push({ code: "UNGATED_RISK", node: name, message: "risky node cannot be the entry node" });
  }

  return report();
}

export function resolveRelative(base: string, p: string): string {
  return p.startsWith("/") ? p : join(dirname(base), p);
}
