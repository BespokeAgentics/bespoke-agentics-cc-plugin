---
name: "funcspec-evaluate"
description: "Page-by-page functional evaluation of a Storybook workspace. Inventories pages/composites, runs the Stage-1 framing interview, launches parallel page-evaluator agents, optionally verifies visually against running Storybook, and synthesizes a cross-page feature inventory with an ambiguity register. Stops before plan generation."
argument-hint: "[<workspace>] [--pages all|a,b] [--visual auto|on|off] [--out <dir>]"
allowed-tools: Skill(funcspec), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Funcspec — Evaluate

Run Phases 0–4 of the `funcspec` skill: inventory → Stage-1 interview → parallel
page-by-page evaluation → visual verification → cross-page synthesis.

## Arguments

Parse from `$ARGUMENTS`:

```
[<workspace>] [--pages all|<comma-list>] [--visual auto|on|off] [--out <dir>]
```

- `<workspace>` (optional) — Storybook workspace root; defaults to auto-detection in CWD.
- `--pages` — which pages to evaluate (composites always run). Default `all`.
- `--visual` — visual verification pass. Default `auto`.
- `--out` — output directory. Default `<workspace>/docs/funcspec`.

## Process

Invoke the `funcspec` skill in **evaluate** mode (Phases 0–4 only) and forward
`$ARGUMENTS`.

The skill will:

1. **Inventory** — detect a `design-zip-to-library` `analysis.json` fast path or scan
   stories generically; write `page-inventory.json`; confirm the page list with the user.
2. **Interview (Stage-1)** — AskUserQuestion to establish purpose, roles, backend
   reality, auth, non-goals; digest to `context.md`.
3. **Evaluate (ultracode)** — composites sequentially, then ALL pages simultaneously
   via a full fan-out of `page-evaluator` agents (one per page, no batch cap);
   schema-validate every profile as it lands.
4. **Verify visually** — when enabled and feasible, walk rendered stories and extend
   profiles; otherwise note the skip.
5. **Synthesize** — entity model, route map, feature inventory with traceability,
   shared services, consolidated ambiguity register.

## Output

`<out>/page-inventory.json`, `<out>/context.md`, `<out>/profiles/*.json`,
`<out>/synthesis.json`, plus a summary: pages evaluated, features inferred, entities,
operations, open ambiguities (blocking count). Ends by pointing to
`/bespoke-agentics:funcspec-plan` for validation + deliverables.
