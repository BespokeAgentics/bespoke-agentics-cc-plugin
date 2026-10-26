// The reference runner. Executes the graph node by node; every transition is an event; the
// outcome of a node is computed by the harness from evidence, never taken from the model.
// The loop belongs to the harness: attempts, budget, escalation and pausing are decided here.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { isTerminal } from "./graph.ts";
import { projectState } from "./store.ts";
import { validateContract } from "./contract.ts";
import { buildReceipt } from "./receipt.ts";
import type {
  Contract, Graph, HarnessEvent, ModelAdapter, ModelInput, NodeDef, PolicyEngine, RunState, Sensor, SensorResult, StateStore, ToolAdapter, ToolCall,
} from "./types.ts";

export interface RunnerOptions {
  graph: Graph;
  graphPath: string;
  store: StateStore;
  policy: PolicyEngine;
  tools: ToolAdapter;
  sensors: Map<string, Sensor>;
  model: ModelAdapter;
  workspace: string;
  /** Simulate a crash: exit the process after this many node entries in this process. */
  killAfterSteps?: number;
  /** Force sensor failures: "tests:2" fails sensor "tests" on attempts <= 2. */
  injectFailures?: Record<string, number>;
  /** Decision to apply if the run is paused at human_review. */
  decision?: "approved" | "rejected";
  decisionNote?: string;
  log?: (line: string) => void;
}

export class Runner {
  private o: RunnerOptions;
  private stepsThisProcess = 0;
  constructor(o: RunnerOptions) { this.o = o; }

  private emit(type: HarnessEvent["type"], data: Record<string, unknown>, node?: string, attempt?: number): HarnessEvent {
    const e = this.o.store.append({ run_id: this.runId, type, node, attempt, data });
    this.o.log?.(`${String(e.seq).padStart(4)} ${type}${node ? ` ${node}` : ""}${attempt ? ` #${attempt}` : ""}${summarize(data)}`);
    return e;
  }

  private get runId(): string { return this.o.store.events()[0]?.run_id ?? this._runId; }
  private _runId = "";

  /** Start a brand-new run. */
  async start(run_id: string, contract: unknown): Promise<RunState> {
    if (this.o.store.events().length) throw new Error("store already has events; use resume()");
    this._runId = run_id;
    this.emit("run.started", { graph: this.o.graph.name, graph_path: this.o.graphPath, level: this.o.graph.level, entry: this.o.graph.entry, policy_version: this.o.policy.version(), model_route: this.o.model.route(), workspace: resolve(this.o.workspace), contract_candidate: contract });
    return this.continue();
  }

  /** Continue from whatever the log says. Idempotent on a finished run. */
  async continue(): Promise<RunState> {
    let state = projectState(this.o.store.events());
    if (state.status === "completed" || state.status === "failed") return state;
    if (state.status === "paused") {
      if (!this.o.decision) return state;
      this.emit("run.resumed", { with_decision: this.o.decision });
      state = projectState(this.o.store.events());
    } else if (state.step > 0 && this.o.store.events().at(-1)?.type !== "run.started") {
      this.emit("run.resumed", { from_node: state.current_node, step: state.step });
    }

    const g = this.o.graph;
    while (true) {
      state = projectState(this.o.store.events());
      if (state.step >= g.budget.max_steps) { this.fail(state, "budget.max_steps exhausted"); break; }
      if (g.budget.max_cost_usd !== undefined && state.cost.usd > g.budget.max_cost_usd) { this.fail(state, "budget.max_cost_usd exhausted"); break; }

      const name = state.current_node;
      const node = g.nodes[name];
      if (!node) { this.fail(state, `node "${name}" does not exist`); break; }
      const attempt = (state.attempts[name] ?? 0) + 1;

      // Loop cap: decided by the harness before the model gets another turn.
      if (node.retry && attempt > node.retry.max) {
        this.emit("retry.exhausted", { max: node.retry.max, to: node.retry.on_exhausted }, name, attempt);
        this.emit("escalated", { reason: `retry cap ${node.retry.max} reached at ${name}`, to: node.retry.on_exhausted }, name, attempt);
        this.emit("node.exited", { outcome: "exhausted", next: node.retry.on_exhausted }, name, attempt);
        continue;
      }
      if (node.type === "repair" && state.retries_total >= g.budget.max_retries_total) {
        const to = node.retry?.on_exhausted ?? "receipt";
        this.emit("retry.exhausted", { max_retries_total: g.budget.max_retries_total, to }, name, attempt);
        this.emit("escalated", { reason: `budget.max_retries_total ${g.budget.max_retries_total} reached`, to }, name, attempt);
        this.emit("node.exited", { outcome: "exhausted", next: to }, name, attempt);
        continue;
      }

      this.emit("node.entered", { type: node.type }, name, attempt);
      this.stepsThisProcess++;
      if (this.o.killAfterSteps !== undefined && this.stepsThisProcess >= this.o.killAfterSteps) {
        this.o.log?.(`-- simulated crash after ${this.stepsThisProcess} steps (node ${name} entered, not exited)`);
        process.exit(137);
      }

      const outcome = await this.exec(name, node, attempt, projectState(this.o.store.events()));
      if (outcome === "pending") {
        this.emit("run.paused", { at: name, waiting_for: "human decision (resume --decision approved|rejected)" }, name, attempt);
        break;
      }
      if (isTerminal(node)) {
        this.emit("node.exited", { outcome }, name, attempt);
        break;
      }
      const next = node.edges?.[outcome] ?? node.edges?.["*"];
      if (!next) { this.emit("node.exited", { outcome }, name, attempt); this.fail(projectState(this.o.store.events()), `no edge for outcome "${outcome}" at ${name}`); break; }
      this.emit("node.exited", { outcome, next }, name, attempt);
    }
    state = projectState(this.o.store.events());
    this.o.store.snapshot(state);
    return state;
  }

  private fail(state: RunState, reason: string): void {
    this.emit("run.failed", { reason, at: state.current_node, step: state.step });
    this.o.store.snapshot(projectState(this.o.store.events()));
  }

  private async exec(name: string, node: NodeDef, attempt: number, state: RunState): Promise<string> {
    switch (node.type) {
      case "contract": return this.execContract(name, attempt);
      case "load_context": return this.execLoadContext(name, node, attempt, state);
      case "plan": return this.execPlan(name, node, attempt, state);
      case "act": return this.execAct(name, node, attempt, state);
      case "verify": return this.execVerify(name, node, attempt, state);
      case "policy_gate": return this.execGate(name, attempt, state);
      case "repair": return this.execRepair(name, node, attempt, state);
      case "human_review": return this.execHumanReview(name, attempt, state);
      case "receipt": return this.execReceipt(name, attempt, state);
    }
  }

  private execContract(name: string, attempt: number): string {
    const candidate = this.o.store.events()[0].data.contract_candidate;
    const r = validateContract(candidate, new Set(this.o.sensors.keys()));
    this.emit("sensor.ran", { name: "contract_complete", pass: r.ok, summary: r.ok ? "contract complete" : r.errors.map((e) => `${e.path}: ${e.message}`).join("; "), evidence: { errors: r.errors } }, name, attempt);
    if (!r.ok) { this.emit("contract.rejected", { reason: r.errors.map((e) => `${e.path}: ${e.message}`).join("; "), errors: r.errors }, name, attempt); return "fail"; }
    this.emit("contract.accepted", { contract: candidate }, name, attempt);
    this.emit("rollback.point", rollbackPoint(this.o.workspace, this.o.store.location()), name, attempt);
    return "ok";
  }

  private loadGuides(node: NodeDef): { path: string; content: string }[] {
    const out: { path: string; content: string }[] = [];
    for (const g of node.guides ?? []) {
      const p = resolve(this.o.workspace, g);
      if (existsSync(p)) out.push({ path: g, content: readFileSync(p, "utf8").slice(0, 20000) });
    }
    return out;
  }

  private execLoadContext(name: string, node: NodeDef, attempt: number, state: RunState): string {
    const guides = this.loadGuides(node);
    const missing = (node.guides ?? []).filter((g) => !existsSync(resolve(this.o.workspace, g)));
    const sources = [...guides.map((g) => g.path), ...(state.contract?.inputs ?? [])];
    this.emit("context.loaded", { sources, missing, bytes: guides.reduce((n, g) => n + g.content.length, 0) }, name, attempt);
    if (missing.length && node.edges?.fail) return "fail";
    return "ok";
  }

  private modelInput(name: string, node: NodeDef, attempt: number, state: RunState): ModelInput {
    const events = this.o.store.events();
    const history = events.filter((e) => e.type === "node.exited").map((e) => ({ node: e.node!, outcome: String(e.data.outcome), failures: [] as string[] }));
    // Failures since this node last exited: the concrete evidence the model repairs against.
    const lastExit = events.findLast((e) => e.type === "node.exited" && e.node === name)?.seq ?? 0;
    const lastFailures = state.failures.filter((f) => f.seq > lastExit).map((f) => f.summary);
    const planEvent = events.findLast((e) => e.type === "artifact.produced" && e.data.kind === "plan");
    return { node: name, node_type: node.type, attempt, contract: state.contract, guides: this.loadGuides(node), tools: node.tools ?? [], history, last_failures: lastFailures, plan: planEvent?.data.plan as string[] | undefined };
  }

  private async propose(name: string, node: NodeDef, attempt: number, state: RunState) {
    const out = await this.o.model.propose(this.modelInput(name, node, attempt, state));
    this.emit("cost.recorded", { route: this.o.model.route(), ...(out.usage ?? { input_tokens: 0, output_tokens: 0, usd: 0 }) }, name, attempt);
    return out;
  }

  private async execPlan(name: string, node: NodeDef, attempt: number, state: RunState): Promise<string> {
    const out = await this.propose(name, node, attempt, state);
    // The plan is carried on the exit event so later nodes can read it from history.
    this.emit("artifact.produced", { path: `${this.o.store.location()}/plan.json`, kind: "plan", plan: out.plan ?? [] }, name, attempt);
    writeFileSync(join(this.o.store.location(), "plan.json"), JSON.stringify({ plan: out.plan ?? [], notes: out.notes ?? "" }, null, 2) + "\n");
    return "ok";
  }

  private async execAct(name: string, node: NodeDef, attempt: number, state: RunState): Promise<string> {
    const out = await this.propose(name, node, attempt, state);
    let blocked = false, failed = false;
    for (const call of out.calls ?? []) {
      this.emit("tool.requested", { tool: call.tool, args: redact(call.args) }, name, attempt);
      if (!(node.tools ?? []).includes(call.tool)) {
        this.emit("policy.decided", { tool: call.tool, decision: "deny", rule: "node.tools", reason: `tool is not granted to node ${name}`, tier: this.o.policy.toolTier(call.tool) ?? "approve" }, name, attempt);
        blocked = true; continue;
      }
      const d = this.o.policy.decide({ tool: call.tool, args: call.args, node: name, contract: state.contract, run_id: this.runId });
      this.emit("policy.decided", { tool: call.tool, ...d }, name, attempt);
      if (d.decision !== "allow") { blocked = true; continue; }
      if (!this.o.tools.has(call.tool)) { this.emit("tool.executed", { tool: call.tool, ok: false, error: "no adapter implements this tool" }, name, attempt); failed = true; continue; }
      const r = await this.o.tools.execute(call, { workspace: this.o.workspace, run_id: this.runId });
      this.emit("tool.executed", { tool: call.tool, ok: r.ok, error: r.error, output: truncate(r.output) }, name, attempt);
      if (!r.ok) failed = true;
      if (r.artifact) this.emit("artifact.produced", { ...r.artifact }, name, attempt);
    }
    // Sensors declared directly on an act node run here (an act followed by verify declares none).
    if (node.sensors?.length) {
      const results = await this.runSensors(name, node, attempt, state);
      if (results.some((r) => !r.pass)) failed = true;
    }
    if (blocked) return "blocked";
    if (failed) return "fail";
    return "ok";
  }

  private async runSensors(name: string, node: NodeDef, attempt: number, state: RunState): Promise<SensorResult[]> {
    const ctx = { workspace: this.o.workspace, contract: state.contract, artifacts: state.artifacts, attempt, injectFailure: (s: string, a: number) => (this.o.injectFailures?.[s] ?? 0) >= a };
    const sensors = (node.sensors ?? []).map((s) => { const sensor = this.o.sensors.get(s); if (!sensor) throw new Error(`sensor ${s} not built`); return sensor; });
    const results = node.parallel ? await Promise.all(sensors.map((s) => s.run(ctx))) : await sequential(sensors.map((s) => () => s.run(ctx)));
    for (const r of results) this.emit("sensor.ran", { name: r.name, pass: r.pass, summary: r.summary, evidence: truncate(r.evidence), error: r.error ?? false, parallel: node.parallel ?? false }, name, attempt);
    return results;
  }

  private async execVerify(name: string, node: NodeDef, attempt: number, state: RunState): Promise<string> {
    const results = await this.runSensors(name, node, attempt, state);
    return results.every((r) => r.pass) ? "pass" : "fail";
  }

  private execGate(name: string, attempt: number, state: RunState): string {
    const risk = state.contract?.risk ?? "irreversible";
    if (risk === "reversible") { this.emit("policy.decided", { tool: "release", decision: "allow", rule: "gate:risk=reversible", reason: "workspace-only change", tier: "write" }, name, attempt); return "allow"; }
    const d = this.o.policy.decide({ tool: "release", args: {}, node: name, contract: state.contract, run_id: this.runId });
    // "release" is a virtual approve-tier tool; a policy without it falls back to require_approval semantics.
    const decision = d.rule === "tool.unknown" ? ({ decision: "needs_approval", rule: "gate:risk=" + risk, reason: `contract risk is ${risk}; add an approval record for tool "release" to pass the gate`, tier: "approve" } as const) : d;
    this.emit("policy.decided", { tool: "release", ...decision }, name, attempt);
    return decision.decision;
  }

  private async execRepair(name: string, node: NodeDef, attempt: number, state: RunState): Promise<string> {
    const out = await this.propose(name, node, attempt, state);
    this.emit("retry.scheduled", { attempt, max: node.retry?.max, notes: out.notes ?? "", failures: state.failures.slice(-5).map((f) => f.summary) }, name, attempt);
    return "ok";
  }

  private execHumanReview(name: string, attempt: number, state: RunState): string {
    if (this.o.decision) {
      const d = this.o.decision; this.o.decision = undefined;
      this.emit("human.decided", { decision: d, note: this.o.decisionNote ?? "" }, name, attempt);
      return d;
    }
    const reason = state.pending.at(-1)?.summary ?? state.failures.at(-1)?.summary ?? "review requested";
    this.emit("escalated", { reason, pending: state.pending.map((p) => p.summary) }, name, attempt);
    const pendingPath = join(this.o.store.location(), "pending.json");
    writeFileSync(pendingPath, JSON.stringify({ run_id: this.runId, node: name, reason, pending: state.pending, failures: state.failures.slice(-5), how_to_continue: `resume --run ${this.o.store.location()} --decision approved|rejected [--note '...']` }, null, 2) + "\n");
    return "pending";
  }

  private execReceipt(name: string, attempt: number, state: RunState): string {
    const accepted = state.last_outcome === "allow" || state.last_outcome === "approved";
    if (accepted) this.emit("run.completed", { artifact: state.artifacts.find((a) => a.kind !== "plan") ?? null }, name, attempt);
    else this.emit("run.failed", { reason: state.last_outcome === "fail" && state.failures[0]?.node === "contract" ? "contract rejected" : `arrived at receipt via outcome "${state.last_outcome}"`, at: name }, name, attempt);
    const final = projectState(this.o.store.events());
    const receipt = buildReceipt(this.o.store.events(), final, this.o.graph);
    const p = join(this.o.store.location(), "receipt.json");
    writeFileSync(p, JSON.stringify(receipt, null, 2) + "\n");
    this.emit("artifact.produced", { path: p, kind: "receipt" }, name, attempt);
    return accepted ? "ok" : "fail";
  }
}

async function sequential<T>(fns: (() => Promise<T>)[]): Promise<T[]> { const out: T[] = []; for (const f of fns) out.push(await f()); return out; }

function truncate(v: unknown): unknown {
  const s = JSON.stringify(v ?? null);
  return s.length > 4000 ? { truncated: true, preview: s.slice(0, 4000) } : v ?? null;
}

function redact(args: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(args)) out[k] = typeof v === "string" && v.length > 400 ? `${v.slice(0, 400)}…(${v.length} chars)` : v;
  return out;
}

function summarize(d: Record<string, unknown>): string {
  const keys = ["outcome", "decision", "tool", "pass", "reason", "name"].filter((k) => k in d);
  return keys.length ? " " + keys.map((k) => `${k}=${JSON.stringify(d[k])}`).join(" ") : "";
}

export function rollbackPoint(workspace: string, runDir: string): Record<string, unknown> {
  const git = (args: string[]) => spawnSync("git", args, { cwd: workspace, encoding: "utf8" });
  const head = git(["rev-parse", "HEAD"]);
  if (head.status !== 0) return { kind: "none", reason: "workspace is not a git repository" };
  const diff = git(["diff", "--binary", "HEAD"]);
  const dir = join(runDir, "rollback");
  mkdirSync(dir, { recursive: true });
  const patch = join(dir, "pre.patch");
  writeFileSync(patch, diff.stdout);
  return { kind: "git", head: head.stdout.trim(), dirty: diff.stdout.length > 0, patch, how: `git checkout ${head.stdout.trim()} -- . && git apply ${patch}` };
}

export function readJson(p: string): unknown { return JSON.parse(readFileSync(p, "utf8")); }
export function ensureDir(p: string): void { mkdirSync(dirname(p), { recursive: true }); }
