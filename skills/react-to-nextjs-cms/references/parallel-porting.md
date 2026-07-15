# Parallel porting — ultracode wave protocol

How Phases 5–6 fan the per-file work (design-system components, page views, content externalization) out
across many parallel subagents without losing idiom consistency. The main thread is the orchestrator: it
builds waves, writes the contract, dispatches agents, gates between waves, and reconciles. Subagents port;
they don't decide conventions. (Same shape as the sibling skill's protocol, adapted for a Next.js + Tina
target.)

## Step 1 — Golden reference (main thread, before any fan-out)

1. Port the most-used design-system primitive (usually `Button`) yourself, per
   `component-porting.md` + the shared `claude-design-to-app-workflow/references/component-conversion.md`.
   This resolves every judgment call once: Server vs Client default, token→utility mapping, prop typing,
   icon approach, file layout.
2. Do one **content-externalized page** end-to-end too (usually `home`): its `content/pages/home.json`, the
   `page` collection templates, the RSC-fetch → client-`useTina` split, and `tinaField` on each editable
   element. This is the golden reference for content work.
3. Distill `<work>/conventions.md` (~40 lines): the RSC/client rule, token classes, prop typing, the block
   component shape, the `data-tina-field` placement rule (real elements only), file/import conventions.
4. Verify both compile (`pnpm build` or `tsc --noEmit`) **before** fanning out — a broken reference
   replicates its breakage across every agent.

## Step 2 — Build dependency waves

From `analysis.json`:
1. **Wave 1** — leaf design-system primitives (depend on no other DS component).
2. **Wave 2+** — DS components whose deps are all in earlier waves.
3. **Shell wave** — `Header`/`Footer`/eyebrow from `site/shared.jsx`.
4. **Page wave** — one agent per page: ports the view component AND externalizes its content
   (`content-porter` role), composing only ported components + the fixed collection schema.

Print the wave plan before dispatching — it's the user's last cheap chance to catch a wrong inventory.

## Step 3 — Dispatch (full fan-out per wave)

All members of a wave launch simultaneously, one agent each, in a single multi-Agent message. Each prompt
carries:

```
kind:            ds-component | shell | page
name:            <ComponentName or page id>
source:          <site/*.jsx or _ds bundle ref + the rendered *.html snapshot for visual truth>
out_path:        components/ds/<name>/  |  components/shared/  |  app/(site)/<route>/ + content/pages/<id>.json
conventions:     <work>/conventions.md
golden_ref:      components/ds/button/  (and app/(site)/page.tsx + home-view.tsx for pages)
token_theme:     app/globals.css (the @theme mapping)
collection:      tina/collections/page.ts (pages only — the fixed schema to target)
porting_doc:     <skill>/references/component-porting.md  (+ content-modeling.md for pages)
shared_playbook: claude-design-to-app-workflow/references/component-conversion.md
ported_deps:     <paths of already-ported components this one imports>
```

Page agents also receive the list of ported component exports so they import rather than re-implement, and
the content-candidate list for their page.

## Step 4 — Between-wave gate (main thread)

After each wave returns:
1. `pnpm build` (or `tsc --noEmit` for speed) — App Router will flag `"use client"`/hook/Server-Component
   boundary errors here.
2. Fix trivial failures directly; re-dispatch a porter once with the error text for structural ones; take
   over on a second failure.
3. Only then dispatch the next wave — wave N+1 imports wave N.

Track with TaskCreate/TaskUpdate — one task per wave, not per component.

## Step 5 — Reconciliation sweep (start of Phase 8)

One `reconciler` agent over `app/` + `components/` + `tina/` + `content/`. Parallel porting drifts predictably:

- **RSC/client boundary**: no `"use client"` on purely presentational primitives; no hook/handler in a
  Server Component.
- **`data-tina-field` placement**: on real HTML elements, never on React components; present on every
  editable element (grep visible copy for any still-hardcoded strings a porter missed).
- **Token usage**: semantic utilities from the `@theme`, not stray hex (except brand colors).
- **Content shape**: every page reads from `data.blocks` (no leftover hardcoded copy); `content/*.json`
  matches the collection schema; `__typename` switch covers every template.
- **Imports/exports**: block components barrel-exported; no `window.*`, no `data-lucide` global.

The reconciler fixes mechanical drift directly and **reports** judgment calls — the main thread decides
those, then runs the Phase 8 build/dev verification.

## Failure economics

A porter that fails twice costs less than a wrong convention propagated silently. Porters follow
`conventions.md` even where they disagree, and surface disagreements in their report instead of improvising.
The orchestrator owns taste; the agents own throughput.
