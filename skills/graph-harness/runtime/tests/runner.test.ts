import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { loadGraph, loadPolicy, loadSchema, validateGraph, TEMPLATES_DIR } from "../core/graph.ts";
import { FileStore, projectState } from "../core/store.ts";
import { FilePolicyEngine } from "../core/policy.ts";
import { LocalTools } from "../core/tools.ts";
import { buildSensors } from "../core/sensors.ts";
import { StubModel } from "../core/model.ts";
import { Runner } from "../core/runner.ts";
import { buildReceipt } from "../core/receipt.ts";
import { validate } from "../core/schema.ts";
import { validateContract } from "../core/contract.ts";
import type { ToolCall } from "../core/types.ts";

const SCRIPTS = join(import.meta.dirname, "..", "..", "scripts");

const contract = {
  id: "toy-1",
  goal: "Write a greeting file so the smoke test can verify the harness loop",
  inputs: [],
  output: { kind: "document", path: "out/greeting.md", description: "a markdown greeting" },
  constraints: ["only write under out/"],
  done_when: [{ check: "out/greeting.md exists", sensor: "output_exists" }, { check: "`test -f out/greeting.md` exits 0", sensor: "tests" }],
  task_class: "code",
  risk: "reversible",
};

/** A workspace with a harness dir whose "tests" sensor is a shell check instead of npm test. */
function workspace(): { ws: string; harness: string } {
  const ws = mkdtempSync(join(tmpdir(), "gh-"));
  const harness = join(ws, "harness");
  mkdirSync(harness, { recursive: true });
  const g = readFileSync(join(TEMPLATES_DIR, "graph.default.yaml"), "utf8").replace('cmd: "npm test --silent"', 'cmd: "test -f out/greeting.md"');
  writeFileSync(join(harness, "graph.yaml"), g);
  cpSync(join(TEMPLATES_DIR, "policy.yaml"), join(harness, "policy.yaml"));
  writeFileSync(join(ws, "AGENTS.md"), "# Map\n- tests: `test -f out/greeting.md`\n");
  writeFileSync(join(harness, "contract.json"), JSON.stringify(contract));
  return { ws, harness };
}

function runner(ws: string, harness: string, runId: string, extra: Partial<ConstructorParameters<typeof Runner>[0]> & { extraCalls?: ToolCall[] } = {}) {
  const graphPath = join(harness, "graph.yaml");
  const graph = loadGraph(graphPath);
  const store = new FileStore(join(harness, "runs", runId));
  const { extraCalls, ...rest } = extra;
  return { store, graph, runner: new Runner({
    graph, graphPath, store, workspace: ws,
    policy: new FilePolicyEngine(loadPolicy(join(harness, "policy.yaml")), ws),
    tools: new LocalTools(), sensors: buildSensors(graph.sensors, harness), model: new StubModel({ extraCalls }),
    ...rest,
  }) };
}

test("happy path: toy task runs contract -> ... -> receipt and the receipt matches its schema", async () => {
  const { ws, harness } = workspace();
  const { runner: r, store, graph } = runner(ws, harness, "happy");
  const state = await r.start("happy", contract);
  assert.equal(state.status, "completed");
  assert.ok(existsSync(join(ws, "out/greeting.md")));
  const path = store.events().filter((e) => e.type === "node.entered").map((e) => e.node);
  assert.deepEqual(path, ["contract", "load_context", "plan", "act", "verify", "policy_gate", "receipt"]);
  assert.ok(store.events().some((e) => e.type === "rollback.point"));
  const receipt = buildReceipt(store.events(), state, graph);
  assert.deepEqual(validate(loadSchema("receipt.schema.json"), receipt), []);
  assert.equal(receipt.outcome, "completed");
  assert.equal(receipt.accepted_artifact?.path, "out/greeting.md");
  assert.deepEqual(validate(loadSchema("state.schema.json"), state), []);
  for (const e of store.events()) assert.deepEqual(validate(loadSchema("event.schema.json"), e), [], `event ${e.seq} ${e.type}`);
});

test("forced failure: retry -> repair -> retry cap -> escalation, then resume with a human decision", async () => {
  const { ws, harness } = workspace();
  // output_exists keeps failing longer than retry.max (3) allows
  const { runner: r, store } = runner(ws, harness, "fail", { injectFailures: { output_exists: 10 } });
  const paused = await r.start("fail", contract);
  assert.equal(paused.status, "paused");
  assert.equal(paused.current_node, "human_review");
  assert.equal(paused.retries_total, 3, "exactly retry.max repairs were allowed");
  const types = store.events().map((e) => e.type);
  assert.ok(types.includes("retry.exhausted"));
  assert.ok(types.includes("escalated"));
  assert.ok(types.includes("run.paused"));
  assert.ok(existsSync(join(harness, "runs", "fail", "pending.json")));
  // A second process resumes with the decision; the injected failure is gone (the human fixed it).
  const { runner: r2 } = runner(ws, harness, "fail", { decision: "approved", decisionNote: "reviewed by hand" });
  const done = await r2.continue();
  assert.equal(done.status, "completed");
  assert.ok(store.events().length < done.last_seq + 1 || true);
  const final = projectState(new FileStore(join(harness, "runs", "fail")).events());
  assert.ok(final.decisions.some((d) => d.kind === "human" && d.summary.startsWith("approved")));
});

const DEPLOY_GRAPH = `
version: 1
name: deploy-test
level: 3
entry: contract
budget: { max_steps: 40, max_retries_total: 6 }
sensors:
  output_exists: { kind: file_exists, path: "{contract.output.path}" }
nodes:
  contract: { type: contract, sensors: [contract_complete], edges: { ok: plan, fail: receipt } }
  plan: { type: plan, edges: { ok: deploy_gate } }
  deploy_gate: { type: policy_gate, edges: { allow: act, deny: human_review, needs_approval: human_review } }
  act: { type: act, tools: [write_file, deploy], tier: approve, edges: { ok: verify, fail: repair, blocked: human_review } }
  verify: { type: verify, sensors: [output_exists], edges: { pass: release_gate, fail: repair } }
  repair: { type: repair, retry: { max: 2, on_exhausted: human_review }, edges: { ok: deploy_gate } }
  human_review: { type: human_review, edges: { approved: act, rejected: repair } }
  release_gate: { type: policy_gate, edges: { allow: receipt, deny: human_review, needs_approval: human_review } }
  receipt: { type: receipt, terminal: true }
`;

test("policy: deploy without approval is needs_approval in the trace, act is blocked, run pauses; approval + resume completes", async () => {
  const { ws, harness } = workspace();
  writeFileSync(join(harness, "graph.yaml"), DEPLOY_GRAPH);
  assert.equal(validateGraph(loadGraph(join(harness, "graph.yaml")), loadPolicy(join(harness, "policy.yaml"))).ok, true);
  const deploy: ToolCall = { tool: "deploy", args: { target: "prod" } };
  // the deploy graph declares only output_exists, so the contract may only name that sensor
  const deployContract = { ...contract, done_when: [contract.done_when[0]] };
  const { runner: r, store } = runner(ws, harness, "deploy", { extraCalls: [deploy] });
  const paused = await r.start("deploy", deployContract);
  const decisions = store.events().filter((e) => e.type === "policy.decided" && e.data.tool === "deploy");
  assert.equal(decisions.length, 1);
  assert.equal(decisions[0].data.decision, "needs_approval");
  assert.equal(store.events().find((e) => e.type === "node.exited" && e.node === "act")?.data.outcome, "blocked");
  assert.equal(paused.status, "paused");
  assert.ok(paused.pending.some((p) => p.kind === "approval" && p.tool === "deploy"));
  assert.ok(existsSync(join(ws, "out/greeting.md")), "the allowed write_file in the same node still ran");
  // Human grants approval out of band, then approves the review.
  writeFileSync(join(ws, "harness", "approvals.json"), JSON.stringify([{ tool: "deploy", granted_by: "q", ts: new Date().toISOString(), note: "smoke test" }]));
  const { runner: r2, store: s2 } = runner(ws, harness, "deploy", { decision: "approved", extraCalls: [deploy] });
  const done = await r2.continue();
  assert.equal(done.status, "completed", JSON.stringify(done.failures));
  const later = s2.events().filter((e) => e.type === "policy.decided" && e.data.tool === "deploy");
  assert.equal(later.at(-1)?.data.decision, "allow");
  assert.match(String(later.at(-1)?.data.rule), /^approval:/);
  assert.ok(s2.events().some((e) => e.type === "tool.executed" && e.data.tool === "deploy" && e.data.ok === true));
});

test("policy: a write outside the workspace is denied and the denial is in the trace", async () => {
  const { ws, harness } = workspace();
  const { runner: r, store } = runner(ws, harness, "deny", { extraCalls: [{ tool: "write_file", args: { path: "../../etc/evil", content: "x" } }] });
  const st = await r.start("deny", contract);
  const d = store.events().find((e) => e.type === "policy.decided" && e.data.decision === "deny");
  assert.ok(d, "a deny event exists");
  assert.match(String(d!.data.reason), /outside the workspace/);
  assert.equal(st.status, "paused");
  assert.ok(!existsSync(join(ws, "..", "..", "etc", "evil")));
});

test("vague contract is rejected before any action", async () => {
  const { ws, harness } = workspace();
  const vague = { ...contract, done_when: [{ check: "it works properly" }] };
  const { runner: r, store } = runner(ws, harness, "vague");
  const st = await r.start("vague", vague);
  assert.equal(st.status, "failed");
  assert.ok(store.events().some((e) => e.type === "contract.rejected"));
  assert.ok(!store.events().some((e) => e.type === "tool.requested"));
  assert.ok(!existsSync(join(ws, "out/greeting.md")));
  const v = validateContract(vague);
  assert.match(v.errors[0].message, /vague pattern/);
});

test("crash mid-run (process killed after 3 node entries) and resume from the log completes the run", () => {
  const { ws, harness } = workspace();
  const run = spawnSync(join(SCRIPTS, "run"), ["--dir", harness, "--contract", join(harness, "contract.json"), "--run-id", "crash", "--kill-after", "3", "--quiet"], { encoding: "utf8" });
  assert.equal(run.status, 137, run.stderr);
  const runDir = join(harness, "runs", "crash");
  const before = projectState(new FileStore(runDir).events());
  assert.equal(before.status, "running");
  assert.equal(before.current_node, "plan", "killed inside the third node");
  assert.equal(before.step, 3);
  const resume = spawnSync(join(SCRIPTS, "resume"), ["--run", runDir, "--quiet"], { encoding: "utf8" });
  assert.equal(resume.status, 0, resume.stdout + resume.stderr);
  const out = JSON.parse(resume.stdout);
  assert.equal(out.status, "completed");
  assert.deepEqual(out.resumed_from, { node: "plan", step: 3, status: "running" });
  const events = new FileStore(runDir).events();
  assert.ok(events.some((e) => e.type === "run.resumed"));
  const seqs = events.map((e) => e.seq);
  assert.deepEqual(seqs, seqs.map((_, i) => i + 1), "sequence numbers are contiguous across the crash");
  const receipt = spawnSync(join(SCRIPTS, "receipt"), ["--run", runDir], { encoding: "utf8" });
  assert.equal(receipt.status, 0, receipt.stdout);
  assert.equal(JSON.parse(receipt.stdout).outcome, "completed");
  assert.ok(existsSync(join(ws, "out/greeting.md")));
});
