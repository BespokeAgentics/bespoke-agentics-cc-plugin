---
name: "bespokeagentics:xstate-refactor"
description: "Refactor a feature's ad-hoc state logic + UI into an explicit XState v5 machine, statechart, or actor system. Analyzes every code path and UI dependency (parallel Explore agents, file:line evidence), designs the statechart with a mermaid diagram and a state↔UI coverage matrix, validates the model via an AskUserQuestion interview, writes an executable migration plan to ./plans/, then — only on explicit approval — implements the machine, wires the UI so every state has a decided visual answer, generates deterministic path-coverage (xstate/graph createTestModel) + UI state-coverage tests, installs XState v5 if missing, and retires the old code behind a grep-verified deprecation checklist."
argument-hint: "'<target>' [--mode plan|implement|full] [--style machine|statechart|actors|auto] [--out <dir>] [--no-tests] [--force]"
allowed-tools: Skill(xstate-refactor), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# XState Refactor

Run the `xstate-refactor` skill: recover the statechart a feature already implements implicitly,
validate it with the user, and migrate the code onto XState v5 — machine + UI wiring + deterministic
tests + deprecation of the old state logic. **No application code is edited before the approval gate.**

## Arguments

Parse from `$ARGUMENTS`:

```
'<target>' [--mode plan|implement|full] [--style machine|statechart|actors|auto] [--out <dir>] [--no-tests] [--force]
```

- `<target>` (required) — file path, directory, component name, or a description of the feature
  ("the checkout flow"); descriptions are resolved to files and confirmed before analysis.
- `--mode plan|implement|full` (default `full`) — `plan` stops at the validated migration plan;
  `implement` executes an existing plan; `full` = plan → approval gate → implement.
- `--style machine|statechart|actors|auto` (default `auto`) — nudge the model shape; `auto` lets the
  analysis recommend (including "don't use XState" when the target is trivially simple).
- `--out <dir>` (default `./plans`) — where the migration plan is written.
- `--no-tests` — skip test generation (discouraged).
- `--force` — re-run all phases even if intermediate outputs exist.

## Process

Invoke the `xstate-refactor` skill and forward `$ARGUMENTS`. The skill will:

1. **Pre-flight** — resolve the target files; detect XState (version), framework, test runner, TS,
   package manager.
2. **Behavior discovery** — parallel `Explore` agents inventory state variables & flag combinations,
   events & effects, and every UI dependency (plus outside consumers) → `behavior-map.md`, all
   `file:line`-cited, impossible-but-representable states enumerated.
3. **State model design** — statechart draft with mermaid diagram, guards/actions/actors traced back
   to the behavior map, impossible-states-eliminated table, draft UI coverage matrix (gaps ⚠).
4. **Interview** — AskUserQuestion validates every inferred state and behavioral divergence, resolves
   each UI gap (build / intentionally invisible / defer), sets deprecation appetite.
5. **Migration plan** — self-contained, executable plan to `./plans/{slug}-xstate-migration.md`;
   wiki-ingested when a vault exists.
6. **Gated implementation** — on approval: setup if needed → machine in isolation → tests green
   (path coverage + unit) → UI wired per matrix + UI coverage tests → deprecation checklist executed
   and grep-verified → project typecheck/lint/tests green.
