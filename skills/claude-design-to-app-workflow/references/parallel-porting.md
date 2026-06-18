# Parallel Porting — Ultracode Wave Protocol

How Phases 5–6 fan component and page porting out across many parallel subagents
without losing idiom consistency. The main thread is the orchestrator: it builds the
waves, writes the contract, dispatches agents, gates between waves, and reconciles at
the end. Subagents port; they do not decide conventions.

## Step 1 — Reference port (main thread, before any fan-out)

1. Port the most-used primitive (usually `Button`) yourself, exactly per
   `component-conversion.md` + the target's authoring doc. This is the **golden
   reference** — it resolves every judgment call (idiom, token mapping, state handling,
   story shape) once, concretely.
2. Distill `<work>/conventions.md` (~40 lines max) from that port:
   - Authoring idiom (e.g. adapted-UUI: plain typed elements, source prop names, no React Aria)
   - `cx`/`sortCx` usage pattern + variant map shape
   - Token mapping: 3–4 worked examples of inline-style → utility class via `tokens.index.json`
   - Prop typing pattern (unions from inventory defaults, `ComponentPropsWithoutRef` extension)
   - Icon approach for this target
   - Story file shape (meta, argTypes from inventory props, variants to show)
   - File/export conventions (paths, named exports, index barrel)
3. Verify the reference compiles (`bunx tsc --noEmit` in `packages/ui`) **before**
   fanning out — a broken reference replicates its breakage across every agent.

## Step 2 — Build dependency waves

From the `analysis.json` inventory (`recommended_library_components` + accepted
promotions + `screens`):

1. Derive the import graph: grep each source component file for references to other
   inventory names (JSX usage `<Name`, not just imports — claude.ai exports often share
   one file).
2. Topo-sort into waves:
   - **Wave 1** — leaf primitives (reference no other inventory component)
   - **Wave 2+** — components whose dependencies are all in earlier waves
   - **Composite wave** — Shell/Sidebar/TopBar-style layout composites
   - **Page wave** — every page story (per `--pages`), depends on everything
3. Cycles (rare; usually a shared-file artifact): break by porting the cycle members in
   one agent.
4. Print the wave plan (wave → component list) before dispatching — it's the user's
   last cheap chance to spot a wrong inventory.

## Step 3 — Dispatch (full fan-out per wave)

All members of a wave launch **simultaneously**, one `component-porter` agent each, in
a single multi-Agent message. No artificial batch cap — the wave boundary is the only
synchronization point. Each agent's prompt carries:

```
kind:            component | composite | page
name:            <ComponentName or page id>
source_path:     <file in _src — plus line range when components share a file>
out_path:        packages/ui/src/components/<name>/ (or apps/storybook/src/pages/ for pages)
conventions:     <work>/conventions.md
golden_ref:      packages/ui/src/components/button/ (the reference port)
token_index:     <work>/tokens.index.json (or packages/tokens/src/tokens.index.json)
conversion_doc:  <skill>/references/component-conversion.md
target_doc:      <skill>/references/targets/<library>.md
inventory_entry: <the component's analysis.json record: props, defaults, types>
ported_deps:     <paths of already-ported components this one imports>
fixtures:        <mock-data module path — pages only>
```

Pages additionally receive the full list of ported library exports so they import
rather than re-implement.

## Step 4 — Between-wave gate (main thread)

After each wave returns:

1. `bunx tsc --noEmit` in `packages/ui` (and the storybook app after the page wave).
2. Failures: fix trivial ones (missing import, typo) directly; re-dispatch a porter
   once with the error text for structural ones; take over in the main thread on a
   second failure.
3. Only then dispatch the next wave — wave N+1 imports wave N, so a broken wave
   poisons everything downstream.

Track progress with TaskCreate/TaskUpdate — one task per wave, not per component.

## Step 5 — Reconciliation sweep (start of Phase 8)

After the page wave, launch one `library-reconciler` agent over `packages/ui` +
`apps/storybook`. Parallel porting drifts in predictable ways; the sweep checklist:

- **Naming**: variant/size prop value casing consistent across components (`primary` vs `Primary`)
- **Token usage**: no stray inline `var(--x)` styles where a utility exists in `tokens.index.json`
- **cx pattern**: same composition helper everywhere; no one-off `clsx` imports
- **Type style**: prop unions vs enums consistent; same `ComponentPropsWithoutRef` extension pattern
- **Stories**: every component has one; same meta shape; sidebar grouping `Primitives/` · `Composites/` · `Pages/`
- **Exports**: every component reachable from the package barrel; no duplicate identifiers
- **Dead code**: stubs or TODOs a porter left behind

The reconciler fixes mechanical drift directly and **reports** (not fixes) judgment
calls — the main thread decides those, then runs the normal Phase 8 verification
(`tsc --noEmit`, `bun run build-storybook`).

## Failure economics

A porter that fails twice costs less than a wrong convention propagated silently:
porters must follow `conventions.md` even where they disagree, and surface
disagreements in their report instead of improvising. The orchestrator owns taste;
the agents own throughput.
