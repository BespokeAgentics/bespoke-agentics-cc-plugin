# Graph specification

A harness run is a walk over a directed graph of typed nodes. The graph file (`harness/graph.yaml`,
schema `templates/graph.schema.json`) is declarative and validated, so the graph itself is a
reviewable artifact. The runtime that executes it is `runtime/core/runner.ts`.

## Graph file

```yaml
version: 1
name: default
level: 2                     # 1..3; what machinery this graph assumes
entry: contract
budget: { max_steps: 40, max_retries_total: 6, max_cost_usd: 2.0 }
sensors: { <name>: <SensorDef> }
nodes:   { <name>: <NodeDef> }
```

## Node types and outcomes

A node's **outcome** is computed by the harness from evidence. The model's self-assessment is never
an outcome. Each type has a fixed outcome vocabulary; `edges` must cover the required set (or use
`"*"`), and may not name an outcome the type cannot produce.

| type | does | outcomes (required) | declares |
|---|---|---|---|
| `contract` | validates the request as a contract (schema + vagueness check); records the rollback point | `ok` · `fail` | `sensors: [contract_complete]` |
| `load_context` | reads `guides` from the workspace; records sources | `ok` (+ optional `fail` when a named guide is missing) | `guides` |
| `plan` | asks the model for ordered steps; no side effects | `ok` | — |
| `act` | asks the model for tool calls; each passes the policy engine; runs its own sensors if declared | `ok` · `fail` · `blocked` | `tools`, `tier`; sensors **or** an `ok` edge into `verify` |
| `verify` | runs sensors (in parallel when `parallel: true`) | `pass` · `fail` | `sensors` (≥ 1) |
| `policy_gate` | risk decision for the artifact: `reversible` → allow; otherwise the virtual tool `release` must have an approval record | `allow` · `deny` · `needs_approval` | — |
| `repair` | asks the model what to change given concrete failures; counts a retry | `ok` (`exhausted` routes via `retry.on_exhausted`) | `retry: { max, on_exhausted }` |
| `human_review` | pauses the run (`pending` → `run.paused`) until `resume --decision` | `approved` · `rejected` | — |
| `receipt` | writes `receipt.json`; `run.completed` when entered via `allow`/`approved`, else `run.failed` | terminal | `terminal: true` |

`blocked` means a tool call in the node was denied or needs approval. The other calls in the node
still ran; nothing is retried silently.

## Edges

```yaml
verify:
  type: verify
  sensors: [tests, lint]
  edges: { pass: policy_gate, fail: repair }
```

Transitions are chosen by the harness from the outcome. There are no conditions on edges by
design: a fixed outcome vocabulary is what makes "every outcome has an edge" checkable.

## Loops, budgets, gates — the validator's rules

`validate-graph` (JSON report, exit 1) fails on:

| code | rule |
|---|---|
| `SCHEMA` | the file does not match `graph.schema.json` (budget required, known node types, …) |
| `ENTRY_MISSING` · `EDGE_TARGET` | entry / edge / `on_exhausted` targets must exist |
| `UNREACHABLE` · `NO_TERMINAL` · `DEAD_END` | every node reachable from entry; a terminal reachable; non-terminal nodes have edges |
| `OUTCOME_UNCOVERED` · `OUTCOME_UNKNOWN` | every required outcome has an edge; no edge for an impossible outcome |
| `UNCAPPED_LOOP` | every cycle contains a node with `retry.max` **or** a `human_review` node (a human bounds the loop) |
| `REPAIR_NO_RETRY` | repair nodes must declare `retry` |
| `UNGATED_RISK` | a node with `risk: irreversible`, `tier: approve`, or any approve-tier tool is entered only from `policy_gate` / `human_review` |
| `UNSENSED_ACT` · `VERIFY_NO_SENSOR` | act output is sensed (own sensors or an `ok` edge into verify); verify has sensors |
| `SENSOR_UNDECLARED` · `TOOL_UNDECLARED` · `TIER_MISMATCH` | names resolve; a node's tier is ≥ every tool it grants |

Seven deliberately broken graphs under `fixtures/broken-graphs/` pin these rules in the test suite.

## Sensors

```yaml
sensors:
  tests:         { kind: command,      cmd: "npm test", applies_to: [code], timeout_ms: 300000 }
  output_exists: { kind: file_exists,  path: "{contract.output.path}" }
  has_sources:   { kind: file_contains, path: "{contract.output.path}", pattern: "https?://" }
  shape:         { kind: json_schema,  path: "out/data.json", schema: "schemas/output.schema.json" }
  a11y:          { kind: custom,       module: "sensors/a11y.ts", todo: "not wired yet" }
```

`{contract.output.path}`-style placeholders interpolate from the contract. A sensor with `todo`
reports `pass: false` (unless `allow_todo: true`) so an unimplemented check is never green.
`contract_complete` is built in. Custom modules export `run(ctx, def) → { pass, summary, evidence }`.

## Subgraphs

`verify` with `parallel: true` runs its sensors concurrently (the common ∥ tests/lint/screenshot
case). `subgraph: <file>` is reserved and validated as a string; the reference runner does not
expand file subgraphs yet — a node needing one is a TODO in `AGENTS.md`, not a silent no-op.

## Events

`events.jsonl` is append-only; each line matches `event.schema.json`:
`{ seq, ts, run_id, type, node?, attempt?, data }`. Types:

`run.started` · `contract.accepted` · `contract.rejected` · `context.loaded` · `node.entered` ·
`node.exited` (`data.outcome`, `data.next`) · `tool.requested` · `policy.decided` (`decision`,
`rule`, `reason`, `tier`) · `tool.executed` · `sensor.ran` · `artifact.produced` ·
`retry.scheduled` · `retry.exhausted` · `escalated` · `human.decided` · `cost.recorded` ·
`rollback.point` · `subgraph.completed` · `run.paused` · `run.resumed` · `run.completed` · `run.failed`

Every transition is an event. `seq` is contiguous; `append` fsyncs before returning. A torn final
line (crash mid-write) is dropped on read; everything before it is intact.

## State and resume

State (`state.schema.json`) is a projection of the log: `projectState(events)` is pure, so replaying
the same events yields the same state. `attempts[node]` counts `node.entered` events;
`retries_total` counts `retry.scheduled`.

`resume --run <dir>`:

1. reads `events.jsonl`, projects state;
2. `completed`/`failed` → returns the state, no events written;
3. `paused` → requires `--decision approved|rejected`; appends `run.resumed`, then `human.decided`;
4. `running` (the process died) → appends `run.resumed` and **re-enters `current_node`**.

Node execution is therefore *at-least-once*: a node interrupted after `node.entered` runs again.
Tools must be idempotent (`write_file` is; a `deploy` that is not should be gated) or the node must
restart cleanly. A re-entry counts as another attempt, so a crash inside `repair` consumes a retry —
conservative on purpose.

## Policy

`policy.yaml` (schema `policy.schema.json`): five tiers, one rule each; every tool a contract.
`decide({tool, args, node, run_id})` → `allow | deny | needs_approval` with `rule` and `reason`:

- any path argument outside `workspace` → deny (every tier); under `deny_paths` → deny (non-read tiers)
- `allow_listed`: sandbox commands by prefix (`sandbox_allow`), network hosts by suffix (`network_allow`)
- `require_approval`: a record in `approvals_file` `{ tool | "*", run_id?, granted_by, ts }` → allow with
  `rule: approval:<granted_by>`; otherwise `needs_approval`, the act node is `blocked`, the run pauses
- a tool not granted to the node (`node.tools`) → deny with `rule: node.tools`

## Adapter seam

`runtime/core/types.ts` defines `StateStore`, `PolicyEngine`, `Sensor`, `ToolAdapter`, `ModelAdapter`.
The file implementations are the reference. To plug in a durable-execution backend, implement
`StateStore` (append must be durable before it returns; `events()` must be total and ordered) and
hand it to `Runner`. XState would wrap the graph as a machine whose actions call the same
`exec*` steps; DBOS/Postgres or Restate would own `append` and `events` and provide the resume
trigger. None of these are built here; the seam is the contract they must meet.

`ModelAdapter.propose(ModelInput) → ModelOutput`: `plan` (steps), `calls` (tool calls), `notes`,
`usage`. `command:<shell>` adapters receive the input as JSON on stdin and print JSON; e.g. a
wrapper around `claude -p` that asks for the output shape.

## The harness YAML subset

The runtime parses YAML without a dependency, so harness files stay inside this subset: block
mappings, block sequences, flow sequences and mappings (nesting allowed), quoted and unquoted
scalars, comments, `null`/`~`/booleans/numbers. **Not** supported, and rejected loudly: anchors,
aliases, tags, block scalars (`|`, `>`), multi-document files, tabs. JSON files are accepted
anywhere a YAML file is.
