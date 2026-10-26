# Maturity levels — the smallest harness that closes the loop

Move up only when the task earns it. The harness should be smaller than the failure surface it
controls; Level 3 machinery around a Level 1 task is cost without evidence.

| Level | Adds | Files bootstrap writes | Closes the loop for |
|---|---|---|---|
| **L0** prompt + model | nothing | — | a one-shot answer nobody acts on |
| **L1** guide + tools | a root map; a contract per task; tool contracts and tiers *as prose* | `AGENTS.md`, `harness/policy.yaml`, `harness/schemas/contract.schema.json`, `harness/contracts/`, `harness/guides/<class>.md`, `harness/README.md` | a reversible task a human checks by hand |
| **L2** structured state + tests + bounded loop | the graph, sensors, the vendored runner, the event log, capped repair, escalation | + `harness/graph.yaml`, `harness/runtime/`, `harness/bin/`, `harness/runs/`, `harness/sensors/`, event/state/graph/policy schemas | a task that needs evidence (tests, screenshots) and may need more than one attempt |
| **L3** permissions + traces + recovery + human gates | approval records for irreversible tools; the receipt schema; the approve tier switches from `deny` to `require_approval` | + `harness/approvals.json`, `harness/schemas/receipt.schema.json` | a task that touches something irreversible or shared (deploy, delete, send) |

Note: the L2 runner already writes receipts and rollback points; L3 is about *permitting*
irreversible actions safely. At L2 they are refused outright.

## Recommend a level (used in the skill's elicitation step)

| Signal | Level |
|---|---|
| reversible, workspace-only, verifiable by reading the result | L1 |
| needs tests/screenshots/schema checks to know it is done; has failed or looped before | L2 |
| irreversible or visible to other people; must be auditable; runs unattended | L3 |
| research task with no mechanical verifier | L2 with `todo` sensors routing to `human_review` — never L1, because "looks right" is not evidence |

## Upgrade criteria (when to move up)

- **L1 → L2** when: a task was declared done without running the tests; the same fix was tried
  more than twice; a session ended with the work only in the conversation. Run
  `bootstrap --level 2 --task-class <class>`, then `validate-graph`, then push one contract.
- **L2 → L3** when: the contract's `risk` is `shared` or `irreversible`; a run needs `deploy`,
  `delete_path`, `fetch` to a new host, or sending anything; someone other than the author must be
  able to audit what happened. Run `bootstrap --level 3`; add approval records as decisions are made.
- **Never** add a level because it exists. The audit's "smallest next upgrade" names the single
  change with the best evidence behind it.

## Downgrade

A project can run an L3 graph for one task class and L1 for another: the level lives in the graph
file (`level:`), the policy (`approve` tier rule), and the presence of `approvals.json`. Keep a
second graph (`harness/graph.<class>.yaml`) rather than loosening the main one.
