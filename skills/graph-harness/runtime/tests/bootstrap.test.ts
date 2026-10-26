import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { bootstrap, detect } from "../core/bootstrap.ts";
import { audit } from "../core/audit.ts";
import { propose, inferClass } from "../core/upgrade.ts";
import { loadStructured, loadPolicy, validateGraph } from "../core/graph.ts";
import { FileStore } from "../core/store.ts";

const SCRIPTS = join(import.meta.dirname, "..", "..", "scripts");

function repo(): string {
  const dir = mkdtempSync(join(tmpdir(), "gh-repo-"));
  writeFileSync(join(dir, "package.json"), JSON.stringify({ name: "demo-app", description: "A demo app for the harness smoke test", scripts: { test: "node --test", lint: "eslint ." } }));
  writeFileSync(join(dir, "tsconfig.json"), "{}");
  writeFileSync(join(dir, "README.md"), "# demo\n\nA demo app.\n");
  mkdirSync(join(dir, "docs"), { recursive: true });
  writeFileSync(join(dir, "docs", "architecture.md"), "# arch\n");
  spawnSync("git", ["init", "-q"], { cwd: dir });
  spawnSync("git", ["-c", "user.email=t@t", "-c", "user.name=t", "add", "."], { cwd: dir });
  spawnSync("git", ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"], { cwd: dir });
  return dir;
}

test("detect reads manifests and docs", () => {
  const d = detect(repo());
  assert.equal(d.project_name, "demo-app");
  assert.equal(d.test_cmd, "npm test");
  assert.equal(d.lint_cmd, "npm run lint");
  assert.equal(d.types_cmd, "npx tsc --noEmit");
  assert.ok(d.docs.some((x) => x.path === "docs/architecture.md"));
  assert.equal(d.is_git, true);
});

test("level 1 writes map + contract + policy and nothing from level 2", () => {
  const dir = repo();
  const r = bootstrap({ target: dir, level: 1, task_class: "code" });
  assert.ok(r.written.includes("AGENTS.md"));
  assert.ok(r.written.includes("harness/policy.yaml"));
  assert.ok(r.written.includes("harness/schemas/contract.schema.json"));
  assert.ok(!existsSync(join(dir, "harness", "graph.yaml")));
  assert.ok(!existsSync(join(dir, "harness", "runtime")));
  const agents = readFileSync(join(dir, "AGENTS.md"), "utf8");
  assert.match(agents, /demo-app/);
  assert.match(agents, /`npm test`/);
  assert.match(agents, /TODO at level 1/);
  assert.match(agents, /docs\/architecture\.md/);
  const a = audit(dir);
  assert.equal(a.level_detected, 1);
  assert.ok(a.score >= 2 && a.score < 6, `L1 score ${a.score}`);
  assert.ok(a.items.every((i) => i.status === "pass" || i.fix.length > 0), "every gap has a fix");
  // rerun does not overwrite: existing files are skipped and the map goes to harness/AGENTS.harness.md for merging
  const r2 = bootstrap({ target: dir, level: 1, task_class: "code" });
  assert.ok(r2.skipped.some((s) => s.path === "harness/policy.yaml"));
  assert.ok(r2.written.includes("harness/AGENTS.harness.md"));
  assert.ok(r2.notes.some((n) => /merge/.test(n)));
  assert.match(readFileSync(join(dir, "AGENTS.md"), "utf8"), /demo-app/, "original map untouched");
});

test("level 2 -> 3 upgrade path: graph validates, vendored bin runs a contract, audit climbs, upgrade proposes", () => {
  const dir = repo();
  bootstrap({ target: dir, level: 1, task_class: "code" });
  const l2 = bootstrap({ target: dir, level: 2, task_class: "code", force: true });
  assert.ok(l2.written.includes("harness/graph.yaml"));
  assert.ok(existsSync(join(dir, "harness", "runtime", "core", "runner.ts")));
  assert.ok(!existsSync(join(dir, "harness", "runtime", "tests")), "tests are not vendored");
  assert.ok(existsSync(join(dir, "harness", "bin", "run")));
  const policy2 = readFileSync(join(dir, "harness", "policy.yaml"), "utf8");
  assert.match(policy2, /approve: deny/);
  const graph = loadStructured(join(dir, "harness", "graph.yaml")) as any;
  const v = validateGraph(graph, loadPolicy(join(dir, "harness", "policy.yaml")));
  assert.deepEqual(v.errors, []);
  assert.equal(graph.sensors.tests.cmd, "npm test");
  assert.equal(graph.sensors.lint.cmd, "npm run lint");
  assert.equal(graph.sensors.types.cmd, "npx tsc --noEmit");

  // Make the sensors runnable in this throwaway repo, then push a contract through the VENDORED binaries.
  const g = readFileSync(join(dir, "harness", "graph.yaml"), "utf8").replace("cmd: npm test", 'cmd: "test -f out/result.md"').replace("cmd: npm run lint", 'cmd: "true"').replace("cmd: npx tsc --noEmit", 'cmd: "true"');
  writeFileSync(join(dir, "harness", "graph.yaml"), g);
  const vg = spawnSync(join(dir, "harness", "bin", "validate-graph"), ["--dir", join(dir, "harness")], { encoding: "utf8" });
  assert.equal(vg.status, 0, vg.stdout + vg.stderr);
  const contract = { ...JSON.parse(readFileSync(join(dir, "harness", "contracts", "example.json"), "utf8")), id: "first", done_when: [{ check: "out/result.md exists", sensor: "output_exists" }, { check: "`test -f out/result.md` exits 0", sensor: "tests" }] };
  writeFileSync(join(dir, "harness", "contracts", "first.json"), JSON.stringify(contract));
  const run = spawnSync(join(dir, "harness", "bin", "run"), ["--dir", join(dir, "harness"), "--contract", join(dir, "harness", "contracts", "first.json"), "--run-id", "first", "--quiet"], { encoding: "utf8", cwd: dir });
  assert.equal(run.status, 0, run.stdout + run.stderr);
  assert.equal(JSON.parse(run.stdout).status, "completed");
  assert.ok(existsSync(join(dir, "out", "result.md")));
  const events = new FileStore(join(dir, "harness", "runs", "first")).events();
  assert.equal(events.find((e) => e.type === "rollback.point")?.data.kind, "git");

  const a2 = audit(dir);
  assert.equal(a2.level_detected, 2);
  assert.ok(a2.score >= 9, `L2 score ${a2.score}: ${JSON.stringify(a2.items.filter((i) => i.status !== "pass").map((i) => [i.id, i.evidence]))}`);
  assert.equal(a2.items[3].status, "partial", "Q4 is partial at L2 (approve tier is deny)");

  // A failed run -> upgrade proposal
  const fail = spawnSync(join(dir, "harness", "bin", "run"), ["--dir", join(dir, "harness"), "--contract", join(dir, "harness", "contracts", "first.json"), "--run-id", "loop", "--inject-failure", "tests:9", "--quiet"], { encoding: "utf8", cwd: dir });
  assert.equal(fail.status, 2, "paused at human_review");
  const up = spawnSync(join(dir, "harness", "bin", "upgrade-from-failure"), ["--run", join(dir, "harness", "runs", "loop"), "--write"], { encoding: "utf8", cwd: dir });
  assert.equal(up.status, 0, up.stdout + up.stderr);
  const proposal = JSON.parse(up.stdout);
  assert.equal(proposal.failure_class, "repeated_loop");
  assert.equal(proposal.inferred, true);
  assert.ok(proposal.evidence.some((e: any) => e.type === "retry.exhausted"));
  assert.ok(proposal.guide.text.length > 20 && proposal.check.spec);
  assert.ok(existsSync(proposal.written));
  const unsafe = propose(new FileStore(join(dir, "harness", "runs", "loop")).events(), "unsafe_action");
  assert.equal(unsafe.failure_class, "unsafe_action");
  assert.equal(unsafe.inferred, false);

  const l3 = bootstrap({ target: dir, level: 3, task_class: "code", force: true });
  assert.ok(l3.written.includes("harness/approvals.json"));
  assert.match(readFileSync(join(dir, "harness", "policy.yaml"), "utf8"), /approve: require_approval/);
  const a3 = audit(dir);
  assert.equal(a3.level_detected, 3);
  assert.ok(a3.score > a2.score, `L3 ${a3.score} > L2 ${a2.score}`);
  const md = spawnSync(join(SCRIPTS, "audit"), ["--target", dir, "--markdown"], { encoding: "utf8" });
  assert.match(md.stdout, /Score \*\*/);
});

test("inferClass picks the most specific class present", () => {
  const mk = (type: string, data: Record<string, unknown>, seq: number) => ({ seq, ts: "t", run_id: "r", type: type as any, data });
  assert.equal(inferClass([mk("run.started", {}, 1), mk("policy.decided", { decision: "deny", tool: "x" }, 2)]).cls, "unsafe_action");
  assert.equal(inferClass([mk("run.started", {}, 1), mk("sensor.ran", { pass: false, name: "tests" }, 2)]).cls, "bad_output");
  assert.equal(inferClass([mk("run.started", {}, 1), mk("context.loaded", { missing: ["docs/x.md"] }, 2)]).cls, "missing_context");
  assert.equal(inferClass([mk("run.started", {}, 1), mk("run.paused", {}, 2)]).cls, "lost_decision");
  assert.equal(inferClass([mk("run.started", {}, 1)]).cls, "unknown_failure");
});
