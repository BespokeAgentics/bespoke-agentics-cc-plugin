# `graph-harness` — Skill Spec and Graph Schema

**Created:** 2026-10-26
**Status:** Built (schema below is what the runtime implements; review and change here first)
**Target:** `skills/graph-harness/` (bespoke-agentics plugin)

---

## Design, restated

- **The model reasons; the harness is the operating system.** Every failure class maps to a
  harness change (guide, tool, validator, cap, gate, state, trace) — never to prompt wording alone.
- **Request → Contract before any action.** `goal / inputs / output / constraints / done_when`;
  `done_when` entries are mechanically rejected when vague (no sensor and no verifiable predicate).
- **Work is a directed graph of typed nodes.** `contract → load_context → plan → act → verify →
  policy_gate → receipt`, with `repair` and `human_review` as the only loops and escalations.
- **Edges are chosen by the harness from evidence.** A node ends with an *outcome* computed from
  sensor results, policy decisions and budget state. The model's self-assessment is never an outcome.
- **History is an append-only JSONL event log; state is a projection of it.** Kill the process at
  any step; `resume` rebuilds state from the log and re-enters the current node.
- **Permissions enforced outside the model.** `MODEL SUGGESTS → POLICY CHECKS → TOOL EXECUTES`.
  Every tool call passes `PolicyEngine.decide`; every decision (allow/deny/needs_approval) is an event.
- **Every rule twice.** Each guide rule the skill installs has a mechanical check, or a marked TODO.
- **Smallest harness that closes the loop.** L1 = guide + tools + policy, no runner. L2 = graph,
  state, sensors, bounded loop. L3 = approvals, traces, receipts, rollback point, human gates.
- **Zero required infra.** TypeScript on Node ≥ 22.18 (native type stripping), no npm dependencies:
  a JSON-Schema subset validator and a YAML subset parser are vendored in the runtime. Durable
  backends (XState, DBOS, Restate) plug in behind `StateStore`; documented, not built.

## Graph schema

### Node types and their outcomes (fixed by the harness)

| type | produces | outcomes | must declare |
|---|---|---|---|
| `contract` | the bounded task object | `ok` · `fail` | — (built-in `contract_complete` sensor) |
| `load_context` | selected guides + files | `ok` | `guides` |
| `plan` | an ordered step list | `ok` | — |
| `act` | tool calls → artifacts | `ok` · `fail` · `blocked` | `tools`, `tier`; sensors **or** an `ok` edge into a `verify` node |
| `verify` | sensor results | `pass` · `fail` | ≥ 1 `sensors` entry |
| `policy_gate` | a risk decision | `allow` · `deny` · `needs_approval` | — |
| `repair` | a repair plan (model) | `ok` · `exhausted` | `retry.max` |
| `human_review` | a human decision | `approved` · `rejected` · `pending` | — |
| `receipt` | the change receipt | terminal | `terminal: true` |

`blocked` = a tool call in the node was denied or needs approval; the run goes where the graph says
(default: `policy_gate` / `human_review`), never silently on.

### Edges

```yaml
nodes:
  verify:
    type: verify
    sensors: [tests, lint]
    edges: { pass: policy_gate, fail: repair }
```

`edges` maps every outcome the node type can produce to a target node (`"*"` is a wildcard). The
validator fails on a missing outcome, a target that does not exist, and a non-terminal node with
no edges.

### Loops and budgets

- `budget: { max_steps, max_retries_total, max_cost_usd }` is required at graph level.
- Every cycle must contain a node with `retry: { max: n, on_exhausted: <node> }`. The harness
  counts attempts per node; `exhausted` is an outcome, not a model decision.

### Gates on risky edges

- A node is *risky* when it declares `risk: irreversible` or any of its `tools` is at policy tier
  `approve` (default: `deploy`, `delete_path`). Every incoming edge to a risky node must come from
  `policy_gate` or `human_review`.

### Subgraphs

A `verify` node may set `parallel: true`; its sensors run concurrently and the node's outcome is
`pass` only when all pass. A node may instead point at `subgraph: <file>`: the sub-run gets its own
event log and the parent records `subgraph.completed` with the child's outcome. (Parallel sensors
are implemented; file subgraphs are validated and run sequentially in the reference runner.)

### Events (append-only, `events.jsonl`)

`{ seq, ts, run_id, type, node?, attempt?, data }` with types:

`run.started` · `contract.accepted` · `contract.rejected` · `context.loaded` · `node.entered` ·
`node.exited` · `tool.requested` · `policy.decided` · `tool.executed` · `sensor.ran` ·
`artifact.produced` · `retry.scheduled` · `retry.exhausted` · `escalated` · `human.decided` ·
`cost.recorded` · `rollback.point` · `run.paused` · `run.resumed` · `run.completed` · `run.failed`

### State (projection)

`{ run_id, graph, level, status, current_node, step, attempts{node→n}, retries_total, contract,
decisions[], artifacts[], failures[], pending[], cost, rollback_point, last_seq }`

`status ∈ running | paused | completed | failed`. `resume` replays the log, re-enters
`current_node` (at-least-once semantics: tools must be idempotent or the node restarts cleanly).

## Decisions to review

1. **Outcome vocabulary is fixed per node type** (table above) rather than free-form conditions.
   It makes "every outcome has an edge" checkable; custom conditions would not be.
2. **Sensors are declared in the graph file** (`sensors:` map, kinds `command` · `file_exists` ·
   `file_contains` · `json_schema` · `contract_complete`), not in code. Custom kinds are a TS stub.
3. **Policy is YAML, decisions are events.** Approval is a record in `approvals.json`
   `{tool, run_id?, granted_by, ts}`; a run that needs one pauses and `resume --approve` continues.
4. **Vendored runtime in the target repo** (`harness/runtime/`) so a bootstrapped project has no
   install step. Upgrading = re-running bootstrap; the files are plain TS and reviewable.
5. **Model adapters:** `stub` (deterministic, for smoke tests) and `command` (any CLI that reads a
   JSON prompt on stdin and writes JSON on stdout, e.g. `claude -p`). No SDK dependency.
