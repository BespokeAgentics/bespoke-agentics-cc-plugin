# Bun workspace layout

The monorepo the skill scaffolds. **Don't hand-write these files — run the bundled
scaffolder**, which substitutes `<scope>`/`<name>`, injects the per-`--library` dep
matrix, and writes a skeleton that already `tsc --noEmit`-clean:

```bash
python3 <skill>/scripts/scaffold_workspace.py \
  --out <name>-workspace --name <scope> \
  --analysis <work>/analysis.json --library <library>
cd <name>-workspace && bun install
```

The layout it produces (templates live in `assets/templates/` if you need to inspect or
tweak one):

```
<name>-workspace/
├── package.json            # private root; workspaces: ["packages/*","apps/*"]
├── bunfig.toml
├── tsconfig.base.json
├── .gitignore
├── packages/
│   ├── tokens/             # @<scope>/tokens — design tokens
│   │   ├── package.json
│   │   └── src/
│   │       ├── tokens.css            # verbatim source sheet (runtime vars + [data-theme])
│   │       ├── tailwind-theme.css    # @theme inline map (from tokens_to_tailwind.py)
│   │       └── tokens.index.json
│   └── ui/                 # @<scope>/ui — component library
│       ├── package.json
│       ├── tsconfig.json
│       └── src/
│           ├── index.ts              # re-exports every public component
│           ├── styles/index.css      # imports tokens + tailwind-theme + keyframes
│           ├── components/…          # one folder/file per component + *.stories.tsx
│           └── lib/cx.ts             # class-merge helper (target-dependent)
└── apps/
    └── storybook/          # @<scope>/storybook — Storybook host
        ├── package.json
        ├── tsconfig.json
        ├── vite.config.ts
        ├── .storybook/{main.ts,preview.ts}
        └── src/
            ├── fixtures/             # ported mock data
            └── pages/                # composed page demos as *.stories.tsx
```

## Decisions

- **Why a `tokens` package.** It justifies the workspace, keeps tokens reusable by other
  apps, and gives a clean import (`@<scope>/tokens/tokens.css`). If the user wants a
  single package, collapse it into `packages/ui/src/styles/` and drop the workspace dep.
- **Where stories live.** Per-component stories sit next to components in `packages/ui`.
  Page-demo stories live in `apps/storybook/src/pages` (they need the mock data and
  compose many components). Storybook's `main.ts` globs both.
- **Workspace deps** use the `workspace:*` protocol: `apps/storybook` depends on
  `@<scope>/ui` and `@<scope>/tokens`; `@<scope>/ui` depends on `@<scope>/tokens`.

## Root `package.json` (template: `assets/templates/root-package.json`)

```json
{
  "name": "<name>-workspace",
  "private": true,
  "type": "module",
  "workspaces": ["packages/*", "apps/*"],
  "scripts": {
    "storybook": "bun --filter @<scope>/storybook storybook",
    "build-storybook": "bun --filter @<scope>/storybook build-storybook",
    "typecheck": "bun --filter '*' typecheck"
  }
}
```

## `bunfig.toml` (template: `assets/templates/bunfig.toml`)

```toml
[install]
# Hoisted (flat) node_modules — fast, matches npm intuition.
# If two packages pin incompatible React majors, switch to:
# linker = "isolated"
```

## `tsconfig.base.json` (template: `assets/templates/tsconfig.base.json`)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "verbatimModuleSyntax": true,
    "noEmit": true
  }
}
```

(For `--framework svelte`/`lit`, adjust `jsx`/`lib` and add the framework's TS plugin —
see the relevant `targets/<framework>.md`.)

## Package manifests

- `@<scope>/tokens`: `package.json` with `"exports"` mapping `./tokens.css`,
  `./tailwind-theme.css`, `./index.json` to `src/…`. No build needed (CSS/JSON shipped
  as-is). Template: `assets/templates/tokens-package.json`.
- `@<scope>/ui`: depends on `@<scope>/tokens` (`workspace:*`), `lucide-react`, plus the
  target's runtime deps (e.g. `react-aria-components`, `tailwind-merge` for Untitled UI).
  `"exports"` points at `src/index.ts` (Storybook/Vite consume TS source directly — no
  build step required for the showcase; add `tsup`/`tsc` only if publishing). Template:
  `assets/templates/ui-package.json`.
- `@<scope>/storybook`: the Storybook devDeps + scripts. See `references/storybook.md`
  for the exact set (Storybook v10 + Tailwind v4 + Vite). Template:
  `assets/templates/storybook-package.json`.

## Order of operations

1. `scaffold_workspace.py … --name <scope> --library <library>` → writes the whole
   skeleton (root manifests, all three packages, Storybook config, `cx.ts`, svg shims).
2. `bun install` once.
3. (Optional) `bunx tsc --noEmit` on the empty skeleton — should be clean, confirming the
   config before you port anything.
4. Fill `packages/tokens` (Phase 4), then `packages/ui` (Phase 5–6), then page demos in
   `apps/storybook` (Phase 6–7).
5. `bunx tsc --noEmit` (per `references/typescript-gotchas.md`) and `bun run
   build-storybook` to verify (Phase 8).

The scaffolder derives `<scope>` from `--name` (sanitized). Derive a sensible scope from
the design name (`Foundry Scope` → `foundry`). It reads `source_uses_react_aria` from
`analysis.json` to decide the `packages/ui` dep matrix (adds `react-aria-components` only
for full Untitled UI).
