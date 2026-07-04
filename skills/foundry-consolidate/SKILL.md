---
name: foundry-consolidate
description: >-
  Merge another existing Foundry component library into the canonical foundry-base,
  deduping against the base's canon so nothing gets duplicated. USE THIS when the user
  wants to "consolidate", "merge", "join", "fold in", "unify", "combine", or "bring
  together" component libraries — e.g. "merge the Sift UI library into the base",
  "consolidate my Foundry libraries", "fold the scope-workspace components into
  foundry-base", "we have three @foundry/ui libraries, unify them", or "dedupe our
  component libraries into one source of truth". It inventories the incoming library,
  diffs every component against foundry-base's foundry.index.json, and buckets each into
  reuse (already in canon), reconcile (near-duplicate — confirm), promote-to-canon
  (net-new reusable primitive), or add-as-app (product-specific) — then merges the
  net-new components on top of the base, rethemed to base tokens, recording provenance +
  similar_to lineage. Distinct from foundry-project (which SEEDS a new app from the base)
  and design-zip-to-library (which builds a library from a design zip): this MERGES an
  existing library INTO the base.
---

**Invocation.** `/foundry-consolidate --incoming <path-to-other/packages/ui> --lib <slug> [--base <path>]`.
Parse the incoming library path, a slug for it (used as provenance + app-section name),
and optionally the base path (defaults to the local `foundry-base` checkout / clone).

# Foundry consolidate

You merge **another existing Foundry library** into `foundry-base` — the canonical
design system (the source of truth). The base already carries `provenance` and
`similar_to` hooks in its index precisely so libraries can be folded in without
creating duplicates. Your job: dedup the incoming library against canon, promote its
genuinely-new reusable primitives into canon, route product-specific pieces to an app
section, and keep the base green — so the base steadily becomes the single library
every Foundry app shares.

The guiding rule is **reuse over duplicate**. Every incoming component that canon
already covers must be dropped in favor of canon; every near-duplicate must be
reconciled (reuse/extend, not fork); only genuinely-new components are added.

## Building blocks you reuse

- **This skill's script** `scripts/plan_merge.py` — the consolidation differ.
- **The base's index/governance**: `foundry.index.json` (dedup target), `CLAUDE.md`
  (idiom), `scripts/build-index.mjs` (regenerate after merging).
- **Agents** (plugin `agents/`): `component-porter` (retheme + add one component) and
  `library-reconciler` (final idiom sweep). Same contracts as the other skills.

## Workflow

### 1 — Plan the merge (the dedup differ)
```
python3 scripts/plan_merge.py --incoming <other>/packages/ui \
    --index <base>/foundry.index.json --lib <slug> --out <base>/.foundry/merge-<slug>.json
```
Buckets every incoming component:
- **reuse-canon** — exact match to a canon component → drop the incoming copy, use canon.
- **reuse-app** — exact match to an existing app component → already covered there.
- **reconcile** — a close (≥0.6) but not exact match → **confirm with the user**: reuse/extend
  the base match, or promote under a distinct name. Never silently fork a near-duplicate.
- **promote-canon** — net-new AND primitive-shaped → add to base `canon/primitives/`.
- **app-new** — net-new AND product-specific → add under `apps/<slug>/`.

### 2 — Confirm the judgment buckets
Present the summary. Walk the **reconcile** bucket with the user (each is a real
"is this the same component?" call) and confirm the **promote-canon** set (these
change the shared canon everyone inherits, so they deserve a glance). Move items
between buckets per the user's answers.

### 3 — Merge the net-new components (parallel, rethemed to base tokens)
The incoming library has its OWN tokens; canon is themed by the base tokens. So each
merged component is **rethemed**, not copied. For every confirmed **promote-canon** /
**app-new** item, dispatch a `component-porter` agent:
- `source_path`: the incoming component file
- `out_path`: `canon/primitives/<name>.tsx` (promote) or `apps/<slug>/<name>.tsx` (app)
- `conventions`: the base `CLAUDE.md`; `golden_ref`: the closest existing canon component
- reuse canon atoms (`Icon`, `cx`, tokens); translate the incoming `var(--…)` to the base's
  semantic utilities (exactly as the base's own components do)
- add a story (`Canon/Primitives/<Name>` or `Apps/<Slug>/<Name>`); the orchestrator owns
  the barrel — porters do not edit `index.ts`

Fan out in waves with a `tsc --noEmit` gate between them. For **reconcile→reuse**
items, wire the base's existing component instead of adding anything.

### 4 — Record lineage, index, verify
- Add each merged component's barrel export (orchestrator-owned, single edit).
- `bun run index` — new components appear with `provenance: "<slug>"`; set `similar_to`
  on reconciled/near-duplicate pairs so the dedup history is queryable.
- Dispatch `library-reconciler` over the newly-added set for idiom drift.
- Gate: `bun run typecheck && bun run index:check && bun run build-storybook`.

### 5 — Promote back + report
The base is the source of truth: commit the merge to `foundry-base` (or open a PR) so
every app inherits the enriched canon. Report: components scanned, reused vs reconciled
vs promoted vs app-added counts, which incoming components were dropped as duplicates,
and the new canon additions by name.

## Consolidating several libraries
Run once per incoming library, each with its own `--lib` slug. Because dedup is always
against the *current* base index, later libraries automatically reuse primitives that
earlier ones promoted — the base converges instead of accumulating duplicates.
