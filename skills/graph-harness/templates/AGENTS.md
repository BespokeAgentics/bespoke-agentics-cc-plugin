# {{project_name}} — Agent Map

This file is a map, not a manual. Read it first; load the guides it points to only when a step
needs them. Detailed knowledge lives next to the code it governs.

## What this project is

{{purpose}}

## Where things are

| Need | Go to |
|---|---|
{{map_rows}}

## Commands (run these; do not guess)

| Purpose | Command | Evidence it produces |
|---|---|---|
{{command_rows}}

## Harness (level {{level}})

Every task starts as a **contract** (`harness/contracts/<id>.json`, schema `harness/schemas/contract.schema.json`):
`goal`, `inputs`, `output`, `constraints`, `done_when`. A `done_when` entry must name a sensor or a concrete
predicate; the harness rejects vague ones ("works", "looks good") before any action.

{{harness_rows}}

Permission tiers (`harness/policy.yaml`, enforced outside the model):
read = allowed · run tests = sandbox (listed commands only) · write = workspace only ·
network = scoped per task · deploy / delete = requires an approval record.

## Rules, each with its check

Every rule here exists twice: as prose for you, and as a mechanical check you cannot bypass.
A rule without a check is marked TODO with the reason.

| Rule | Check |
|---|---|
| A task is bounded by a contract before any tool runs | `contract` node + `contract_complete` sensor (harness/graph.yaml) |
| Output is verified by sensors, never by self-assessment | `verify` node must declare sensors (`validate-graph` VERIFY_NO_SENSOR) |
| Repair loops are capped | `repair.retry.max` + `budget.max_retries_total` (`validate-graph` UNCAPPED_LOOP) |
| Irreversible actions pass a gate | approve-tier tools need an approval record (`policy.yaml`); risky nodes need a gate in front (`validate-graph` UNGATED_RISK) |
| Writes stay inside the workspace | `policy.yaml` write tier = allow_in_workspace + `deny_paths` |
{{rule_rows}}

## Task guides

{{task_guides}}

## When something fails

Repair the class of failure, not just the output. Run
`harness/bin/upgrade-from-failure --run harness/runs/<id>` to get a Guide + Check proposal
(see `harness/README.md` § Failure taxonomy).
