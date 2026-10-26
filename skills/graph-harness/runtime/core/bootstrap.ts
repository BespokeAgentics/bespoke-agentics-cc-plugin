// bootstrap: scaffold the harness into a target repo at a chosen maturity level.
// Deterministic: inspects the repo (manifests, docs, scripts), fills templates, writes only what
// the level needs, never overwrites without --force. Output is a JSON manifest of what was written.

import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync, chmodSync } from "node:fs";
import { basename, dirname, join, relative, resolve } from "node:path";
import { parseYaml, toYaml } from "./yaml.ts";
import { TEMPLATES_DIR } from "./graph.ts";
import type { Graph, TaskClass } from "./types.ts";

export const RUNTIME_DIR = join(import.meta.dirname, "..");

export interface Detected {
  project_name: string;
  purpose: string;
  languages: string[];
  test_cmd?: string; lint_cmd?: string; types_cmd?: string;
  docs: { label: string; path: string }[];
  ci: string[];
  is_git: boolean;
  existing_map?: string;
}

const DOC_CANDIDATES: [string, string][] = [
  ["README", "README.md"], ["Contributing", "CONTRIBUTING.md"], ["Architecture", "ARCHITECTURE.md"], ["Architecture", "docs/architecture.md"],
  ["Testing", "TESTING.md"], ["Testing", "docs/testing.md"], ["Security", "SECURITY.md"], ["Product", "docs/product.md"], ["Docs", "docs"],
  ["Decisions (ADRs)", "docs/adr"], ["Decisions (ADRs)", "adr"], ["Wiki", "wiki"], ["Plans", "plans"], ["Plans", "docs/plans"], ["Claude guide", "CLAUDE.md"],
];

export function detect(target: string): Detected {
  const d: Detected = { project_name: basename(resolve(target)), purpose: "", languages: [], docs: [], ci: [], is_git: existsSync(join(target, ".git")) };
  const pkgPath = join(target, "package.json");
  if (existsSync(pkgPath)) {
    try {
      const pkg = JSON.parse(readFileSync(pkgPath, "utf8"));
      d.languages.push(existsSync(join(target, "tsconfig.json")) ? "typescript" : "javascript");
      if (pkg.name) d.project_name = String(pkg.name);
      if (pkg.description) d.purpose = String(pkg.description);
      const s = pkg.scripts ?? {};
      const runner = existsSync(join(target, "bun.lock")) || existsSync(join(target, "bun.lockb")) ? "bun run" : existsSync(join(target, "pnpm-lock.yaml")) ? "pnpm run" : "npm run";
      if (s.test) d.test_cmd = `${runner === "npm run" ? "npm" : runner.split(" ")[0]} test`;
      for (const k of ["lint", "check"]) if (s[k] && !d.lint_cmd) d.lint_cmd = `${runner} ${k}`;
      for (const k of ["typecheck", "type-check", "types", "tsc"]) if (s[k] && !d.types_cmd) d.types_cmd = `${runner} ${k}`;
      if (!d.types_cmd && existsSync(join(target, "tsconfig.json"))) d.types_cmd = "npx tsc --noEmit";
    } catch { /* unreadable package.json: fall through */ }
  }
  if (existsSync(join(target, "pyproject.toml")) || existsSync(join(target, "requirements.txt")) || existsSync(join(target, "setup.py"))) {
    d.languages.push("python");
    d.test_cmd ??= existsSync(join(target, "uv.lock")) ? "uv run pytest -q" : "pytest -q";
    d.lint_cmd ??= "ruff check .";
    if (existsSync(join(target, "pyproject.toml"))) {
      const py = readFileSync(join(target, "pyproject.toml"), "utf8");
      const m = py.match(/^description\s*=\s*"([^"]+)"/m); if (m && !d.purpose) d.purpose = m[1];
      const n = py.match(/^name\s*=\s*"([^"]+)"/m); if (n) d.project_name = n[1];
      if (/\bmypy\b/.test(py)) d.types_cmd ??= "mypy .";
      if (/\bpyright\b/.test(py)) d.types_cmd ??= "pyright";
    }
  }
  if (existsSync(join(target, "Cargo.toml"))) { d.languages.push("rust"); d.test_cmd ??= "cargo test"; d.lint_cmd ??= "cargo clippy -- -D warnings"; d.types_cmd ??= "cargo check"; }
  if (existsSync(join(target, "go.mod"))) { d.languages.push("go"); d.test_cmd ??= "go test ./..."; d.lint_cmd ??= "go vet ./..."; d.types_cmd ??= "go build ./..."; }
  if (existsSync(join(target, "Makefile"))) {
    const mk = readFileSync(join(target, "Makefile"), "utf8");
    if (/^test:/m.test(mk)) d.test_cmd ??= "make test";
    if (/^lint:/m.test(mk)) d.lint_cmd ??= "make lint";
  }
  for (const [label, p] of DOC_CANDIDATES) {
    if (existsSync(join(target, p)) && !d.docs.some((x) => x.label === label)) d.docs.push({ label, path: p });
  }
  if (!d.purpose && existsSync(join(target, "README.md"))) {
    const para = readFileSync(join(target, "README.md"), "utf8").split(/\n\s*\n/).map((s) => s.trim()).find((s) => s && !s.startsWith("#") && !s.startsWith("[") && !s.startsWith("!"));
    if (para) d.purpose = para.replace(/\s+/g, " ").slice(0, 300);
  }
  if (!d.purpose) d.purpose = "TODO: one paragraph on what this project is for and who uses it.";
  const wf = join(target, ".github", "workflows");
  if (existsSync(wf)) d.ci = readdirSync(wf).filter((f) => /\.ya?ml$/.test(f)).map((f) => `.github/workflows/${f}`);
  if (existsSync(join(target, "AGENTS.md"))) d.existing_map = "AGENTS.md";
  return d;
}

export interface BootstrapOptions { target: string; level: 1 | 2 | 3; task_class: TaskClass; force?: boolean; dryRun?: boolean; name?: string }
export interface BootstrapResult { level: number; task_class: TaskClass; harness_dir: string; detected: Detected; written: string[]; skipped: { path: string; reason: string }[]; notes: string[]; next: string[] }

export function sensorsFor(task_class: TaskClass, d: Detected): Record<string, any> {
  const load = (f: string) => parseYaml(readFileSync(join(TEMPLATES_DIR, "sensors", f), "utf8")) as Record<string, any>;
  const fill = (s: Record<string, any>) => {
    for (const [name, def] of Object.entries(s)) {
      if (typeof def.cmd !== "string") continue;
      const sub: Record<string, string | undefined> = { "{{test_cmd}}": d.test_cmd, "{{lint_cmd}}": d.lint_cmd, "{{types_cmd}}": d.types_cmd, "{{ui_render_cmd}}": undefined, "{{ui_screenshot_cmd}}": undefined, "{{data_range_cmd}}": undefined };
      for (const [ph, val] of Object.entries(sub)) {
        if (!def.cmd.includes(ph)) continue;
        if (val) def.cmd = def.cmd.replace(ph, val);
        else { def.cmd = "false"; def.todo = `${name}: no command detected for ${ph.replace(/[{}]/g, "")}; set cmd in harness/graph.yaml`; }
      }
    }
    return s;
  };
  const classes: Record<TaskClass, string[]> = { code: ["code.yaml"], ui: ["code.yaml", "ui.yaml"], research: ["research.yaml"], data: ["data.yaml", "code.yaml"], mixed: ["code.yaml"] };
  let out: Record<string, any> = {};
  for (const f of classes[task_class]) out = { ...out, ...fill(load(f)) };
  if (task_class === "ui" || task_class === "data") delete out.lint; // keep the verify set small; add back by hand
  return out;
}

export function buildGraph(level: 1 | 2 | 3, task_class: TaskClass, d: Detected): Graph {
  const g = parseYaml(readFileSync(join(TEMPLATES_DIR, "graph.default.yaml"), "utf8")) as Graph;
  g.level = level === 1 ? 2 : level;
  g.name = `${task_class}-l${g.level}`;
  g.sensors = sensorsFor(task_class, d);
  const verify = g.nodes.verify;
  verify.sensors = Object.keys(g.sensors).filter((s) => s !== "lint" || task_class === "code");
  if (task_class === "research") { verify.sensors = Object.keys(g.sensors); }
  return g;
}

function policyFor(level: 1 | 2 | 3): string {
  const text = readFileSync(join(TEMPLATES_DIR, "policy.yaml"), "utf8");
  // Level 2 has no approval mechanism yet: irreversible tools are simply refused.
  return level === 2 ? text.replace("  approve: require_approval", "  approve: deny   # level 2: no approval mechanism; bootstrap --level 3 adds approvals.json") : text;
}

export function renderAgentsMd(d: Detected, level: 1 | 2 | 3, task_class: TaskClass): string {
  let t = readFileSync(join(TEMPLATES_DIR, "AGENTS.md"), "utf8");
  const mapRows = [
    ...d.docs.map((x) => `| ${x.label} | \`${x.path}\` |`),
    ...(d.ci.length ? [`| CI | ${d.ci.map((c) => `\`${c}\``).join(", ")} |`] : []),
    `| Harness (contracts, policy${level >= 2 ? ", graph, runs" : ""}) | \`harness/\` |`,
  ];
  const cmdRows = [
    d.test_cmd ? `| Tests | \`${d.test_cmd}\` | exit code + output (sensor \`tests\`) |` : "| Tests | TODO: no test command detected | — |",
    d.types_cmd ? `| Types | \`${d.types_cmd}\` | exit code (sensor \`types\`) |` : "",
    d.lint_cmd ? `| Lint | \`${d.lint_cmd}\` | exit code (sensor \`lint\`) |` : "",
    level >= 2 ? "| Validate the graph | `harness/bin/validate-graph --dir harness` | JSON report, exit 1 on any gap |" : "",
    level >= 2 ? "| Run a task | `harness/bin/run --dir harness --contract harness/contracts/<id>.json` | `harness/runs/<id>/events.jsonl`, `receipt.json` |" : "",
    level >= 2 ? "| Resume after a crash or review | `harness/bin/resume --run harness/runs/<id> [--decision approved]` | continues from the event log |" : "",
    "| Audit the harness | `harness/bin/audit --target .` | 12-question score with a fix per gap |",
  ].filter(Boolean);
  const harnessRows = [
    `- Policy: \`harness/policy.yaml\` (tool contracts + tiers).`,
    level >= 2 ? `- Graph: \`harness/graph.yaml\` — contract → load_context → plan → act → verify → policy_gate → receipt; repair is capped; human_review is the escalation.` : `- Level 1 has no runner: the policy is prose until \`bootstrap --level 2\` installs the runtime that enforces it.`,
    level >= 2 ? `- State: \`harness/runs/<id>/events.jsonl\` is the system of record; \`state.json\` is a projection; \`receipt.json\` is the change receipt.` : "",
    level >= 3 ? `- Approvals: \`harness/approvals.json\` — a record per approved irreversible tool call (\`{ tool, granted_by, ts }\`).` : "",
  ].filter(Boolean);
  const ruleRows = [
    level === 1 ? "| Policy tiers are enforced by the runtime, not the prompt | TODO at level 1: prose only. `bootstrap --level 2` installs the enforcing runtime. |" : "",
    task_class === "ui" ? "| UI changes ship with a screenshot | sensor `screenshot` in harness/graph.yaml (TODO until `ui_screenshot_cmd` is wired) |" : "",
    task_class === "research" ? "| Every claim cites a source | sensor `sources_present`; `claims_cited` is TODO and routes to human_review |" : "",
    task_class === "data" ? "| Output matches the declared schema | sensor `schema` (json_schema) in harness/graph.yaml |" : "",
  ].filter(Boolean);
  const guides = [`- **${task_class}** tasks: sensors in \`harness/graph.yaml\` § sensors; guide in \`harness/guides/${task_class}.md\`.`];
  t = t.replace("{{project_name}}", d.project_name).replace("{{purpose}}", d.purpose).replace("{{level}}", String(level))
    .replace("{{map_rows}}", mapRows.join("\n")).replace("{{command_rows}}", cmdRows.join("\n")).replace("{{harness_rows}}", harnessRows.join("\n"))
    .replace("{{rule_rows}}\n", ruleRows.length ? ruleRows.join("\n") + "\n" : "").replace("{{task_guides}}", guides.join("\n"));
  return t;
}

function guideFor(task_class: TaskClass, d: Detected): string {
  const sensors: Record<TaskClass, string> = {
    code: "tests + types + lint", ui: "render + screenshot + inspection (plus the code sensors)", research: "sources present + claims cited + contradictions",
    data: "schema + ranges + freshness (plus tests)", mixed: "tests + types + lint; add ui/data sensors per task",
  };
  const done: Record<TaskClass, string> = {
    code: '{ "check": "`' + (d.test_cmd ?? "npm test") + '` exits 0", "sensor": "tests" }',
    ui: '{ "check": "screenshot of /route saved to out/route.png", "sensor": "screenshot" }',
    research: '{ "check": "out/report.md has a Sources section with >= 3 URLs", "sensor": "sources_present" }',
    data: '{ "check": "out/data.json matches schemas/output.schema.json", "sensor": "schema" }',
    mixed: '{ "check": "`' + (d.test_cmd ?? "npm test") + '` exits 0", "sensor": "tests" }',
  };
  return `# ${task_class} tasks\n\nLoaded by the harness when a contract's task_class is \`${task_class}\`. Keep it short; link, do not duplicate.\n\n## Sensors\n\n${sensors[task_class]} — declared in \`harness/graph.yaml\` under \`sensors:\`; the \`verify\` node runs them.\n\n## A verifiable done_when\n\n\`\`\`json\n${done[task_class]}\n\`\`\`\n\n## Guides to load\n\n${d.docs.map((x) => `- \`${x.path}\``).join("\n") || "- (none detected; add links here)"}\n`;
}

function harnessReadme(level: 1 | 2 | 3, task_class: TaskClass): string {
  return `# Harness (level ${level}, task class ${task_class})

The model is the reasoning engine; this directory is the operating system around it.

| Path | What it is |
|---|---|
| \`policy.yaml\` | tool contracts + permission tiers (enforced by the runtime from level 2) |
| \`contracts/\` | one JSON contract per task (schema: \`schemas/contract.schema.json\`) |
${level >= 2 ? "| `graph.yaml` | the typed node graph; `bin/validate-graph` must pass before a run |\n| `runs/<id>/` | `events.jsonl` (append-only history), `state.json` (projection), `receipt.json`, `rollback/` |\n| `runtime/` | vendored reference runner (TypeScript, Node ≥ 22.18, no dependencies) |\n| `bin/` | `validate-graph`, `run`, `resume`, `receipt`, `audit`, `upgrade-from-failure` |\n| `sensors/` | custom sensor modules |\n" : ""}${level >= 3 ? "| `approvals.json` | approval records for approve-tier tools (`deploy`, `delete_path`) |\n" : ""}
## Moving up a level

- **L1 → L2** (guide + tools → structured state + sensors + bounded loop): run
  \`bootstrap --target . --level 2 --task-class ${task_class}\`. It adds \`graph.yaml\`, the vendored runtime,
  \`bin/\`, and \`runs/\`. Then \`bin/validate-graph --dir harness\` and push one contract through \`bin/run\`.
  Do this when a task has failed for lack of evidence (nobody ran the tests) or has looped.
- **L2 → L3** (→ permissions + traces + recovery + human gates): run \`bootstrap --target . --level 3 ...\`.
  It switches the \`approve\` tier from \`deny\` to \`require_approval\`, adds \`approvals.json\` and the
  receipt schema. Do this when a task must touch something irreversible or shared (deploy, delete, send).
- Never generate L3 machinery for an L1 task: the harness should be smaller than the failure surface it controls.

## Failure taxonomy

| Failure | Harness change |
|---|---|
| missing context | map / retrieval rule in AGENTS.md |
| wrong tool | better tool description or routing in policy.yaml |
| bad output | validator or stronger contract (a sensor) |
| repeated loop | retry cap + escalation (graph.yaml) |
| unsafe action | permission gate (policy.yaml tier) |
| lost decision | durable state (events.jsonl) |
| unknown failure | tracing + evidence capture |

\`bin/upgrade-from-failure --run runs/<id>\` reads a trace and proposes the Guide + Check pair.
`;
}

export function bootstrap(o: BootstrapOptions): BootstrapResult {
  const target = resolve(o.target);
  const harness = join(target, "harness");
  const d = detect(target);
  if (o.name) d.project_name = o.name;
  const res: BootstrapResult = { level: o.level, task_class: o.task_class, harness_dir: harness, detected: d, written: [], skipped: [], notes: [], next: [] };
  const files: { path: string; content: string; exec?: boolean }[] = [];
  const put = (p: string, content: string, exec = false) => files.push({ path: join(harness, p), content, exec });

  // Level 1: map + contract + policy
  const agents = renderAgentsMd(d, o.level, o.task_class);
  if (d.existing_map && !o.force) {
    files.push({ path: join(harness, "AGENTS.harness.md"), content: agents });
    res.notes.push("AGENTS.md already exists; wrote harness/AGENTS.harness.md — merge its Harness and Rules sections into AGENTS.md (or rerun with --force to overwrite)");
  } else files.push({ path: join(target, "AGENTS.md"), content: agents });
  put("policy.yaml", policyFor(o.level));
  put("schemas/contract.schema.json", readFileSync(join(TEMPLATES_DIR, "contract.schema.json"), "utf8"));
  put("contracts/example.json", JSON.stringify({
    id: "example-1", goal: "Replace this with the first real task; one sentence on what is true when it is done", inputs: ["AGENTS.md"],
    output: { kind: o.task_class === "ui" ? "ui" : o.task_class === "mixed" ? "mixed" : o.task_class, path: "out/result.md", description: "describe the artifact" },
    constraints: ["only write under out/"], done_when: [{ check: "out/result.md exists", sensor: "output_exists" }], task_class: o.task_class, risk: "reversible",
  }, null, 2) + "\n");
  put(`guides/${o.task_class}.md`, guideFor(o.task_class, d));
  put("README.md", harnessReadme(o.level, o.task_class));

  // Level 2: graph + runtime + runs
  if (o.level >= 2) {
    const g = buildGraph(o.level, o.task_class, d);
    put("graph.yaml", `# Generated by graph-harness bootstrap (level ${o.level}, task class ${o.task_class}). Semantics: harness/runtime/README.md.\n` + toYaml(g) + "\n");
    for (const s of ["event.schema.json", "state.schema.json", "graph.schema.json", "policy.schema.json"]) put(`schemas/${s}`, readFileSync(join(TEMPLATES_DIR, s), "utf8"));
    put("sensors/custom.example.ts", readFileSync(join(TEMPLATES_DIR, "sensors", "custom.example.ts"), "utf8"));
    put("runs/.gitkeep", "");
    put(".gitignore", "runs/*/\n!runs/.gitkeep\ndeploys.log\n");
    for (const bin of ["validate-graph", "run", "resume", "receipt", "audit", "upgrade-from-failure"]) {
      put(`bin/${bin}`, `#!/bin/sh\nHERE="$(cd "$(dirname "$0")" && pwd)"\nexec node --no-warnings "$HERE/../runtime/cli/${bin}.ts" "$@"\n`, true);
    }
    const todo = Object.entries(g.sensors ?? {}).filter(([, s]: [string, any]) => s.todo).map(([n]) => n);
    if (todo.length) res.notes.push(`sensors with TODO (they fail until wired): ${todo.join(", ")}`);
  }
  // Level 3: approvals + receipt schema
  if (o.level >= 3) {
    put("approvals.json", "[]\n");
    put("schemas/receipt.schema.json", readFileSync(join(TEMPLATES_DIR, "receipt.schema.json"), "utf8"));
  }

  for (const f of files) {
    const rel = relative(target, f.path);
    if (existsSync(f.path) && !o.force) { res.skipped.push({ path: rel, reason: "exists (use --force)" }); continue; }
    if (!o.dryRun) { mkdirSync(dirname(f.path), { recursive: true }); writeFileSync(f.path, f.content); if (f.exec) chmodSync(f.path, 0o755); }
    res.written.push(rel);
  }
  if (o.level >= 2) {
    const dest = join(harness, "runtime");
    const exists = existsSync(dest);
    if (!o.dryRun && (!exists || o.force)) {
      for (const sub of ["core", "cli"]) { mkdirSync(join(dest, sub), { recursive: true }); cpSync(join(RUNTIME_DIR, sub), join(dest, sub), { recursive: true, filter: (s) => !s.endsWith(".test.ts") }); }
      writeFileSync(join(dest, "README.md"), readFileSync(join(RUNTIME_DIR, "README.md"), "utf8"));
    }
    if (exists && !o.force) res.skipped.push({ path: "harness/runtime", reason: "exists (use --force to refresh the vendored runtime)" });
    else res.written.push("harness/runtime/ (vendored reference runner)");
  }
  res.next = [
    "write the first real contract: harness/contracts/<id>.json (replace example.json; every done_when names a sensor)",
    ...(o.level >= 2 ? ["harness/bin/validate-graph --dir harness", "harness/bin/run --dir harness --contract harness/contracts/<id>.json", "harness/bin/audit --target ."] : ["bootstrap --level 2 when a task needs sensors or has looped"]),
  ];
  return res;
}

export function dirSize(p: string): number { return existsSync(p) ? statSync(p).size : 0; }
