# Failure taxonomy — failure class → harness change

Repair the class of failure, not just the output. `upgrade-from-failure` reads a run's trace,
infers the class from the events (or takes `--class`), and emits a Guide + Check proposal: the
prose rule for `AGENTS.md` and the mechanical check that enforces it. The table is the contract
between the two.

| Class | Trace signature (inference order) | Guide change | Check change | Example |
|---|---|---|---|---|
| `repeated_loop` | `retry.exhausted`, or `run.failed` with a budget reason | "when sensor X fails twice with the same summary, escalate with evidence" | lower `repair.retry.max` for this signature; keep `on_exhausted: human_review`; tighten `budget.max_retries_total` | the model rewrote the same test three times; the cap fired; the upgrade makes it fire at two |
| `unsafe_action` | `policy.decided` with `deny` or `needs_approval` | "deploy requires an approval record; declare `risk: irreversible` in the contract and gate before act" | tool at tier `approve` in `policy.yaml`; `policy_gate → act` so `validate-graph` UNGATED_RISK holds | a `deploy` call mid-act was blocked; the upgrade moves the gate to plan time |
| `missing_context` | `context.loaded` with a non-empty `missing` | add the map row for the guide the task needed; a retrieval rule by `task_class` | `load_context.guides` names it and has a `fail` edge; audit Q2 catches broken pointers | the model guessed the test command because `TESTING.md` was never pointed at |
| `wrong_tool` | `tool.executed` with `ok: false` | rewrite the tool's contract (purpose/output/failure/boundary) or add the right tool and name the choice in Commands | the contract fields in `policy.yaml`; `validate-graph` TOOL_UNDECLARED | `run_command` with an unlisted prefix failed; the fix is a listed `npm run e2e` with its own contract |
| `unknown_failure` (sensor error) | `sensor.ran` with `error: true` | "capture evidence first: stdout/stderr are in events.jsonl; cite seq numbers" | a reproducing `command` sensor with `todo` until the cause is known | a sensor timed out; nothing was learned until the timeout and output were captured |
| `bad_output` | `sensor.ran` with `pass: false` | the rule the output violated, one line; `done_when` names the sensor that proves it | a sensor that fails on this defect class (`command`, `file_contains`, `json_schema`) | lint passed but the file was empty; the upgrade adds `output_exists` + a size check |
| `lost_decision` | `run.paused` with no later `human.decided` | "decisions are recorded with `resume --decision`, never restated in chat" | the runner refuses to continue a paused run without `--decision` (enforced) | a reviewer said "ship it" in chat; the next session found the run still paused |
| `unknown_failure` (default) | none of the above | evidence capture | tracing + a reproducing sensor | — |

Inference picks the most specific signature present, top to bottom, so a run with both a policy
denial and a failing sensor is classified `unsafe_action` (the gate held; that is the lesson).
Pass `--class` to override.

## What a proposal looks like

```json
{
  "failure_class": "repeated_loop",
  "inferred": true,
  "evidence": [{ "seq": 41, "type": "retry.exhausted", "node": "repair", "summary": "..." }],
  "guide": { "file": "AGENTS.md", "section": "Rules, each with its check", "text": "When tests fails twice ..." },
  "check": { "kind": "graph", "where": "harness/graph.yaml nodes.repair", "spec": { "repair": { "retry": { "max": 2, "on_exhausted": "human_review" } } } },
  "rationale": "..."
}
```

`--write` saves it under `harness/upgrades/<run_id>-<class>.json`. The human applies the guide text
to `AGENTS.md`'s Rules table and the check to the file named in `where`; audit Q12 counts both.
