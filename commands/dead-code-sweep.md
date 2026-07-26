---
name: "bespokeagentics:dead-code-sweep"
description: "Post-session dead-code cleanup with regression proof. Resolves a scope (uncommitted work by default, a branch vs its base, or the whole project), runs the repo's own gates FIRST to record a baseline, finds candidates by tracing the diff plus the ecosystem's native detectors, cross-checks every candidate against dynamic references and framework conventions, then removes in gated waves — high-confidence auto-removed with gates re-run after every wave (a new failure restores the code), medium-confidence batch-confirmed in one interview, low-confidence report-only. Stale tests/mocks/snapshots swept with their subjects; a failing test is never deleted to reach green. Every removal evidence-cited and backed up under .dead-code-sweep/ with one-command restore. Never commits."
argument-hint: "[uncommitted|branch|project] [--base <ref>] [--report-only] [--out <dir>]"
allowed-tools: Skill(dead-code-sweep), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep, Agent
---

# Dead-Code Sweep

Run the `dead-code-sweep` skill against this repository with the arguments given: resolve the
scope, run the baseline gates before touching anything, discover and evidence-check candidates,
remove in gated waves with tiered confirmation, and write the evidence-cited report with restore
instructions.

ARGUMENTS: $ARGUMENTS
