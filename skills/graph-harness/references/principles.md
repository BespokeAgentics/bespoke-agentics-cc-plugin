# Principles — the seven jobs of a harness, and the patterns across them

The model is the reasoning engine; the harness is the operating system. When an agent fails, the
fix is usually in the system around the model, not in the prompt's wording. Each job below names
what the harness owns, the file that implements it in a bootstrapped project, and the check that
makes it mechanical.

## The seven jobs

| # | Job | What it owns | Implemented by | Mechanical check |
|---|---|---|---|---|
| 1 | **Request → Contract** | every task becomes `goal / inputs / output / constraints / done_when` before any action; no silent redefinition | `harness/contracts/<id>.json`, `schemas/contract.schema.json` | `contract` node + `contract_complete` sensor: schema + vagueness rejection (`runtime/core/contract.ts`) |
| 2 | **Map, not manual** | a small root guide points at architecture, testing, product, security and task guides; detail lives next to the code and loads only when a node needs it | `AGENTS.md`, `harness/guides/<class>.md`, `load_context.guides` | `audit` Q2 (pointers resolve); `load_context` fails on a missing named guide when its `fail` edge exists |
| 3 | **Tools with contracts and tiers** | purpose, predictable output, explicit failure state, boundary; read = allowed, tests = sandbox, write = workspace only, network = scoped, deploy/delete = approval | `harness/policy.yaml` | `validate-graph` TOOL_UNDECLARED / TIER_MISMATCH; `audit` Q3–Q4 |
| 4 | **Durable external state** | decisions, artifacts, failures, pending items and the current step live outside the context window; a new session inherits the work, not a retelling | `harness/runs/<id>/events.jsonl` (truth), `state.json` (projection) | `resume` rebuilds from the log; the crash test in `runtime/tests/runner.test.ts` |
| 5 | **Sensors before autonomy** | every artifact type has evidence producers: code → tests + types + lint; UI → render + screenshot + inspection; research → sources + contradictions; data → schema + range + freshness | `graph.yaml § sensors`, `templates/sensors/*.yaml` | `validate-graph` VERIFY_NO_SENSOR / UNSENSED_ACT; a sensor with `todo` fails until wired |
| 6 | **Permissions enforced outside the model** | `MODEL SUGGESTS → POLICY CHECKS → TOOL EXECUTES`; the model never plans, approves risk and executes side effects alone | `runtime/core/policy.ts`, `policy_gate` node, `approvals.json` | every tool call has a `policy.decided` event; `validate-graph` UNGATED_RISK |
| 7 | **Traces and local recovery** | request, selected context, tool calls, state changes, verification, retries, cost, final artifact, rollback point | `events.jsonl`, `receipt.json`, `rollback/pre.patch` | `receipt` validates against `receipt.schema.json`; `audit` Q10–Q11 |

## Cross-cutting patterns

- **Guide + Check.** Every important rule is written twice: prose the agent understands, and a
  mechanical check it cannot bypass ("UI may not query the DB" + the lint rule that fails on the
  import). A rule without a check is a TODO with the reason, never an unmarked gap. The Rules table
  in `AGENTS.md` is that register.
- **The loop belongs to the harness.** Bounded retries (`repair.retry.max`), a budget
  (`budget.max_steps`, `max_retries_total`, `max_cost_usd`), evidence-gated continuation (edges
  from sensor outcomes), and an escalation path (`human_review`). The model decides *how* to
  repair; the harness decides *whether* another attempt is allowed.
- **Separate builder from evaluator.** `act` never approves its own work; `verify` runs sensors
  and `policy_gate` decides risk. A graph where `act` leads straight to `receipt` is rejected.
- **Brain / Hands / History.** Model (`ModelAdapter`), sandbox + tools (`ToolAdapter`,
  `PolicyEngine`), append-only log (`StateStore`) are separate components. If the sandbox dies,
  history survives; if the model changes, tools and policy stay inspectable.
- **Change receipt per run.** Context sources, policy version, model route, tools used, test
  results, human corrections, retries, cost, accepted artifact, rollback point. One JSON file.
- **Failure upgrades the system.** Repair the class, not the output — see
  [failure-taxonomy.md](failure-taxonomy.md).
- **Smallest harness that closes the loop.** L0 prompt + model → L1 guide + tools → L2 structured
  state + tests + bounded loop → L3 permissions + traces + recovery + human gates. Move up only when
  the task earns it — see [maturity-levels.md](maturity-levels.md).
