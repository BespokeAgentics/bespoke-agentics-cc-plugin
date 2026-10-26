// File-based StateStore: events.jsonl is the append-only history; state.json is a snapshot
// (a convenience, never the truth). projectState rebuilds RunState from the events alone,
// which is what makes a run resumable after the process is killed at any point.

import { appendFileSync, closeSync, existsSync, fsyncSync, mkdirSync, openSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import type { HarnessEvent, RunState, StateStore, Contract } from "./types.ts";

export class FileStore implements StateStore {
  private dir: string;
  private seq: number;
  private cache: HarnessEvent[];

  constructor(dir: string) {
    this.dir = dir;
    mkdirSync(dir, { recursive: true });
    this.cache = this.readAll();
    this.seq = this.cache.length ? this.cache[this.cache.length - 1].seq : 0;
  }

  static exists(dir: string): boolean { return existsSync(join(dir, "events.jsonl")); }

  private readAll(): HarnessEvent[] {
    const p = join(this.dir, "events.jsonl");
    if (!existsSync(p)) return [];
    const out: HarnessEvent[] = [];
    for (const line of readFileSync(p, "utf8").split("\n")) {
      if (!line.trim()) continue;
      try { out.push(JSON.parse(line)); }
      catch { break; } // a torn final line from a crash mid-write is dropped; everything before it is intact
    }
    return out;
  }

  append(e: Omit<HarnessEvent, "seq" | "ts">): HarnessEvent {
    const full: HarnessEvent = { seq: ++this.seq, ts: new Date().toISOString(), run_id: e.run_id, type: e.type, data: e.data };
    if (e.node !== undefined) full.node = e.node;
    if (e.attempt !== undefined) full.attempt = e.attempt;
    const p = join(this.dir, "events.jsonl");
    appendFileSync(p, JSON.stringify(full) + "\n");
    const fd = openSync(p, "r"); try { fsyncSync(fd); } finally { closeSync(fd); }
    this.cache.push(full);
    return full;
  }

  events(): HarnessEvent[] { return [...this.cache]; }
  snapshot(state: RunState): void { writeFileSync(join(this.dir, "state.json"), JSON.stringify(state, null, 2) + "\n"); }
  location(): string { return this.dir; }
}

export function emptyState(run_id: string, graph: string, level: number, entry: string): RunState {
  return {
    run_id, graph, level, status: "running", current_node: entry, step: 0, attempts: {}, retries_total: 0,
    decisions: [], artifacts: [], failures: [], pending: [], cost: { input_tokens: 0, output_tokens: 0, usd: 0, model_calls: 0 }, last_seq: 0,
  };
}

/** Current state is a projection of the log. Pure; replaying the same events yields the same state. */
export function projectState(events: HarnessEvent[]): RunState {
  if (!events.length) throw new Error("cannot project state from an empty event log");
  const first = events[0];
  if (first.type !== "run.started") throw new Error("event log does not begin with run.started");
  const d = first.data as { graph: string; level: number; entry: string };
  const s = emptyState(first.run_id, d.graph, d.level, d.entry);
  for (const e of events) {
    s.last_seq = e.seq;
    switch (e.type) {
      case "contract.accepted": s.contract = e.data.contract as Contract; break;
      case "contract.rejected": s.failures.push({ seq: e.seq, node: e.node ?? "contract", summary: String(e.data.reason) }); break;
      case "node.entered":
        s.current_node = e.node!; s.step++;
        s.attempts[e.node!] = (s.attempts[e.node!] ?? 0) + 1;
        s.status = "running";
        break;
      case "node.exited":
        s.last_outcome = String(e.data.outcome);
        if (typeof e.data.next === "string") s.current_node = e.data.next;
        break;
      case "policy.decided":
        if (e.data.decision !== "allow") s.decisions.push({ seq: e.seq, kind: "policy", summary: `${e.data.decision}: ${e.data.tool} (${e.data.rule})`, node: e.node });
        if (e.data.decision === "needs_approval") s.pending.push({ seq: e.seq, kind: "approval", summary: `approval needed for ${e.data.tool}`, node: e.node, tool: String(e.data.tool) });
        if (e.data.decision === "deny") s.failures.push({ seq: e.seq, node: e.node!, summary: `policy denied ${e.data.tool}: ${e.data.reason}`, tool: String(e.data.tool) });
        break;
      case "tool.executed":
        if (e.data.ok === false) s.failures.push({ seq: e.seq, node: e.node!, summary: `${e.data.tool} failed: ${e.data.error}`, tool: String(e.data.tool) });
        break;
      case "artifact.produced": s.artifacts.push({ seq: e.seq, path: String(e.data.path), kind: e.data.kind as string | undefined, node: e.node }); break;
      case "sensor.ran":
        if (e.data.pass === false) s.failures.push({ seq: e.seq, node: e.node!, summary: `${e.data.name}: ${e.data.summary}`, sensor: String(e.data.name) });
        break;
      case "retry.scheduled": s.retries_total++; s.decisions.push({ seq: e.seq, kind: "harness", summary: `retry ${e.data.attempt}/${e.data.max} at ${e.node}`, node: e.node }); break;
      case "retry.exhausted": s.decisions.push({ seq: e.seq, kind: "harness", summary: `retries exhausted at ${e.node}; escalating to ${e.data.to}`, node: e.node }); break;
      case "escalated": s.pending.push({ seq: e.seq, kind: "review", summary: String(e.data.reason), node: e.node }); break;
      case "human.decided":
        s.decisions.push({ seq: e.seq, kind: "human", summary: `${e.data.decision}${e.data.note ? `: ${e.data.note}` : ""}`, node: e.node });
        s.pending = [];
        break;
      case "cost.recorded":
        s.cost.input_tokens += Number(e.data.input_tokens ?? 0);
        s.cost.output_tokens += Number(e.data.output_tokens ?? 0);
        s.cost.usd += Number(e.data.usd ?? 0);
        s.cost.model_calls = (s.cost.model_calls ?? 0) + 1;
        break;
      case "rollback.point": s.rollback_point = e.data; break;
      case "run.paused": s.status = "paused"; break;
      case "run.resumed": s.status = "running"; break;
      case "run.completed": s.status = "completed"; s.outcome = "completed"; break;
      case "run.failed": s.status = "failed"; s.outcome = String(e.data.reason ?? "failed"); break;
    }
  }
  s.cost.usd = Math.round(s.cost.usd * 1e6) / 1e6;
  return s;
}
