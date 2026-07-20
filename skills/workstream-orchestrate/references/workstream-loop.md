# Workstream loop — semantics, state & resume

One workstream = one bounded `code → validate → commit` loop, run to a green commit or a halt. This
file defines the loop precisely so the `workflow` and `agent` engines behave identically.

## The loop

```
for attempt in 1..ATTEMPTS:
    code:     implementer applies THIS workstream's scope in the shared tree; runs GATES;
              returns {files, summary, gateResults}
    validate: independent read-only agent re-runs GATES, diffs tree vs contract, proves/refutes
              each HARD_GATE; returns {pass, findings, proofs}
    you:      re-run GATES yourself (the agent's claim is not evidence)
    if pass AND you confirm the gates are green:
        commit: ONE Conventional Commit, THIS workstream's files only, via COMMIT_CMD
        mark WS committed; break
    else:
        record findings verbatim; feed them into the next attempt's code packet
if no attempt passed → mark WS failed, surface findings, do NOT commit, halt the run
```

Then the **human checkpoint** (unless `--no-confirm`): present the diff summary, gate + hard-gate
verdicts, commit hash + subject, residual risk; wait to proceed to the next workstream.

## Rules

- **Sequential, in-tree, no worktree.** The workstream edits the live working tree. Because only one
  workstream runs at a time and each ends at a commit, there is never a two-writer conflict — the
  reason `orchestrate` needs worktrees for the code path does not apply here.
- **Gates are re-run by you.** The implementer runs them to fail fast; you re-run them in the main
  session before allowing the commit. A commit never lands on a gate you didn't see pass.
- **The commit stages only this workstream's files.** Enumerate them from the implementer's `{files}`
  return and `git status`; never `git add -A`. Pre-existing dirt and unrelated changes stay
  uncommitted.
- **Findings are fed back verbatim.** A failed validate appends its `findings` to the next code
  packet exactly; summarizing them is how a fix misses the point.
- **Halt is honest.** On `ATTEMPTS` exhaustion you stop the whole run at this workstream and surface
  the surviving findings — you never lower the bar or force a commit to "make progress".

## state.md

Write transitions **as they happen** (a batched state file protects nothing). Format:

```markdown
# Workstream state: {RUN_SLUG}
plan: {PLAN_PATH}
contract: {CONTRACT}
branch: {branch}
base_ref: {BASE_REF}
engine: {workflow|agent}
attempts_max: {ATTEMPTS}
flags: {flags passed}
preexisting_dirt: |
  {verbatim `git status --short` from pre-flight — protected, never committed}
gates: [ {command}, … ]          # discovered at pre-flight
commit_cmd: {COMMIT_CMD}
model_substitutions: {none | "opus unavailable → inherit"}

## Workstreams
| ws   | status     | attempts used | hard gates      | commit             | report            |
|------|------------|---------------|-----------------|--------------------|-------------------|
| WS-0 | committed  | 1             | —               | a1b2c3d docs(...)  | reports/ws-0.md   |
| WS-1 | validating | 2             | HG-1 pending    | —                  | reports/ws-1-a2.md|

## Decisions & arbitrations
- {phase: what was decided, by whom (human at Phase A / orchestrator arbitration), why}

## Gate log
| when (ws, attempt) | command | result | routed to |
|---|---|---|---|
```

Statuses: `pending | coding | validating | committed | failed`. A workstream reaches `committed` only
after its commit lands; `failed` only after `ATTEMPTS` exhaustion.

## reports/

One verbatim subagent return per file: `reports/ws-{n}.md` (final), `reports/ws-{n}-a{N}.md` (each
code attempt), `reports/ws-{n}-validate-a{N}.md` (each validate). Never overwrite a failing attempt —
the history is the audit trail.

## Resume rules

1. Re-run pre-flight branch/conventions/plan fresh — the repo may have moved. `BASE_REF` and
   `preexisting_dirt` come from `{STATE}`, never recomputed.
2. `committed` workstreams are skipped on their state alone — their commit is the proof. Do not re-run
   their gates unless a later workstream's gate fails in a way that implicates them.
3. A `coding`/`validating` workstream restarts from the contract; a `failed` one resumes at its next
   attempt with the recorded findings. Attempt counts persist across sessions — 2 recorded attempts
   means the next failure halts.
4. Phase-A decisions are durable: never re-ask a question `{STATE}` records an answer to.
5. If `{CONTRACT}` is missing but reports exist, the run is corrupt — tell the human and offer
   `--force`.
