---
name: "agentnative:chore-crons"
description: "Set up scheduled agents for the maintenance work developers skip: inventories the repo's neglected tail with git/grep evidence (untested critical paths, SDK coverage gaps vs upstream spec, stale skills/prompts, dep/docs/changelog drift), then — after an interview picks chores, runners, and budgets — generates cron runners (GitHub Actions schedule + claude-code-action v1, Claude Code Routines, or Cowork scheduled tasks) each with a self-verification step, a single rolling tracking issue/PR so output accumulates instead of spamming, idempotency guards, turn budgets, and cost telemetry."
argument-hint: "[mode: plan|implement] [chores: 'regression-backfill,dep-updates']"
allowed-tools: Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
disable-model-invocation: true
---

> **How this command loads its skill.** `chore-crons` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/chore-crons/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Chore Crons

Follow the `chore-crons` skill (loaded as described above): find what this repo neglects, then put trustworthy scheduled agents
on it.

## Arguments

Parse from `$ARGUMENTS`:

```
[mode: plan|implement] [chores]
```

- `mode` (optional, default `implement`) — `plan` writes the scored chore inventory + proposed
  runner set to `./plans/chore-crons.md` without touching `.github/`; `implement` interviews,
  then writes the runners.
- `chores` (optional) — comma-separated chore keys to scope to: `regression-backfill`,
  `sdk-gap-fill`, `skill-tuning`, `dep-updates`, `docs-drift`, `changelog`, `stale-sweep`.

## Process

Follow the `chore-crons` skill (loaded as described above) and forward `$ARGUMENTS`. The skill will:

1. Inventory the neglected tail with evidence (change-frequency × incident hotspots without
   tests, upstream-spec diffs, doc examples that no longer compile) plus an interview for the
   chores no grep finds
2. Score each chore value × automatability — only self-verifiable chores graduate to a cron;
   the rest become report-only
3. Interview: chore selection, runner + auth per chore, output/review policy, budget ceiling
4. Generate one runner per chore with the single-channel rule, empty-result rule,
   self-verification step, and manual dispatch handle
5. Verify: zizmor-clean, one manual fire per runner, and a double-fire idempotency test

Start small — one high-value chore and one trivially-verifiable one — and let two clean weeks
earn the rest.
