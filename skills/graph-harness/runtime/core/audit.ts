// audit: score a project against the 12-question readiness checklist (references/checklist.md).
// Every answer is mechanical (a file, a field, a validator result, an event in a trace) and every
// gap carries one concrete fix.

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { loadStructured, loadPolicy, loadSchema, validateGraph } from "./graph.ts";
import { validate } from "./schema.ts";
import { FileStore, projectState } from "./store.ts";
import type { Graph, Policy } from "./types.ts";

export type Status = "pass" | "partial" | "fail";
export interface AuditItem { id: number; question: string; status: Status; evidence: string; fix: string }
export interface AuditReport { target: string; harness_dir: string; level_detected: number; score: number; max: number; items: AuditItem[]; smallest_next_upgrade: string }

function latestRun(runs: string): string | undefined {
  if (!existsSync(runs)) return undefined;
  const dirs = readdirSync(runs).map((d) => join(runs, d)).filter((p) => statSync(p).isDirectory() && FileStore.exists(p));
  dirs.sort((a, b) => statSync(join(b, "events.jsonl")).mtimeMs - statSync(join(a, "events.jsonl")).mtimeMs);
  return dirs[0];
}

export function audit(targetIn: string, harnessIn?: string): AuditReport {
  const target = resolve(targetIn);
  const harness = resolve(harnessIn ?? join(target, "harness"));
  const items: AuditItem[] = [];
  const add = (id: number, question: string, status: Status, evidence: string, fix: string) => items.push({ id, question, status, evidence, fix: status === "pass" ? "" : fix });

  const mapPath = ["AGENTS.md", "CLAUDE.md"].map((f) => join(target, f)).find(existsSync);
  const policyPath = join(harness, "policy.yaml");
  const graphPath = join(harness, "graph.yaml");
  let policy: Policy | undefined; let graph: Graph | undefined; let graphReport: ReturnType<typeof validateGraph> | undefined;
  try { if (existsSync(policyPath)) policy = loadPolicy(policyPath); } catch { /* invalid; reported below */ }
  try { if (existsSync(graphPath)) { graph = loadStructured(graphPath) as Graph; graphReport = validateGraph(graph, policy, graphPath); } } catch (e) { graphReport = { ok: false, graph: graphPath, errors: [{ code: "PARSE", message: (e as Error).message }], warnings: [], stats: { nodes: 0, edges: 0, cycles: 0, sensors: 0 } }; }
  const run = latestRun(join(harness, "runs"));
  const events = run ? new FileStore(run).events() : [];
  const state = events.length ? projectState(events) : undefined;

  // 1 contract
  const schemaOk = existsSync(join(harness, "schemas", "contract.schema.json"));
  const contracts = existsSync(join(harness, "contracts")) ? readdirSync(join(harness, "contracts")).filter((f) => f.endsWith(".json")) : [];
  const realContracts = contracts.filter((f) => f !== "example.json");
  add(1, "Does every task become a contract (goal, inputs, output, constraints, done_when) before any action?",
    schemaOk && realContracts.length ? "pass" : schemaOk ? "partial" : "fail",
    schemaOk ? `schema present; contracts: ${contracts.join(", ") || "none"}` : "no harness/schemas/contract.schema.json",
    schemaOk ? "write the first real contract in harness/contracts/<id>.json (example.json does not count)" : "run bootstrap --level 1 to install the contract schema and an example");

  // 2 map
  let links = 0, broken: string[] = [];
  if (mapPath) {
    const text = readFileSync(mapPath, "utf8");
    for (const m of text.matchAll(/`([\w./-]+\.(md|yaml|json|ts|py))`|\]\(([\w./-]+)\)/g)) {
      const p = m[1] ?? m[3]; if (!p || p.startsWith("http")) continue;
      links++; if (!existsSync(join(target, p))) broken.push(p);
    }
  }
  add(2, "Is there a small root map (AGENTS.md) that points to architecture, testing, product and security guides instead of restating them?",
    mapPath && links >= 3 && broken.length === 0 ? "pass" : mapPath ? "partial" : "fail",
    mapPath ? `${mapPath.split("/").pop()}: ${links} file pointers, ${broken.length} broken${broken.length ? ` (${broken.slice(0, 3).join(", ")})` : ""}` : "no AGENTS.md or CLAUDE.md",
    mapPath ? (broken.length ? `fix the broken pointers: ${broken.join(", ")}` : "add pointers to at least three guides (architecture, testing, security) in AGENTS.md") : "run bootstrap --level 1 to generate AGENTS.md from the repo");

  // 3 tool contracts
  const tools = policy ? Object.entries(policy.tools) : [];
  const incomplete = tools.filter(([, t]) => !t.purpose || !t.output || !t.failure || !t.boundary).map(([n]) => n);
  add(3, "Does every tool have a contract: purpose, predictable output, explicit failure state, boundary, and a tier?",
    policy && tools.length && incomplete.length === 0 ? "pass" : policy ? "partial" : "fail",
    policy ? `${tools.length} tools; incomplete: ${incomplete.join(", ") || "none"}` : "no harness/policy.yaml",
    policy ? `fill output/failure/boundary for: ${incomplete.join(", ")}` : "run bootstrap --level 1 to install policy.yaml with tool contracts");

  // 4 permission tiers
  const approveTools = tools.filter(([, t]) => t.tier === "approve").map(([n]) => n);
  const approveRule = policy?.tiers.approve;
  add(4, "Are permission tiers set (read allowed, tests sandboxed, writes workspace-only, network scoped, deploy/delete needs approval) and enforced outside the model?",
    policy && approveRule === "require_approval" && approveTools.length && existsSync(join(harness, "runtime", "core", "policy.ts")) ? "pass" : policy ? "partial" : "fail",
    policy ? `approve tier = ${approveRule}; approve-tier tools: ${approveTools.join(", ") || "none"}; runtime ${existsSync(join(harness, "runtime", "core", "policy.ts")) ? "present" : "absent"}` : "no policy",
    !policy ? "run bootstrap --level 1" : approveRule !== "require_approval" ? "run bootstrap --level 3 (approve tier -> require_approval + approvals.json)" : "run bootstrap --level 2 so the runtime enforces policy.yaml");

  // 5 durable state
  add(5, "Does durable state (decisions, artifacts, failures, pending items, current step) live outside the conversation?",
    run && state ? "pass" : existsSync(join(harness, "runtime", "core", "store.ts")) ? "partial" : "fail",
    run ? `latest run ${run.split("/").pop()}: ${events.length} events, status ${state?.status}` : existsSync(join(harness, "runtime")) ? "runtime installed, no runs yet" : "no event log and no runtime",
    existsSync(join(harness, "runtime")) ? "push one contract through harness/bin/run so a run exists" : "run bootstrap --level 2 (event log + state projection)");

  // 6 sensors per artifact type
  const sensors = graph?.sensors ?? {};
  const todo = Object.entries(sensors).filter(([, s]) => s.todo).map(([n]) => n);
  const classes = new Set<string>(); for (const s of Object.values(sensors)) for (const c of s.applies_to ?? []) classes.add(c);
  add(6, "Does each artifact type the project produces have evidence producers (code: tests/types/lint; ui: render/screenshot; research: sources; data: schema/range/freshness)?",
    graph && Object.keys(sensors).length >= 2 && todo.length === 0 ? "pass" : graph && Object.keys(sensors).length ? "partial" : "fail",
    graph ? `${Object.keys(sensors).length} sensors for [${[...classes].join(", ")}]; TODO: ${todo.join(", ") || "none"}` : "no graph.yaml",
    graph ? (todo.length ? `wire the TODO sensors: ${todo.join(", ")} (set cmd/module in harness/graph.yaml)` : "declare at least two sensors under sensors: in harness/graph.yaml") : "run bootstrap --level 2 --task-class <class>");

  // 7 harness-owned loop
  const capped = graph ? Object.values(graph.nodes).some((n) => n.type === "repair" && n.retry) : false;
  add(7, "Is the loop owned by the harness: bounded retries, a budget, evidence-gated continuation, escalation to a human?",
    graphReport?.ok && capped && graph?.budget ? "pass" : graph ? "partial" : "fail",
    graphReport ? (graphReport.ok ? `graph valid; budget max_steps=${graph?.budget.max_steps} max_retries_total=${graph?.budget.max_retries_total}` : `validate-graph: ${graphReport.errors.map((e) => e.code).join(", ")}`) : "no graph",
    graphReport && !graphReport.ok ? `fix validate-graph errors: ${graphReport.errors.map((e) => `${e.code}${e.node ? `[${e.node}]` : ""}`).join(", ")}` : "run bootstrap --level 2 (graph with capped repair + budget)");

  // 8 builder ≠ evaluator
  const verifyNodes = graph ? Object.entries(graph.nodes).filter(([, n]) => n.type === "verify" && n.sensors?.length) : [];
  const actToVerify = graph ? Object.values(graph.nodes).filter((n) => n.type === "act").every((n) => graph!.nodes[n.edges?.ok ?? ""]?.type === "verify" || n.sensors?.length) : false;
  add(8, "Is the builder separated from the evaluator (a verify node with sensors grades act's output; the model never approves its own work)?",
    verifyNodes.length && actToVerify ? "pass" : graph ? "partial" : "fail",
    graph ? `verify nodes with sensors: ${verifyNodes.map(([n]) => n).join(", ") || "none"}; every act leads to verify or has sensors: ${actToVerify}` : "no graph",
    graph ? "route every act node's ok edge into a verify node that declares sensors" : "run bootstrap --level 2");

  // 9 policy outside the model
  const policyEvents = events.filter((e) => e.type === "policy.decided").length;
  add(9, "Is MODEL SUGGESTS -> POLICY CHECKS -> TOOL EXECUTES enforced by the runtime (every tool call has a policy decision in the trace)?",
    existsSync(join(harness, "runtime", "core", "policy.ts")) && (policyEvents > 0 || !run) ? (run ? "pass" : "partial") : "fail",
    run ? `${policyEvents} policy decisions in the latest run` : existsSync(join(harness, "runtime")) ? "runtime present, no run to inspect" : "no enforcing runtime",
    existsSync(join(harness, "runtime")) ? "run one contract so the trace shows policy decisions" : "run bootstrap --level 2");

  // 10 traces + receipts
  const receiptPath = run ? join(run, "receipt.json") : undefined;
  let receiptOk = false;
  if (receiptPath && existsSync(receiptPath)) { try { receiptOk = validate(loadSchema("receipt.schema.json"), JSON.parse(readFileSync(receiptPath, "utf8"))).length === 0; } catch { receiptOk = false; } }
  add(10, "Does every run leave a readable trace and a change receipt (context sources, policy version, tools, tests, retries, cost, artifact, rollback point)?",
    receiptOk ? "pass" : run ? "partial" : "fail",
    run ? `latest run has ${events.length} events; receipt ${receiptOk ? "valid" : existsSync(receiptPath!) ? "invalid" : "missing (run did not reach receipt)"}` : "no runs",
    run ? "finish the run (resume --run <dir>) or run `harness/bin/receipt --run <dir> --write`" : "push one contract through harness/bin/run");

  // 11 rollback
  const rollback = events.find((e) => e.type === "rollback.point");
  const rbKind = rollback ? String(rollback.data.kind) : undefined;
  add(11, "Does each run record a rollback point before acting?",
    rbKind === "git" ? "pass" : rollback ? "partial" : "fail",
    rollback ? `rollback.point kind=${rbKind}${rbKind === "git" ? ` head=${String(rollback.data.head).slice(0, 8)}` : ` (${rollback.data.reason ?? ""})`}` : "no rollback.point event",
    rbKind === "none" ? "initialise git in the workspace so the runner can record HEAD + a pre-run patch" : "run one contract; the contract node records the rollback point");

  // 12 failure upgrades
  const upgrades = existsSync(join(harness, "upgrades")) ? readdirSync(join(harness, "upgrades")).filter((f) => f.endsWith(".json")) : [];
  const rulesTable = mapPath ? (readFileSync(mapPath, "utf8").match(/^\|[^|\n]+\|[^|\n]+\|$/gm) ?? []).filter((l) => /validate-graph|sensor|policy\.yaml|TODO/.test(l)).length : 0;
  add(12, "Does failure upgrade the system (each failure class maps to a guide + check change, recorded where the next session finds it)?",
    upgrades.length && rulesTable >= 3 ? "pass" : rulesTable >= 3 || upgrades.length ? "partial" : "fail",
    `${upgrades.length} upgrade proposals in harness/upgrades; ${rulesTable} Guide + Check rows in the map`,
    upgrades.length ? "add the accepted proposals to the Rules table in AGENTS.md" : "after the next failed run: harness/bin/upgrade-from-failure --run harness/runs/<id> --write");

  const score = items.reduce((n, i) => n + (i.status === "pass" ? 1 : i.status === "partial" ? 0.5 : 0), 0);
  const level = graph ? (approveRule === "require_approval" && existsSync(join(harness, "approvals.json")) ? 3 : 2) : policy ? 1 : 0;
  const firstGap = items.find((i) => i.status !== "pass");
  return { target, harness_dir: harness, level_detected: level, score, max: 12, items, smallest_next_upgrade: firstGap ? `Q${firstGap.id}: ${firstGap.fix}` : "none — all twelve pass" };
}
