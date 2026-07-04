---
name: foundry-project
description: >-
  Start a new Foundry app from the memorialized foundry-base design system instead of
  regenerating it. Seeds the canonical base (tokens + @foundry/ui + Storybook — the
  source of truth), then ports ONLY the net-new, product-specific screens from a Claude
  design export on top of it, reusing existing canon components instead of re-creating
  them. USE THIS whenever the user is starting, spinning up, scaffolding, or
  bootstrapping a NEW FOUNDRY project/app/storybook, says "use the Foundry base", "seed
  a Foundry app", "new Foundry app from this design", "build a Foundry app", "another
  Foundry product", or hands over a design zip AND mentions Foundry / their existing
  component library. Prefer this over design-zip-to-library any time Foundry branding or
  the existing @foundry/ui library is in play — design-zip-to-library builds a library
  from scratch; THIS one starts from the base and only adds what's missing. Also governs
  reuse-first when asked to "add a component" to a Foundry project.
---

**Invocation.** `/foundry-project --name <app> [--design "<path-to-design.zip>"] [--out <dir>]`.
Parse the app name, an optional design zip, and flags from the user's message. If no
name is given, derive one from the design or ask. If no design zip is given, just seed
a clean Foundry app (the base) ready to build in.

# Foundry project

You start a **new Foundry app** from `foundry-base` — the canonical, indexed Foundry
design system (see `foundry-base.json` / `CLAUDE.md` in that repo). The base is the
**source of truth**: tokens, the `@foundry/ui` canon (buttons, cards, inputs, chips,
icons…), the Storybook host, and the reuse-first governance are already built and
tested. Your job is to **stand up the base and add only what's new** for this product —
never to regenerate the design system.

This is the companion to `design-zip-to-library`. That skill builds a library from a
design zip from scratch (empty scaffold → port everything). This skill starts from the
finished base and **ports only the components the base doesn't already have**, reusing
canon everywhere it overlaps. Reuse is the whole point — the base is a convergence
point for multiple products, so every avoidable duplicate is future dedup debt.

## Building blocks you reuse (don't rebuild)

- **This skill's scripts** (`scripts/`): `seed_from_base.py` (deterministic seed) and
  `plan_ports.py` (reuse-first diff: design inventory vs base index).
- **design-zip-to-library** (sibling skill): its `scripts/analyze_zip.py` (design →
  `analysis.json` inventory) and `scripts/tokens_to_tailwind.py` (only if this design
  changes tokens). Path: `../claude-design-to-app-workflow/scripts/`.
- **Agents** (plugin `agents/`): `component-porter` (ports one component) and
  `library-reconciler` (final consistency sweep). Same contracts as design-zip-to-library.
- **The base's own governance**: `foundry.index.json`, `CATALOG.md`, `CLAUDE.md`, and
  the `/foundry-component-check` skill ship inside the seed and drive reuse decisions.

## Workflow

### 0 — Preflight
Confirm `bun >= 1.1` and `python3`. Resolve `--name` (kebab slug), optional `--design`
zip path, and `--out` (default `./<name>-workspace`). The base defaults to the GitHub
source of truth; set `$FOUNDRY_BASE_REPO` or pass `--from` to `seed_from_base.py` for a
local/offline base.

### 1 — Seed the base
```
python3 scripts/seed_from_base.py --to <out> --name <name>
```
This clones the base, drops its history, renames the root package (keeping the
`@foundry/*` scope), installs, and verifies `typecheck` + `index:check` green. The new
app now has the entire Foundry design system + a worked reference app (`apps/docbook`)
+ the component index. **If no design zip was given, stop here** — report the seeded
workspace and how to run Storybook; the user builds their screens reusing canon.

### 2 — Inventory the new design (only if `--design` given)
```
python3 ../claude-design-to-app-workflow/scripts/analyze_zip.py "<design.zip>" --out <out>/.foundry/analysis.json
```
Read the resulting `analysis.json`. If the design introduces genuinely new **tokens**
(different brand), run `tokens_to_tailwind.py` — but a Foundry product normally shares
the base tokens, so usually skip this and keep the base's tokens.

### 3 — Plan reuse vs port (the reuse-first diff)
```
python3 scripts/plan_ports.py --analysis <out>/.foundry/analysis.json \
    --index <out>/foundry.index.json --app <name> --out <out>/.foundry/plan.json
```
The plan buckets every design component into **reuse** (already in canon — wire from
`@foundry/ui`), **ambiguous** (a close match — confirm), and **port** (net-new), plus
**pages** (product screens). Present the summary to the user and **confirm the
ambiguous bucket** — default to reusing/extending canon over porting a near-duplicate.
Move confirmed ambiguous items into reuse or port accordingly.

### 4 — Port only the net-new components (parallel)
For each item in the `port` bucket, dispatch a **`component-porter`** agent (fan out in
dependency order, `tsc --noEmit` gate between waves — same protocol as
design-zip-to-library's `references/parallel-porting.md`). Each porter's contract:
- `out_path`: `packages/ui/src/components/apps/<name>/…` (product section, **not** canon)
- `conventions`: the seed's `CLAUDE.md` → "Component library idiom"
- `golden_ref`: the closest existing component (a canon primitive for atoms, an
  `apps/docbook/*` composite for composites) — the base is your reference library
- `inventory_entry`: the component's record from `analysis.json`
- `ported_deps`: reused canon exports (from the `reuse` bucket) + already-ported siblings

Porters **must reuse canon** (Button, Card, Input, Icon, …) rather than re-creating
atoms. Re-export each new component from `packages/ui/src/index.ts`.

### 5 — Build the pages
Port the design's screens as `Apps/<Name>/Pages/…` stories under
`apps/storybook/src/pages/`, rebuilt from ported + reused components (mock data in
`apps/storybook/src/fixtures/`). Full-viewport, same as the base's docbook pages.

### 6 — Index, reconcile, verify, hand off
- `bun run index` — register the new components (they appear under `Apps/<Name>/…`).
- Dispatch **`library-reconciler`** for an idiom-drift sweep over the new section.
- Gate: `bun run typecheck && bun run index:check && bun run build-storybook`.
- Tell the user how to run it (`bun run storybook`) and what was reused vs added.

## Adding a component later (reuse-first governance)

Inside a seeded project, any "add a component" request runs `/foundry-component-check`
first: consult `foundry.index.json`, reuse/extend canon when possible, and only add new
components under `apps/<name>/` (product-specific) or — if it's genuinely reusable —
`canon/` (then it should be promoted back to `foundry-base`). Always `bun run index`
after.

## Promote-back (keep the base the source of truth)

If you improve or add a **canon** component in a product, it belongs in `foundry-base`,
not a fork: commit it there (or open a PR) so every Foundry app inherits it. Product
sections (`apps/<name>/`) stay in the product. The index's `provenance` field tracks
lineage so future library merges can dedup against canon.

## Report

State: the seeded workspace path, the reuse/port/pages counts, which canon components
were reused (by export name), which net-new components were added (and why nothing
existing fit), and the verification results.
