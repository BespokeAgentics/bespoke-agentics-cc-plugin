---
name: design-zip-to-library
description: >-
  Turn a Claude design export (a claude.ai prototype/artifact .zip — tokens.css +
  React/JSX primitives + composed pages) into a real component library inside a Bun
  workspace monorepo, with Storybook showcasing every component AND the composed page
  demos. Use this whenever someone hands you a design-system zip, a "Claude design
  file", a prototype export, an "Untitled UI"/component-library request built from a
  design, or says things like "bootstrap a UI package from this design zip", "extract
  these components into a library", "stand up Storybook for this prototype", "scaffold
  a monorepo from this design", or "convert this claude.ai design into a real React/
  Svelte/Lit component library". Triggers even when the user only attaches a .zip and
  says "build the component library" without naming the steps. Defaults to Untitled UI
  React + TypeScript + Tailwind v4, configurable by flags. Runs in ultracode mode:
  component and page porting fans out across parallel subagent waves.
---

**Invocation.** The user typically points you at a design `.zip` and optionally passes
flags, e.g. `/design-zip-to-library "Foundry Scope - Prototype.zip" --framework svelte`.
Parse the zip path and any `--flag value` tokens from their message (see Configuration
below). If no zip is given, ask for it; if no flags, use the defaults.

You convert a **Claude design export** into a **production-shaped component library + Storybook** living in a **Bun workspace monorepo**. The input is the kind of `.zip` claude.ai produces for a prototype/artifact: a `tokens.css` (or token JSON), a file of React/JSX primitives, layout/shell composites, several composed pages, mock data, and assets. The output is a real library a team can build on — every primitive extracted and typed, themed exactly like the source, and a Storybook that shows both the components in isolation and the original pages rebuilt from them.

The job is **fidelity + structure**: the generated UI should look like the prototype, and the repo should be something an engineer is happy to inherit. Don't invent a new look; recover the one that's already there.

## When to use

Use this for any "design zip → library" request. The user may hand you only a `.zip` and a goal ("make this a component library", "stand up Storybook", "bootstrap the UI package"). They may not list the steps — infer them. Common phrasings: *"here's the Claude design export, build the library"*, *"turn this prototype into an Untitled UI component library with Storybook"*, *"scaffold a Bun monorepo from this design system zip"*, *"extract all the components and show the pages in Storybook"*.

This skill is **dynamic** — it inspects whatever zip it's handed (component count, themes, pages all vary) and generates from that. It is not specialized to any one design.

## Configuration (flags)

Read these from `args` (or ask if ambiguous). Sensible defaults mean you can run with none.

| Flag | Default | Options | Effect |
|------|---------|---------|--------|
| `--library` | `untitled-ui-react` | `untitled-ui-react`, `shadcn`, `custom` | Authoring conventions for the library. See `references/targets/`. |
| `--framework` | `react` | `react`, `svelte`, `lit`, `web-components`, `custom` | Component language. |
| `--styling` | `tailwind` | `tailwind`, `css-vars`, `css-modules` | How tokens reach components. |
| `--pages` | `all` | `all`, `none`, comma-list | Which composed pages to rebuild as stories. |
| `--name` | derived | any | Package scope, e.g. `@foundry`. |
| `--out` | `./<name>-workspace` | any path | Where the monorepo is written. |

`--library` and `--framework` interact: `untitled-ui-react` and `shadcn` imply `react`. If the user picks `--framework svelte|lit|web-components`, treat `--library` as `custom` for that framework and follow `references/targets/<framework>.md`. When a requested combination has no dedicated target file, fall back to `custom` and tell the user you're using the generic authoring conventions for their framework.

The default path — **Untitled UI React + React/TS + Tailwind v4 + all pages** — is the best-trodden one; lean on it unless flags say otherwise.

## The pipeline

Work through these phases in order. Each builds on the last. The two bundled scripts remove the rote inventory/token work so you can spend effort on faithful component porting.

**Ultracode orchestration.** Phases 0–4 are main-thread (global decisions: tokens, scaffold, conventions). Phases 5–6 delegate the per-file work — every component and every page — to parallel `component-porter` subagents dispatched in dependency waves, full fan-out within each wave. Phase 8 opens with a `library-reconciler` sweep that erases the idiom drift parallelism causes. The main thread never ports in bulk; it writes the contract, gates the waves, and judges the results. Protocol details: `references/parallel-porting.md`.

### Phase 0 — Preflight

1. Confirm Bun: `bun --version` (need ≥ 1.1; if missing, print `curl -fsSL https://bun.sh/install | bash` and stop).
2. Resolve the zip path from `args`. If none was given, ask for it. Print it so a wrong file is obvious.
3. Pick a working directory for the monorepo (`--out`, else `./<name>-workspace`). Don't write into the zip's own folder.

### Phase 1 — Analyze the export (deep, not shallow)

Run the bundled analyzer — it extracts, classifies, and inventories so you don't have to:

```bash
python3 <skill>/scripts/analyze_zip.py "<zip>" --out <work>/analysis.json --extract-to <work>/_src
```

It prints a summary and writes `analysis.json` with: `source_framework`, `files_by_role` (tokens / primitives / composite / page / data / entry / asset / screenshot / html), the **component inventory** (name, destructured props + defaults + inferred types, and whether it's `exported`), the **token scopes** (every CSS var grouped by `:root` / `[data-theme="…"]`), detected themes, and font `@import`s.

The analyzer already separates the public library from the screens for you — read these manifest fields and act on them rather than re-deriving:
- **`recommended_library_components`** — the public, non-screen components + layout composites. This is your library (each component carries `kind`/`public`/`window_member`).
- **`promotion_candidates`** — page-local components that look reusable (form/metric controls). Promote the ones that fit; leave the rest in pages.
- **`screens`** — rebuild as page stories in Phase 6, not library components.
- **`source_uses_react_aria`** — gates the authoring idiom in Phase 5.

Then **read the actual source** the manifest points to — at minimum the token sheet, the primitives file(s), the shell/composite files, and 1–2 representative pages — to learn *how* it's built (icon system, inline-style idioms, state patterns, how pages compose primitives) and to sanity-check the recommended list. See `references/analysis.md` for the manifest fields in full.

### Phase 2 — Plan & confirm

Before scaffolding (it writes many files), show the user a tight plan: target stack (from flags), the resolved package scope/name, the **library component list** (`recommended_library_components` + the promotions you'd accept), the **pages** you'll rebuild (the `screens`), the theme model (e.g. "dark default + light via `[data-theme]`"), and the monorepo layout. This is *confirm the list*, not *re-derive it*. Then proceed; adjust to corrections.

### Phase 3 — Scaffold the Bun workspace

Run the bundled scaffolder — it writes the entire skeleton (root manifests, all three packages, Storybook config, `cx.ts`, svg shims) with the correct per-`--library` dep matrix, and the empty tree is already `tsc`-clean:

```bash
python3 <skill>/scripts/scaffold_workspace.py \
  --out <name>-workspace --name <scope> \
  --analysis <work>/analysis.json --library <library>
cd <name>-workspace && bun install
```

The layout it produces (see `references/workspace.md` for details):

```
<name>-workspace/
├── package.json          # private root, workspaces: ["packages/*","apps/*"]
├── bunfig.toml
├── tsconfig.base.json
├── packages/
│   ├── ui/               # the component library  (@<scope>/ui)
│   └── tokens/           # design tokens: source sheet + tailwind-theme.css  (@<scope>/tokens)
└── apps/
    └── storybook/        # Storybook host (depends on @<scope>/ui via workspace:*)
```

`packages/tokens` justifies the workspace and keeps the design tokens reusable. If the user prefers a single package, collapse tokens into `packages/ui/src/styles/` and say so. The scaffolder also pre-writes `.storybook/main.ts` + `preview.ts`, `src/lib/cx.ts`, the svg/css ambient shim, and per-package `tsconfig.json` — so Phases 5–7 are mostly *filling* a working skeleton, not configuring one.

### Phase 4 — Tokens & theming

1. Copy the source token sheet **verbatim** into `packages/tokens/src/tokens.css` — it is the runtime variable + `[data-theme]` switch layer; preserving it keeps theming exact.
2. Generate the Tailwind v4 layer:

```bash
python3 <skill>/scripts/tokens_to_tailwind.py <work>/_src/<tokens.css> --out-dir packages/tokens/src
```

This writes `tailwind-theme.css` (an `@theme inline` map so utilities like `bg-accent` resolve to `var(--accent-default)` at use-site — **live theme switching survives**) and `tokens.index.json` (the `css_var_usage` map: which utility class replaces each `var(--x)` inline-style color). Carry over the font `@import`(s). Review role-color names per `references/tokens-and-tailwind.md`. For `--library untitled-ui-react`, fit these into Untitled UI's `styles/theme.css` 3-layer convention (re-pointed to `[data-theme]`, since these exports use the attribute, not a class) — see `references/targets/untitled-ui-react.md`. For `--styling css-vars`, skip the Tailwind layer and keep inline styles + `tokens.css`.

### Phase 5 — Port the components (parallel waves)

Follow `references/parallel-porting.md` — the full ultracode protocol. In brief:

1. **Reference port (main thread).** Port the most-used primitive (often `Button`)
   yourself per `references/component-conversion.md` (inline-style objects → utility
   classes using `tokens.index.json`, prop defaults → typed prop unions, hover/press
   state → variant/pseudo classes, `data-lucide` icons → the target's icon approach)
   **and** the chosen `references/targets/<library>.md`. **Idiom by
   `source_uses_react_aria`:** when it's `false` (the common claude.ai case) and
   `--library untitled-ui-react`, author in the *adapted* UUI idiom — Untitled UI's
   token system + `sortCx`/`cx`, but plain typed elements and source prop names
   (`variant`/`disabled`/`onClick`), **no React Aria wrappers or `is*` renames**. Only
   go full React Aria when the source already uses it. Verify it compiles, then distill
   the judgment calls into `<work>/conventions.md` — the contract every porter receives.
2. **Build dependency waves.** Topo-sort the inventory by intra-inventory usage: leaf
   primitives → compound components → layout composites. Print the wave plan.
3. **Fan out.** Dispatch one `component-porter` agent per component, the whole wave
   simultaneously. Each porter gets the contract, the golden reference, its
   `inventory_entry` (props drive the co-located `*.stories.tsx`), `tokens.index.json`,
   and the paths of already-ported dependencies. Keep names from the source so pages
   still read naturally.
4. **Gate between waves.** `bunx tsc --noEmit` after each wave; fix or re-dispatch
   failures before the next wave dispatches (wave N+1 imports wave N).

Copy `assets/` (logos, svgs) into the package on the main thread — it's one `cp`, not
agent work.

### Phase 6 — Composites & page demos (parallel)

1. The layout composites (`Shell`/`Sidebar`/`TopBar`-style) are the last component
   wave of Phase 5 — they must exist before pages.
2. Port the mock data into the Storybook app (or a `fixtures` module) — main thread.
3. **Page wave:** dispatch one `component-porter` agent per page (per `--pages`,
   default every page in the manifest), all simultaneously. Each rebuilds its page as a
   **full-viewport Storybook story** composed strictly from the ported library exports
   + fixtures — this is the proof the library actually reconstructs the prototype.
   Faithful composition > pixel-chasing; match layout, spacing, and content. Gate with
   `tsc --noEmit` over the storybook app when the wave returns.

### Phase 7 — Storybook

The scaffolder already wrote `.storybook/main.ts` + `preview.ts` from verified templates (Storybook **v10**, Tailwind **v4**, `@storybook/react-vite`, addons `docs`/`a11y`/`themes`, `withThemeByDataAttribute` dark-default `[data-theme]` toggle). Your job here is mostly: set `preview.ts`'s `defaultTheme` to the source's default, ensure the stories globs cover your files, and group the sidebar `Primitives/` · `Composites/` · `Pages/`. See `references/storybook.md` only if you need to change the config.

### Phase 8 — Reconcile, verify & hand off

- **Reconciliation sweep first:** launch one `library-reconciler` agent over
  `packages/ui` + `apps/storybook` with the conventions contract, golden reference,
  and the porters' deviation/disagreement notes. It fixes mechanical idiom drift
  (naming casing, stray inline `var(--x)` styles, one-off class helpers, story meta
  shape, barrel exports) and reports judgment calls — decide those yourself.
- Type/build check: per-package `bunx tsc --noEmit` (consult `references/typescript-gotchas.md` — the recurring strict-mode fixes cluster by pattern) and `bun run build-storybook` (report real output — if it fails, fix or surface it; don't claim success it didn't earn).
- Tell the user how to run it: `bun --filter @<scope>/storybook storybook` (or `cd apps/storybook && bun storybook`).
- Summarize: components generated, pages rebuilt, where things live, and any judgment calls (promoted page-locals, role-name choices, components that needed manual attention).
- Offer the next step: `/bespoke-agentics:funcspec-evaluate <workspace>` — the `funcspec` skill evaluates the rebuilt pages page-by-page, infers the functionality the UI implies, validates it with the user, and produces a full implementation plan (spec, plan, backlog, gap register).

## Reference map

Read these as the phase calls for them — don't preload everything.

| Need | Read |
|------|------|
| Interpret `analysis.json`; library-vs-page judgment | `references/analysis.md` |
| Token sheet → Tailwind v4 `@theme inline`; role naming; theme toggle | `references/tokens-and-tailwind.md` |
| Port a component (inline styles → utilities, typed props, icons, state) | `references/component-conversion.md` |
| Wave construction, porter prompt contract, between-wave gates, reconciliation | `references/parallel-porting.md` |
| Bun workspace layout + the `scaffold_workspace.py` skeleton | `references/workspace.md` |
| Storybook v10 + Tailwind v4 + Bun exact config | `references/storybook.md` |
| Recurring `tsc --noEmit` strict-mode fixes when porting | `references/typescript-gotchas.md` |
| Authoring conventions for the chosen target | `references/targets/untitled-ui-react.md` · `shadcn.md` · `custom-react.md` · `svelte.md` · `lit.md` |

## Principles

- **Recover, don't redesign.** The source already encodes taste — tokens, spacing, type scale. Your job is to lift it faithfully into a maintainable structure, not improve it.
- **Scripts do the rote part.** Inventory and token mapping are deterministic; let the bundled scripts do them so your effort goes into the components that need judgment.
- **The orchestrator owns taste; the agents own throughput.** Conventions are decided once (reference port + contract), enforced everywhere (porters follow, reconciler sweeps). Parallelism never gets to vote on idiom.
- **The pages are the acceptance test.** A library that can rebuild the original screens is a real library. If a page can't be reconstructed, a primitive is missing or wrong — fix it there.
- **Report honestly.** If the build doesn't compile, say so with the error. Half-ported is in-progress, not done.
