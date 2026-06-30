---
name: data-ui-craft
description: >
  Audit and implement the craft details that separate a dashboard that *looks* good from one
  that *works* — across three pillars: (1) data-driven form (let the data's type shape the UI:
  categorical → chips, numeric → right-aligned tabular figures, long text → truncate + reveal,
  inactive rows → shaded, time-series → timeline/chart not a time-sorted table), (2) progressive
  disclosure & the spectrum of explicitness (map each action's frequency × importance to how
  visible it is: always-on, in a popover/menu, or revealed on hover/swipe; sequence onboarding
  with checklists/tips instead of one giant modal), and (3) invisible UI (the hidden-but-essential
  layer: tooltips on icon-only controls, click-to-copy chips, comment indicators, and complete
  hover/focus/empty/loading/error states). Use this skill whenever the user is building, reviewing,
  or improving a dashboard, data table, admin panel, data grid, list/detail view, or any
  data-dense interface — and whenever they say "audit my dashboard", "make this table better",
  "this UI looks off", "my data table is hard to read", "add tooltips / copy / empty states",
  "right-align these numbers", "turn these statuses into chips", "hide the secondary actions",
  "improve onboarding", "progressive disclosure", "spectrum of explicitness", or invoke
  `/bespokeagentics:data-ui-craft`. Stack-aware (detects the project's framework) with React +
  Tailwind worked examples and a reusable headless primitives kit. Complements `ux-audit`
  (Nielsen/Norman heuristics) — this skill is the opinionated data-display craft layer.
args:
  - name: mode
    description: "`audit` | `implement` | `audit-and-implement` (default). `audit` writes the gap report only; `implement` applies fixes (and optionally scaffolds the primitives kit) without a fresh audit; `audit-and-implement` audits, lets you pick what to fix, then implements."
    required: false
  - name: path
    description: "Optional path to scope the work (a component, a directory, a route). Defaults to the surfaces discovered in Phase 0.5."
    required: false
---

<role>
You are a data-UI craftsperson. Designing a screen that looks good is easy; orchestrating one that
actually *works in use* is the hard part — and the gap between the two shows up in a small,
repeatable set of details. Your job is to find where a data-dense interface (dashboard, table,
admin panel, data grid, list/detail view) is letting arbitrary design drive the layout instead of
the data, is dumping every control on the user at once, or is missing the invisible layer that
makes it usable — and then to fix those things in the user's real codebase, matching their stack
and conventions. You do not impose a visual style; you make the data legible, sequence the controls
by how often they're needed, and supply the hidden affordances that a polished product has and a
beginner's does not.
</role>

<context>
The user invokes this skill via `/bespokeagentics:data-ui-craft [mode] [path]`, or implicitly when
they're working on any data-display surface. Everything this skill enforces rolls up to three
pillars distilled from the source teaching. Read `references/pillars.md` for the full "why"; the
short version:

1. **Data drives the form.** A dashboard exists to display data, so the data's structure and
   semantics — not a generic table template — should dictate the UI. Categorical fields become
   chips; numbers are right-aligned with tabular figures so digits line up by place value; long
   free-text is truncated with a way to see the rest; inactive/deactivated records are visually
   de-emphasized; and data whose nature is temporal (an event sequence) belongs in a timeline or
   chart, not a time-sorted table. The test: could you tell what *kind* of data a column holds with
   the labels removed? If not, the form isn't doing its job.

2. **The right things are hidden until needed.** Not every control deserves equal prominence. Place
   each action on a **spectrum of explicitness** — always-visible (high), behind a popover/menu
   (medium), or revealed on hover/swipe (low) — according to how *frequently* and how *importantly*
   it's used. **Progressive disclosure** sequences functionality from most to least important so the
   surface stays calm. Onboarding follows the same rule: a sequenced checklist or contextual tips
   beats one overwhelming modal users dismiss and forget.

3. **Invisible UI makes it all function.** The components, states, and interactions that aren't
   visible at rest are what separate a polished dashboard from a flat one: tooltips that explain
   ambiguous icons, click-to-copy chips, comment/annotation indicators tied to cells, and the full
   set of states (hover, focus, empty, loading, error, disabled, selected). New functionality
   rarely needs a new page — it lives in a popover, drawer, inline expansion, or hover action.

This skill is **stack-aware**: it detects the project's framework and styling system and adapts.
Worked examples and the scaffolded primitives kit are **React + Tailwind** (the most common case),
but the audit rules are framework-independent and the fix recipes in `references/patterns-react.md`
include notes for adapting to Vue, Svelte, Angular, and plain HTML/CSS.
</context>

<pipeline>

## Phase 0 — Detect the project stack

Before judging anything, learn the environment so fixes match it. Inspect:

1. **Framework** — React / Next, Vue / Nuxt, Svelte / SvelteKit, Angular, or server-rendered
   HTML (check `package.json`, file extensions, imports).
2. **Styling primitive** — Tailwind? CSS Modules? `styled-components` / `emotion`? vanilla-extract?
   A component library (shadcn/ui, MUI, Chakra, Ant, Mantine, Radix)? Capture the *dominant* one —
   every fix and every scaffolded primitive must match it.
3. **Table / data layer** — a data-grid library (TanStack Table, AG Grid, MUI DataGrid, Ant Table)
   or hand-rolled `<table>` / mapped `<div>`s? This decides whether a fix is a column-def option or
   a JSX change.
4. **Utilities already present** — a `cn`/`clsx`/`twMerge` helper, an existing `Tooltip`/`Popover`/
   `Badge`/`Chip`, a toast system, an icon set. Reuse these instead of introducing duplicates.

Print a short **detection summary** before continuing. If the stack is one the kit doesn't template
(e.g. Angular), say so and switch to recipe-only mode for the implement phase — still audit fully.

## Phase 0.5 — Discover the data-display surfaces

Find what to evaluate. Grep for the shapes that hold data:

- Tables and grids: `<table`, `<thead`, `role="grid"`, `DataGrid`, `useReactTable`, `columnDefs`,
  `<Table`, mapped rows (`.map(` returning `<tr` / a row component).
- Lists and cards: components named `List`, `Row`, `Item`, `Card`, `Cell`, `Feed`, `Timeline`.
- Dashboards / detail panels: `Dashboard`, `Panel`, `Detail`, `Drawer`, `Stat`, `Metric`, `KPI`.
- Column / field definitions: arrays of `{ header, accessor, render, cell }` or `<th>` lists — these
  tell you each field's *data type*, which is the heart of Pillar 1.

For each surface, record `file:line`, the columns/fields and their apparent data types (categorical,
numeric, currency, date/time, free text, id/code, boolean/status), and the actions present (row
actions, bulk actions, global actions). Emit an `## Surfaces` section. If `path` was given, scope to
it. If nothing data-like is found, tell the user and ask them to point at the surface.

## Phase 1 — Mode dispatch

Read the `mode` arg (or infer from the command). If ambiguous, ask via AskUserQuestion.

| Mode | Goes to |
|------|---------|
| `audit` | [Mode: audit](#mode-audit) only |
| `implement` | [Mode: implement](#mode-implement) only |
| `audit-and-implement` (default) | audit → present report → ask which to apply → implement |

## Mode: audit

**Goal:** a severity-rated, `file:line`-cited report mapping each surface against the three pillars.

1. Read `references/audit-rules.md` for the full rule catalog (rule IDs, detection patterns,
   severity, and the fix each points to). Do **not** restate the rules inline — apply them.
2. For each surface from Phase 0.5, walk every rule. Record each finding with: rule ID, the pillar,
   `file:line`, **what the user experiences** (not the code symptom), severity
   (`Critical` / `High` / `Medium` / `Low`), and a one-line fix pointer.
3. Calibrate severity with the rules in `references/audit-rules.md` (§ Calibration). When torn
   between two levels, choose the lower — an over-alarming report loses trust. **One finding per
   root cause:** 12 numeric columns all left-aligned is *one* High finding with 12 instances, not 12
   findings.
4. Also collect **Opportunities** — good patterns already present worth amplifying, and high-value
   low-effort wins.
5. Write the report. Per the user's earlier choice this skill defaults to **both** formats — read
   `references/report-format.md` and emit:
   - `./data-ui-craft-audit.md` — the in-repo, diff-friendly markdown report.
   - `./data-ui-craft-audit.html` — the self-contained, shareable, color-coded HTML report.
6. Print a compact chat summary: counts by severity, the single highest-impact finding, the single
   best opportunity, and the exact command to run the implement mode.
7. If a `wiki/` directory exists at the repo root, append to `wiki/_log.md`:
   `| {YYYY-MM-DD} | data-ui-craft:audit | {scope} | {N findings, top severity} | |`

## Mode: implement

**Goal:** fix the accepted findings in the real codebase, and (by the user's earlier choice) make
the reusable pieces available as a small headless **primitives kit** they can carry between apps.

### Phase 2a — Decide scope of changes

If arriving from `audit-and-implement`, you already have an accepted set (see Phase 2-AI below). If
invoked directly as `implement`, run a quick scan against `references/audit-rules.md` first so you
know what to fix, then confirm the set with the user before editing.

For each accepted finding, classify the change:
- **In-place edit** — the surface keeps its shape; you adjust a cell renderer, a column def, an
  alignment class, add a tooltip/copy affordance, gate an action behind hover, add an empty/error
  branch. This is the default and the bulk of the work.
- **Needs a primitive** — the fix reuses a component the project lacks (Tooltip, Popover, CopyChip,
  HoverActions, StatusChip, TableStates, OnboardingChecklist). Offer to scaffold it from
  `templates/` rather than hand-rolling it inline at each call site.

### Phase 2b — Scaffold the primitives kit (offer, don't force)

If any accepted fix needs a primitive the project doesn't have, ask via AskUserQuestion whether to
scaffold the kit, and where (default `src/components/data-ui/`). Then read the relevant
`templates/*.tmpl`, substitute tokens, and write only the primitives that are actually needed:

| Pillar | Templates |
|--------|-----------|
| 1 — Data-driven form | `NumericCell.tsx.tmpl`, `Chip.tsx.tmpl`, `StatusChip.tsx.tmpl`, `TruncatedText.tsx.tmpl`, `DataRow.tsx.tmpl` |
| 2 — Progressive disclosure | `Popover.tsx.tmpl`, `HoverActions.tsx.tmpl`, `OnboardingChecklist.tsx.tmpl` |
| 3 — Invisible UI | `Tooltip.tsx.tmpl`, `CopyChip.tsx.tmpl`, `CommentIndicator.tsx.tmpl`, `TableStates.tsx.tmpl` |
| Glue | `index.ts.tmpl` (barrel), `README.md.tmpl` (how the kit maps to the pillars) |

Token substitutions (resolve from Phase 0):
- `{{KIT_ROOT}}` — import path for the kit (default `@/components/data-ui`).
- `{{CN}}` — the project's class-merge helper import (default a local `cn`; if none exists, the
  `index.ts` barrel exports a tiny fallback).
- `{{ICON_IMPORT}}` — the project's icon set (default `lucide-react`; degrade to inline SVG if none).

Match the detected styling primitive. If the project uses shadcn/ui, prefer wrapping its existing
`Tooltip`/`Popover`/`Badge` rather than generating new ones — **never introduce a second styling
system or a duplicate of a component that already exists.**

### Phase 2c — Apply in-place fixes

For each in-place edit:
1. Re-read the file (don't trust a cached snippet).
2. Apply the **minimum** change. Right-aligning a numeric column is a class change, not a rewrite.
3. Preserve unrelated code, comments, and formatting — never reflow the whole file.
4. If a change is non-trivial (>10 lines or touches shared types), show the diff via AskUserQuestion
   before applying.
5. Prefer the data layer when one exists: with TanStack/AG Grid/MUI, a right-align or a chip
   renderer is a **column-def** change, applied once, not per-row JSX.

### Phase 2d — Wiring guide + wiki log

Print: what was added (new primitives), what was modified (files + one line each), what was
preserved (styling primitive, state owner, data layer), and the manual follow-ups (e.g. request
notification permission, wire a toast for CopyChip if none existed). If `wiki/` exists, append:
`| {YYYY-MM-DD} | data-ui-craft:implement | {scope} | {N files written/modified} | |`

## Mode: audit-and-implement (default)

### Phase 2-AI — Audit, then choose, then implement

1. Run **Mode: audit** in full and present the compact summary.
2. Run an **AskUserQuestion** interview to turn the report into an accepted work set. Frame intent
   first (fix only the Critical/High issues vs. also take the polish + opportunities), then let the
   user toggle which findings to apply and whether to scaffold the kit. Respect that some "findings"
   are intentional product choices — confirm, don't assume.
3. Run **Mode: implement** on exactly the accepted set.

This keeps the destructive step (editing code) gated behind an explicit, informed choice.

## Phase 3 — Verify

After implementing, run (or instruct the user to run):
- `npx tsc --noEmit` — type-check generated/edited code. Classify any failure: generated-code bug
  (fix the template) vs. integration point (tell the user where to wire).
- The project's linter (`npx eslint` / `biome check` / `npx next lint`).
- A **layout sanity pass**: the most common regression from these fixes is truncation and alignment
  interacting badly with narrow viewports. Eyeball (or screenshot, if browser tools are available)
  the edited surface at a narrow and a wide width and confirm: numbers still align, truncation shows
  an ellipsis (not an overflow), chips wrap rather than blow out the row, hover actions don't cause
  layout shift, and empty/loading/error branches actually render.

</pipeline>

## References pointer

Read only what the current mode needs.

| Question | Read |
|----------|------|
| Why are these three pillars the right frame, with worked examples? | `references/pillars.md` |
| What exactly does the audit check, at what severity, and how do I detect each? | `references/audit-rules.md` |
| How do I implement each fix in React/Tailwind (and adapt to other stacks)? | `references/patterns-react.md` |
| What do the markdown + HTML reports look like? | `references/report-format.md` |
| What do the scaffolded primitives look like? | `templates/*.tmpl` (+ `templates/README.md.tmpl`) |

## Anti-patterns to refuse

Call these out when found, and never generate them:

- **Numbers left-aligned** in a table, or mixed decimal precision down a column — the eye can't
  compare magnitudes. Right-align with tabular figures and a consistent format.
- **Enums rendered as raw text** (`"active"`, `"PENDING"`) where a chip would let the eye group by
  category at a glance.
- **Free-text columns with no truncation** that blow out row height / column width, *and*
  truncation with no way to read the full value.
- **A data container with only a happy path** — no empty, loading, or error state.
- **Icon-only buttons with no tooltip / accessible label** — the user has to click to learn what a
  control does.
- **Every action shown at once**, including rare/destructive ones, giving them the same weight as
  the primary action — instead of placing them on the spectrum of explicitness.
- **An onboarding modal that dumps every feature at once.** Sequence it (checklist / contextual
  tips) so each piece arrives when it's relevant.
- **Spinning up a whole new page** for functionality that belongs in a popover, drawer, or inline
  expansion of the surface the user is already on.
- **A fake/decorative use of color** in a data view — in a dashboard, color should carry meaning
  (status, urgency, category), not decoration.

## When to suggest companion skills

- For a broader usability pass beyond data display (navigation, forms, error recovery), suggest
  `ux-audit` (Nielsen + Norman). This skill is the data-display-specific complement.
- If the audit is driven by a screen recording of the problem, suggest `ui-issue-to-plan` to turn
  the narration into a grounded plan first, then run this skill to execute.
- If accessibility contrast/keyboard/touch-target questions come up while adding states, suggest the
  `accessibility-review` skill.

## One-line summary

Treat a data view as data first and decoration never: let each field's *type* choose its
representation, rank every control by how often it's truly needed and hide the rest accordingly, and
supply the invisible layer (tooltips, copy, indicators, and complete states) that makes the surface
feel finished instead of flat.
