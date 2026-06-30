---
name: "bespokeagentics:data-ui-craft"
description: "Audit and implement the craft details that make a data-dense UI work, across three pillars: data-driven form (categorical → chips, numeric → right-aligned tabular figures, long text → truncate + reveal, inactive rows → shaded, time-series → timeline/chart not a table), progressive disclosure & the spectrum of explicitness (place each control by frequency × importance; sequence onboarding), and invisible UI (tooltips, click-to-copy, comment indicators, and complete empty/loading/error/hover/focus states). Detects the project stack, writes a severity-rated report (markdown + HTML), then fixes the accepted findings in place and scaffolds a reusable React/Tailwind primitives kit. For dashboards, data tables, admin panels, data grids, and list/detail views."
argument-hint: "[mode: audit|implement|audit-and-implement] [path]"
allowed-tools: Skill(data-ui-craft), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Data-UI Craft

Run the `data-ui-craft` skill: audit a data-dense interface against the three pillars of data-UI
craft, then (by default) implement the fixes you accept — matching the project's stack and
conventions, and scaffolding a reusable primitives kit for the parts worth reusing.

## Arguments

Parse from `$ARGUMENTS`:

```
[mode: audit|implement|audit-and-implement] [path]
```

- `mode` (optional, default `audit-and-implement`) — `audit` writes the gap report only;
  `implement` applies fixes (and offers the primitives kit) without a fresh audit;
  `audit-and-implement` audits, lets you choose what to fix, then implements.
- `path` (optional) — scope to a component, directory, or route. Defaults to the data-display
  surfaces discovered by the skill.

## Process

Invoke the `data-ui-craft` skill and forward `$ARGUMENTS`. The skill will:

1. **Detect** the stack — framework, styling primitive, data-grid library, and existing utilities
   (`cn`, an icon set, an existing Tooltip/Popover/Badge) so fixes match and nothing is duplicated.
2. **Discover** the data-display surfaces (tables, grids, lists, cards, dashboards, detail panels)
   and map each column/field to its data type.
3. **Audit** each surface against the rule catalog (Pillar 1 `DF*`, Pillar 2 `PD*`, Pillar 3 `IU*`),
   severity-rating every finding with a `file:line` and a fix pointer, and writing both
   `./data-ui-craft-audit.md` and `./data-ui-craft-audit.html`.
4. **Choose** (in `audit-and-implement`) — an AskUserQuestion interview to frame intent (fix the
   serious issues vs. also take polish + opportunities), confirm which findings are real and
   in-scope, and decide whether to scaffold the primitives kit.
5. **Implement** the accepted set — in-place edits (alignment, chips, truncation, tooltips, copy,
   hover-gated actions, empty/loading/error branches), preferring column-def changes when a data
   layer exists, plus the reusable primitives kit (default `src/components/data-ui/`).
6. **Verify** — type-check, lint, and a narrow/wide layout sanity pass.

## Output

`./data-ui-craft-audit.md` + `./data-ui-craft-audit.html` (the report), in-place code edits for the
accepted findings, and (if chosen) a `src/components/data-ui/` primitives kit. Wiki-logged when a
vault exists. The destructive step (editing code) is always gated behind your explicit choice.
