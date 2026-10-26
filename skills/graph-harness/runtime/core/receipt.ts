// Change receipt: a compact JSON summary of one run, derived from the event log alone.

import type { Graph, HarnessEvent, RunState } from "./types.ts";

export interface Receipt {
  run_id: string; contract_id: string; graph: string; policy_version: string; model_route: string;
  outcome: "completed" | "failed" | "paused" | "running";
  context_sources: string[];
  tools_used: { name: string; calls: number; denied: number; needs_approval: number }[];
  sensors: { name: string; runs: number; passed: number; last: "pass" | "fail" | "error" }[];
  test_results: { ran: number; passed: number; summary: string };
  human_corrections: { seq: number; decision: string; note?: string }[];
  retries: { total: number; by_node: Record<string, number>; exhausted: boolean };
  cost: { input_tokens: number; output_tokens: number; usd: number; model_calls: number };
  accepted_artifact: { path: string; kind?: string } | null;
  rollback_point: Record<string, unknown> | null;
  started_at: string; finished_at: string | null; events: number;
}

export function buildReceipt(events: HarnessEvent[], state: RunState, graph?: Graph): Receipt {
  const first = events[0];
  const tools = new Map<string, { calls: number; denied: number; needs_approval: number }>();
  const sensors = new Map<string, { runs: number; passed: number; last: "pass" | "fail" | "error" }>();
  const byNode: Record<string, number> = {};
  const sources = new Set<string>();
  let exhausted = false;
  for (const e of events) {
    if (e.type === "tool.requested") { const t = tools.get(String(e.data.tool)) ?? { calls: 0, denied: 0, needs_approval: 0 }; t.calls++; tools.set(String(e.data.tool), t); }
    if (e.type === "policy.decided" && e.data.tool !== "release") {
      const t = tools.get(String(e.data.tool)) ?? { calls: 0, denied: 0, needs_approval: 0 };
      if (e.data.decision === "deny") t.denied++;
      if (e.data.decision === "needs_approval") t.needs_approval++;
      tools.set(String(e.data.tool), t);
    }
    if (e.type === "sensor.ran") {
      const s = sensors.get(String(e.data.name)) ?? { runs: 0, passed: 0, last: "fail" as const };
      s.runs++; if (e.data.pass) s.passed++;
      s.last = e.data.error ? "error" : e.data.pass ? "pass" : "fail";
      sensors.set(String(e.data.name), s);
    }
    if (e.type === "retry.scheduled") byNode[e.node!] = (byNode[e.node!] ?? 0) + 1;
    if (e.type === "retry.exhausted") exhausted = true;
    if (e.type === "context.loaded") for (const s of (e.data.sources as string[]) ?? []) sources.add(s);
  }
  const testSensors = [...sensors.entries()].filter(([n, s]) => /test/i.test(n) || (graph?.sensors?.[n]?.kind === "command"));
  const last = events.at(-1);
  const finished = state.status === "completed" || state.status === "failed" ? last?.ts ?? null : null;
  return {
    run_id: state.run_id,
    contract_id: state.contract?.id ?? "",
    graph: String(first.data.graph ?? state.graph),
    policy_version: String(first.data.policy_version ?? ""),
    model_route: String(first.data.model_route ?? ""),
    outcome: state.status,
    context_sources: [...sources],
    tools_used: [...tools.entries()].map(([name, t]) => ({ name, ...t })),
    sensors: [...sensors.entries()].map(([name, s]) => ({ name, ...s })),
    test_results: { ran: testSensors.reduce((n, [, s]) => n + s.runs, 0), passed: testSensors.reduce((n, [, s]) => n + s.passed, 0), summary: testSensors.map(([n, s]) => `${n}: ${s.passed}/${s.runs} (last ${s.last})`).join("; ") },
    human_corrections: state.decisions.filter((d) => d.kind === "human").map((d) => ({ seq: d.seq, decision: d.summary.split(":")[0], note: d.summary.includes(":") ? d.summary.slice(d.summary.indexOf(":") + 2) : undefined })),
    retries: { total: state.retries_total, by_node: byNode, exhausted },
    cost: { input_tokens: state.cost.input_tokens, output_tokens: state.cost.output_tokens, usd: state.cost.usd, model_calls: state.cost.model_calls ?? 0 },
    accepted_artifact: state.status === "completed" ? (state.artifacts.find((a) => a.kind !== "plan" && a.kind !== "receipt") ?? null) : null,
    rollback_point: state.rollback_point ?? null,
    started_at: first.ts,
    finished_at: finished,
    events: events.length,
  };
}
