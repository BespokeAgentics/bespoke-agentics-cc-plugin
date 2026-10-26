// upgrade-from-failure: trace + failure class -> a Guide + Check proposal.
// The class is inferred from the events when not given. The proposal repairs the class of
// failure (references/failure-taxonomy.md), not the one output.

import type { HarnessEvent } from "./types.ts";

export type FailureClass = "missing_context" | "wrong_tool" | "bad_output" | "repeated_loop" | "unsafe_action" | "lost_decision" | "unknown_failure";
export const FAILURE_CLASSES: FailureClass[] = ["missing_context", "wrong_tool", "bad_output", "repeated_loop", "unsafe_action", "lost_decision", "unknown_failure"];

export interface Evidence { seq: number; type: string; node?: string; summary: string }
export interface Proposal {
  failure_class: FailureClass;
  inferred: boolean;
  evidence: Evidence[];
  guide: { file: string; section: string; text: string };
  check: { kind: "sensor" | "validator" | "policy" | "graph" | "map"; where: string; spec: Record<string, unknown> | string; todo?: string };
  rationale: string;
}

function short(e: HarnessEvent): string {
  const d = e.data;
  const bits = ["tool", "decision", "name", "pass", "reason", "summary", "error", "outcome"].filter((k) => k in d).map((k) => `${k}=${JSON.stringify(d[k]).slice(0, 80)}`);
  return bits.join(" ");
}

export function inferClass(events: HarnessEvent[]): { cls: FailureClass; evidence: Evidence[] } {
  const ev = (filter: (e: HarnessEvent) => boolean) => events.filter(filter).map((e) => ({ seq: e.seq, type: e.type, node: e.node, summary: short(e) }));
  const exhausted = ev((e) => e.type === "retry.exhausted" || (e.type === "run.failed" && /budget/.test(String(e.data.reason))));
  if (exhausted.length) return { cls: "repeated_loop", evidence: [...exhausted, ...ev((e) => e.type === "retry.scheduled").slice(-3)] };
  const unsafe = ev((e) => e.type === "policy.decided" && e.data.decision !== "allow");
  if (unsafe.length) return { cls: "unsafe_action", evidence: unsafe };
  const missing = ev((e) => e.type === "context.loaded" && Array.isArray(e.data.missing) && (e.data.missing as unknown[]).length > 0);
  if (missing.length) return { cls: "missing_context", evidence: missing };
  const toolErr = ev((e) => e.type === "tool.executed" && e.data.ok === false);
  if (toolErr.length) return { cls: "wrong_tool", evidence: toolErr };
  const sensorErr = ev((e) => e.type === "sensor.ran" && e.data.error === true);
  if (sensorErr.length) return { cls: "unknown_failure", evidence: sensorErr };
  const sensorFail = ev((e) => e.type === "sensor.ran" && e.data.pass === false);
  if (sensorFail.length) return { cls: "bad_output", evidence: sensorFail };
  const paused = ev((e) => e.type === "run.paused");
  if (paused.length && !events.some((e) => e.type === "human.decided")) return { cls: "lost_decision", evidence: paused };
  return { cls: "unknown_failure", evidence: ev((e) => e.type === "run.failed").concat(ev((e) => e.type === "node.exited").slice(-2)) };
}

export function propose(events: HarnessEvent[], cls?: FailureClass): Proposal {
  const inferred = !cls;
  const inf = inferClass(events);
  const failure = cls ?? inf.cls;
  const evidence = cls ? inf.cls === cls ? inf.evidence : events.slice(-5).map((e) => ({ seq: e.seq, type: e.type, node: e.node, summary: short(e) })) : inf.evidence;
  const sensorNames = [...new Set(events.filter((e) => e.type === "sensor.ran" && e.data.pass === false).map((e) => String(e.data.name)))];
  const deniedTools = [...new Set(events.filter((e) => e.type === "policy.decided" && e.data.decision !== "allow").map((e) => String(e.data.tool)))];
  const missingGuides = [...new Set(events.flatMap((e) => (e.type === "context.loaded" ? (e.data.missing as string[]) ?? [] : [])))];
  const failedTools = [...new Set(events.filter((e) => e.type === "tool.executed" && e.data.ok === false).map((e) => String(e.data.tool)))];
  const repairNode = events.find((e) => e.type === "retry.exhausted")?.node ?? "repair";

  const table: Record<FailureClass, () => Omit<Proposal, "failure_class" | "inferred" | "evidence">> = {
    missing_context: () => ({
      guide: { file: "AGENTS.md", section: "Where things are", text: `Add a row pointing at the guide the task needed${missingGuides.length ? ` (${missingGuides.join(", ")} was named but not found)` : ""}, and a retrieval rule: load it when task_class matches.` },
      check: { kind: "map", where: "harness/bin/audit Q2 + load_context node", spec: { node: "load_context", guides: missingGuides.length ? missingGuides : ["AGENTS.md", "docs/<guide>.md"], edges: { ok: "plan", fail: "human_review" } }, todo: undefined },
      rationale: "A missing guide is a map defect, not a model defect: the load_context node should fail loudly (fail edge) when a named guide is absent, and audit Q2 catches broken pointers before a run.",
    }),
    wrong_tool: () => ({
      guide: { file: "harness/policy.yaml", section: `tools.${failedTools[0] ?? "<tool>"}`, text: `Rewrite purpose/output/failure/boundary so the model can predict the result; if the tool was the wrong one for the job, add the right tool with its own contract and name the choice in AGENTS.md § Commands.` },
      check: { kind: "policy", where: "harness/policy.yaml", spec: { tools: { [failedTools[0] ?? "<tool>"]: { tier: "<tier>", purpose: "<one sentence>", output: "<shape>", failure: "<explicit failure states>", boundary: "<what it never touches>" } } } },
      rationale: "A tool that fails in a way the model did not expect has an incomplete contract. validate-graph TOOL_UNDECLARED and audit Q3 refuse tools without all four fields.",
    }),
    bad_output: () => ({
      guide: { file: "AGENTS.md", section: "Rules, each with its check", text: `Add the rule the output violated${sensorNames.length ? ` (sensor ${sensorNames.join(", ")} failed)` : ""} as one line of prose, and tighten the contract's done_when to name the sensor that proves it.` },
      check: { kind: "sensor", where: "harness/graph.yaml § sensors", spec: { [sensorNames[0] ?? "new_check"]: { kind: "command", cmd: "<command that exits non-zero on this defect>", applies_to: ["code"] } } },
      rationale: "Bad output that reached verify means the check is weaker than the rule. Make the sensor fail on this class of defect, then the loop repairs against evidence instead of opinion.",
    }),
    repeated_loop: () => ({
      guide: { file: "AGENTS.md", section: "Rules, each with its check", text: `When ${sensorNames.join(", ") || "a sensor"} fails twice with the same summary, stop repairing and escalate with the evidence; the human sees the pending.json.` },
      check: { kind: "graph", where: `harness/graph.yaml nodes.${repairNode}`, spec: { [repairNode]: { type: "repair", retry: { max: 2, on_exhausted: "human_review" }, edges: { ok: "act" } }, budget: { max_retries_total: 4 } } },
      rationale: "The loop already hit its cap (good); the upgrade lowers the cap for this failure signature and keeps the escalation path, so the next run spends less before a human sees it.",
    }),
    unsafe_action: () => ({
      guide: { file: "AGENTS.md", section: "Harness", text: `${deniedTools.join(", ") || "This tool"} requires an approval record; request it in the contract (risk: irreversible) and plan the gate before act, do not retry the call.` },
      check: { kind: "policy", where: "harness/policy.yaml + harness/graph.yaml", spec: { policy: { tools: Object.fromEntries(deniedTools.map((t) => [t, { tier: "approve" }])) }, graph: { gate_before_act: "policy_gate -> act for nodes that grant approve-tier tools (validate-graph UNGATED_RISK)" } } },
      rationale: "The gate held. The upgrade makes the requirement visible to the model earlier (contract risk + a gate before the act node) so the run pauses at plan time, not mid-action.",
    }),
    lost_decision: () => ({
      guide: { file: "AGENTS.md", section: "Harness", text: "Decisions are recorded as human.decided events via `resume --decision`; never continue a paused run by re-stating the decision in chat." },
      check: { kind: "validator", where: "harness/runs/<id>/events.jsonl", spec: "resume refuses to continue a paused run without --decision; the decision becomes a human.decided event (enforced by the runner)" },
      rationale: "A decision that lives only in the conversation is lost at the next session; the event log is the only place the harness reads it from.",
    }),
    unknown_failure: () => ({
      guide: { file: "AGENTS.md", section: "When something fails", text: "Capture the evidence first: the failing sensor's stdout/stderr and the tool output are in events.jsonl; attach the seq numbers to the issue." },
      check: { kind: "sensor", where: "harness/graph.yaml § sensors", spec: { "<name>": { kind: "command", cmd: "<reproduce the failure deterministically>", timeout_ms: 60000 } }, todo: "no mechanical check until the failure is reproducible; the sensor above fails on purpose until cmd is set" },
      rationale: "An unknown failure means tracing was not enough to classify it; the upgrade is more evidence capture, then a sensor once the cause is known.",
    }),
  };
  const p = table[failure]();
  return { failure_class: failure, inferred, evidence, ...p };
}
