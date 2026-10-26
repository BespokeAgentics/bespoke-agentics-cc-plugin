---
name: graph-harness
description: >
  Manual only (/bespoke-agentics:graph-harness). Bootstrap, scaffold, audit or harden a graph-based
  agent harness in a target project — the operating system around a model: what it sees (a root map),
  what it can touch (tools with contracts and permission tiers), what survives between sessions
  (an append-only event log), what counts as evidence (sensors per artifact type), and when a run
  must stop (capped repair loops, policy gates, human review). Triggers: "agent harness",
  "graph harness", "harness engineering", "scaffold a harness", "audit our agent setup",
  "the agent keeps looping / redefining the task / deploying without asking". Elicits task class
  and risk, writes the first contract, scaffolds at the smallest maturity level (L1–L3) that
  closes the loop, validates the graph, smoke-tests retry → repair → escalation and resume-after-kill,
  emits a change receipt, scores the 12-question audit. Deterministic TypeScript scripts (Node ≥ 22.18,
  zero dependencies); model and storage are adapters.
disable-model-invocation: true
---

# Graph Harness

**The model is the reasoning engine; the harness is the operating system.** When an agent fails,
the fix is usually in the system around the model, not the prompt's wording. This skill makes that
system concrete, minimal and upgradeable: a directed graph of typed nodes whose edges the harness
chooses from *evidence*, an event log that is the system of record, a policy engine the model
cannot bypass, and a receipt per run.

Principles: [references/principles.md](references/principles.md). Graph semantics, events, resume
rules and the adapter seam: [references/graph-spec.md](references/graph-spec.md). Levels:
[references/maturity-levels.md](references/maturity-levels.md). Failure → harness change:
[references/failure-taxonomy.md](references/failure-taxonomy.md). The audit:
[references/checklist.md](references/checklist.md).

## Arguments

```
/bespoke-agentics:graph-harness [<target-dir>] [--level 1|2|3] [--task-class code|ui|research|data|mixed]
    [--audit-only] [--force]
```

- `<target-dir>` — the repo to harness. Default: cwd. Greenfield is fine (an empty directory).
- `--level` — skip the recommendation and scaffold at this level.
- `--task-class` — skip the elicitation question.
- `--audit-only` — run step 8 against an existing harness and stop.
- `--force` — overwrite files bootstrap would otherwise skip.

All scripts live in `scripts/` (sh shims over `runtime/cli/*.ts`), print JSON to stdout, and exit
non-zero on failure. Paths below are relative to this skill's directory; a bootstrapped project
gets the same commands under `harness/bin/`.

## Workflow

Work the steps in order. Do the mechanical parts with the scripts; spend judgment on the contract,
the level and the sensors.

### 1. Elicit

Ask briefly (one `AskUserQuestion` call, four questions at most):

1. **Task class** — code / UI / research / data / mixed.
2. **Risk profile** — what can be irreversible or touch other people? (deploys, deletes, sends,
   shared data) → maps to contract `risk`: `reversible` / `shared` / `irreversible`.
3. **Target** — existing repo or greenfield; path.
4. **Runtime preference** — the reference runner (Node, file-based, zero deps) or a durable backend
   to plug in later (XState / DBOS / Restate; the seam is documented, adapters are not built).

Then **recommend a starting level and say why**, using the signal table in
`references/maturity-levels.md`: reversible + verifiable by reading → L1; needs sensors or has looped
→ L2; irreversible/shared/unattended → L3. Research with no mechanical verifier is L2 with `todo`
sensors that route to `human_review`, never L1.

### 2. Contract first

Help the user write `harness/contracts/<id>.json` for their first real task
(`templates/contract.schema.json`). Every `done_when` entry must name a sensor or a concrete
predicate (a path, a command, a number, a status code). The check that enforces this is
`runtime/core/contract.ts` (`vaguenessOf`): "works", "looks good", "is done", "properly" are
rejected. Show the rejection and the rewrite rather than silently fixing it — the user should see
the rule and its check together.

Check it before scaffolding:

```bash
node runtime/cli/validate-graph.ts --graph templates/graph.default.yaml   # sanity: the shipped graph
node -e 'import("./runtime/core/contract.ts").then(m=>console.log(JSON.stringify(m.validateContract(JSON.parse(require("fs").readFileSync(process.argv[1],"utf8"))),null,2)))' harness/contracts/<id>.json
```

### 3. Scaffold

```bash
scripts/bootstrap --target <dir> --level <1|2|3> --task-class <class> [--force]
```

Generates only what the level needs (table in `references/maturity-levels.md`). Read the JSON
manifest: `written`, `skipped` (existing files are never overwritten without `--force`), `notes`
(sensors with `todo`, an existing `AGENTS.md` that got a `harness/AGENTS.harness.md` to merge),
`next`. At L2+ the reference runtime is vendored into `harness/runtime/` with shims in
`harness/bin/`; no install step.

### 4. Map

Bootstrap inspects the repo (manifests, scripts, docs, CI) and renders `AGENTS.md` from
`templates/AGENTS.md`: a map, not a manual. Review it with the user: every row should **link to an
existing doc** rather than duplicate it; the Commands table must be the real test/lint/types
commands; the Rules table must have a check per rule (a TODO row is acceptable only with its reason).
If the project already had an `AGENTS.md`, merge the Harness and Rules sections in by hand.

### 5. Wire sensors and policy

- Sensors: `harness/graph.yaml § sensors` was filled from `templates/sensors/<class>.yaml` with the
  detected commands. A sensor whose command was not detected has `cmd: "false"` and a `todo`; it
  **fails until wired** — that is the point. Wire it or delete it with the user; never set
  `allow_todo: true` to make a run green.
- Policy: `harness/policy.yaml`. Confirm the workspace, `deny_paths`, the sandbox allow-list, any
  network hosts the task needs, and that every tool the task will use has all four contract fields.
  At L2 the `approve` tier is `deny` (irreversible tools refused); at L3 it is `require_approval`
  with records in `harness/approvals.json`.

### 6. Validate

```bash
scripts/validate-graph --dir harness
```

Must pass before any run. It fails on: unreachable nodes, dead ends, missing outcome edges, loops
without a retry cap (or a human in them), risky nodes without a gate in front, act/verify nodes
with no sensor, undeclared sensors/tools, node tiers below their tools. The seven fixtures under
`fixtures/broken-graphs/` show each failure with its code.

### 7. Smoke test

Push a toy task through the full graph with the deterministic stub model, including one forced
failure and one kill, to prove the loop is the harness's:

```bash
scripts/run --dir harness --contract harness/contracts/<id>.json --run-id smoke-1 --model stub
scripts/run --dir harness --contract harness/contracts/<id>.json --run-id smoke-2 --inject-failure tests:9
#   → retry → repair ×3 → retry.exhausted → escalated → run.paused (exit 2); pending.json names the decision
scripts/resume --run harness/runs/smoke-2 --decision approved
scripts/run --dir harness --contract harness/contracts/<id>.json --run-id smoke-3 --kill-after 3
#   → exit 137 with the run mid-node
scripts/resume --run harness/runs/smoke-3          # rebuilds state from events.jsonl, completes
```

At L3 also prove the gate: `--stub-extra '{"tool":"deploy","args":{"target":"prod"}}'` must
produce `policy.decided decision=needs_approval` in the trace and pause the run. Read the trace on
stderr; every transition is there. With a real model, swap `--model command:'<cli>'` (JSON in, JSON out).

### 8. Receipt + audit

```bash
scripts/receipt --run harness/runs/smoke-1 --write      # validated against receipt.schema.json
scripts/audit --target <dir> --markdown                 # 12 questions, a fix per gap
```

Report the score, the gaps with their fixes, and the **smallest next upgrade** the audit names.
When a run failed, add its proposal:

```bash
scripts/upgrade-from-failure --run harness/runs/<id> --write   # Guide + Check pair under harness/upgrades/
```

## Constraints

- **Minimal by default.** Do not generate L3 machinery for an L1 task. The harness should be
  smaller than the failure surface it controls.
- **No vendor lock-in.** Model and storage are adapters (`runtime/core/types.ts`). Ship `stub` and
  `command:` model adapters and the file store; document the seam for durable backends, do not build them.
- **Every rule twice.** Any rule added to a guide comes with its mechanical check, or a marked TODO
  explaining why a check is not possible yet.
- **Deterministic scripts.** Scripts do the mechanical work and print JSON; the model does judgment.
- **Never commit, never deploy, never approve.** Approval records are written by humans.

## Verification

Done when all of these hold and are shown, not asserted:

- `validate-graph --dir harness` exits 0; the JSON shows `errors: []`.
- The toy task completed (`run` exit 0) and the receipt validated (`receipt` exit 0).
- The forced failure paused at `human_review` with `retry.exhausted` in the trace, and `resume
  --decision` finished it.
- The killed run resumed from the log and completed; `seq` is contiguous.
- At L3: the ungated `deploy` was `needs_approval` in the trace and did not execute.
- `audit` ran; its score and smallest next upgrade are in the final report.

Runtime tests (the skill's own proof): `cd runtime && node --test 'tests/*.test.ts'`.
