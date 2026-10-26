# The 12-question readiness audit

`audit --target <repo>` answers each question mechanically and scores pass (1), partial (0.5),
fail (0) out of 12, with one concrete fix per gap and the "smallest next upgrade" (the first gap in
this order — the order is by leverage). The questions are the checklist; the script is the check.

| # | Question | Pass when | Partial when |
|---|---|---|---|
| 1 | Does every task become a **contract** (goal, inputs, output, constraints, done_when) before any action? | `harness/schemas/contract.schema.json` exists and `harness/contracts/` has a real contract | schema only (just `example.json`) |
| 2 | Is there a small **root map** (`AGENTS.md`) that points to architecture, testing, product and security guides instead of restating them? | ≥ 3 file pointers, none broken | map exists with fewer pointers or broken ones |
| 3 | Does every **tool have a contract**: purpose, predictable output, explicit failure state, boundary, and a tier? | every tool in `policy.yaml` has all four fields | some incomplete |
| 4 | Are **permission tiers** set (read allowed, tests sandboxed, writes workspace-only, network scoped, deploy/delete needs approval) and enforced outside the model? | approve tier = `require_approval`, approve-tier tools exist, runtime present | policy exists but approve = `deny` (L2) or no runtime (L1) |
| 5 | Does **durable state** (decisions, artifacts, failures, pending, current step) live outside the conversation? | a run with `events.jsonl` exists | runtime installed, no run yet |
| 6 | Does each **artifact type** have evidence producers (code: tests/types/lint; ui: render/screenshot; research: sources; data: schema/range/freshness)? | ≥ 2 sensors, none `todo` | sensors exist but some are `todo` |
| 7 | Is the **loop owned by the harness**: bounded retries, a budget, evidence-gated continuation, escalation to a human? | `validate-graph` passes and repair has `retry` | graph exists but invalid |
| 8 | Is the **builder separated from the evaluator**? | every `act` leads to a `verify` with sensors (or has its own) | graph exists but an act self-approves |
| 9 | Is **MODEL SUGGESTS → POLICY CHECKS → TOOL EXECUTES** enforced by the runtime? | `policy.decided` events in the latest run | runtime present, no run to inspect |
| 10 | Does every run leave a **trace and a change receipt**? | latest run's `receipt.json` validates against the schema | run exists, receipt missing/invalid |
| 11 | Does each run record a **rollback point** before acting? | `rollback.point` with `kind: git` | present but `kind: none` (not a git repo) |
| 12 | Does **failure upgrade the system** (failure class → guide + check, recorded where the next session finds it)? | `harness/upgrades/` has proposals and the map's Rules table has ≥ 3 Guide + Check rows | one of the two |

A fresh L1 bootstrap scores roughly 3–5; L2 after one run roughly 9–10; L3 after one run with an
upgrade proposal 11–12. The audit never modifies anything.
