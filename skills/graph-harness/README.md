# graph-harness

Bootstrap a graph-based agent harness into a project: the environment around a model that decides
what it sees, what it can touch, what survives between sessions, what counts as evidence, and when
a run must stop. Invoked as `/bespoke-agentics:graph-harness`; the workflow is in `SKILL.md`.

```
graph-harness/
├── SKILL.md                 # trigger, workflow, routing
├── references/              # principles · graph-spec · maturity-levels · failure-taxonomy · checklist
├── templates/               # AGENTS.md map, six JSON schemas, policy.yaml, graph.default.yaml, sensors/
├── scripts/                 # bootstrap · validate-graph · run · resume · receipt · audit · upgrade-from-failure
├── runtime/                 # the reference runner (TypeScript, Node ≥ 22.18, zero deps) + its tests
├── fixtures/broken-graphs/  # seven graphs validate-graph must reject
└── evals/                   # skill eval cases
```

## Quick start

```bash
S=skills/graph-harness/scripts
$S/bootstrap --target . --level 2 --task-class code      # AGENTS.md + harness/ (graph, policy, runtime, bin)
harness/bin/validate-graph --dir harness                 # must pass
harness/bin/run --dir harness --contract harness/contracts/<id>.json
harness/bin/audit --target . --markdown
```

Every script prints JSON and exits non-zero on failure. Proof the pieces work:
`cd skills/graph-harness/runtime && node --test 'tests/*.test.ts'` (18 tests: schemas, YAML
subset, validator vs. the broken fixtures, happy path, forced failure → escalation, deploy gate,
workspace boundary, vague-contract rejection, crash + resume, bootstrap L1→L2→L3, audit, upgrade).

## Moving from L1 → L2 → L3

The level is the smallest harness that closes the loop for the task at hand. Each step adds
files; nothing is removed.

**L1 → L2** — *guide + tools* becomes *structured state + sensors + bounded loop*. Do it when a task
was declared done without evidence, the same fix was tried more than twice, or the work only
existed in the conversation at session end.

```bash
scripts/bootstrap --target . --level 2 --task-class <class>
harness/bin/validate-graph --dir harness
harness/bin/run --dir harness --contract harness/contracts/<id>.json
```

Adds `harness/graph.yaml` (sensors filled from the detected test/lint/types commands), the vendored
runtime and `harness/bin/`, `harness/runs/` (the event log), the event/state/graph/policy schemas.
The `approve` tier is `deny`: irreversible tools are refused outright.

**L2 → L3** — adds *permissions + traces + recovery + human gates* for irreversible work. Do it
when a contract's `risk` is `shared` or `irreversible`, a run needs `deploy` / `delete_path` /
a new network host, or someone else must audit what happened.

```bash
scripts/bootstrap --target . --level 3 --task-class <class> --force   # --force rewrites policy.yaml
```

Switches `approve` to `require_approval`, adds `harness/approvals.json` (a record per approved
tool: `{ "tool": "deploy", "granted_by": "<name>", "ts": "<iso>" }`) and the receipt schema. A run
that needs an approval pauses at `human_review`; a human adds the record and runs
`harness/bin/resume --run harness/runs/<id> --decision approved`.

**Never up a level because it exists.** `harness/bin/audit` names the single smallest next upgrade
with the best evidence behind it.

## Design decisions worth reviewing

Recorded in `docs/plans/graph-harness-skill.md` (the schema proposal) and `references/graph-spec.md`.
The ones most likely to need a second opinion: fixed outcome vocabularies per node type (instead of
free-form edge conditions); a cycle through `human_review` needs no retry cap; node execution is
at-least-once on resume; the vendored runtime (no install step) with a documented YAML subset.
