---
name: "bespokeagentics:workstream-orchestrate"
description: "Generate a kickoff contract from an implementation plan, then drive a strictly-sequential, per-workstream code→validate→commit build with the Workflow tool — one bounded Workflow per workstream, an adversarial validator that proves the plan's server-side hard gates, one Conventional Commit per green workstream, and a human checkpoint between workstreams. The driver never writes production code; given a raw task it drafts and confirms a plan first."
argument-hint: "'<plan-path-or-task>' [--from WS-n] [--to WS-m] [--engine workflow|agent] [--attempts N] [--no-commit] [--no-confirm] [--dry-run] [--resume [<slug>]] [--force]"
allowed-tools: Skill(workstream-orchestrate), Workflow, Agent, AskUserQuestion, SendMessage, Bash, Read, Write, Edit, Glob, Grep, ToolSearch
---

# Workstream Orchestrate

Run the `workstream-orchestrate` skill: turn a plan into a human-confirmed **kickoff contract**, then
execute it **one workstream at a time** through a gated `code → validate → commit` loop. **The driver
never writes production code — it grounds the plan, authors the contract, delegates each workstream to
subagents, runs the gates itself, and commits one Conventional Commit per validated workstream.**

## Arguments

Parse from `$ARGUMENTS`:

```
'<plan-path-or-task>' [--from WS-n] [--to WS-m] [--engine workflow|agent] [--attempts N]
                      [--no-commit] [--no-confirm] [--dry-run] [--resume [<slug>]] [--force]
```

- `<plan-path-or-task>` (required) — a readable file is the authoritative plan; any other text is a
  raw task prompt, which triggers a draft-plan-and-confirm phase first.
- `--from WS-n` / `--to WS-m` — run only a contiguous range of workstreams (default: all, in order).
- `--engine workflow|agent` (default `workflow`) — one Workflow per workstream, or the identical
  loop via direct Agent calls; auto-falls back to `agent` if the Workflow tool is unavailable.
- `--attempts N` (default `3`) — max code→validate iterations per workstream before halting.
- `--no-commit` — run code→validate but leave the validated changes staged (no commit phase).
- `--no-confirm` — skip the between-workstream human checkpoint (still stops on refuted hard gate,
  behavior-changing ambiguity, or a shared/prod-DB migration).
- `--dry-run` — generate and confirm the kickoff contract, then stop before executing.
- `--resume [<slug>]` — continue a prior run from `.workstream/<slug>/`; committed workstreams are
  skipped (most recent run when no slug given).
- `--force` — ignore existing run state and start fresh.

## Process

Invoke the `workstream-orchestrate` skill and forward `$ARGUMENTS`. The skill will:

1. **(Plan Draft)** — raw-prompt input only: draft a plan with a numbered workstream breakdown, save
   it per the project's plans convention, and get explicit confirmation — the confirmed plan is the
   contract's source.
2. **Pre-flight** — record git state (pre-existing changes preserved and kept out of every commit;
   feature branch if on a protected one), read the repo's `CLAUDE.md` conventions, discover the gate
   commands + commit flow, read the plan in full.
3. **Kickoff contract (Phase A)** — ground the plan's `file:line` anchors read-only, then derive the
   10-section contract (workstreams, gates, guardrails, hard gates, commit convention). One
   AskUserQuestion batch confirms it and raises any locked decision that looks wrong. `--dry-run` ends
   here.
4. **Workstream loop (Phase B)** — for each workstream, in order: one bounded `code → validate →
   commit` Workflow. An implementer applies only that workstream's scope; an independent adversarial
   validator re-runs the gates and **proves or refutes the declared server-side hard gates**; on a
   green, validated workstream the skill makes one Conventional Commit staging only its files. Failing
   validation loops back to code (≤`--attempts`), then halts and surfaces the findings. A human
   checkpoint follows each commit (unless `--no-confirm`).
5. **Close-out & report** — verify the Definition of Done (all workstreams committed and green, every
   hard-gate proof on record, declared round-trips demonstrated), honor project wiki/log conventions,
   then a faithful report: per-workstream commits, gate + hard-gate verdicts, deviations, residual
   risks. **Nothing is pushed and no PR is opened unless you ask.**

## Output

A resumable run record under `.workstream/<slug>/` (the kickoff contract, per-agent reports, state),
one Conventional Commit per validated workstream on the feature branch, and the final report.
Interrupted or halted runs continue with `--resume`.
