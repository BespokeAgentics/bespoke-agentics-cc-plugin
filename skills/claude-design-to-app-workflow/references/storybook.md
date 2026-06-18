# Storybook + Tailwind CSS v4 + Bun + Vite + React + TypeScript (monorepo package)

Verified mid-2026. Known-good, hand-authored (deterministic) config for a Storybook
host inside a Bun-workspace monorepo. Lead with commands + full file contents.

## Verified versions (pin these)

| Package | Version | Notes |
|---|---|---|
| `storybook` (core CLI) | `10.4.2` | Storybook 10 is current stable (v9 superseded mid-2026). |
| `@storybook/react-vite` | `10.4.2` | Framework package. Must match core. |
| `@storybook/addon-docs` | `10.4.2` | Separate package in v10 (was in removed `addon-essentials`). |
| `@storybook/addon-a11y` | `10.4.2` | Accessibility addon. |
| `@storybook/addon-themes` | `10.4.2` | Provides `withThemeByDataAttribute`. |
| `tailwindcss` | `4.3.0` | Tailwind v4. No `tailwind.config.js` needed. |
| `@tailwindcss/vite` | `4.3.0` | First-party Vite plugin (preferred over PostCSS). |
| `vite` | `7.x` (e.g. `^7.0.4`) | Storybook 10.4.2 dev-tests on Vite 7. Vite 8 (`8.0.16`) is also peer-accepted (`^5 \|\| ^6 \|\| ^7 \|\| ^8`) but prefer `^7` for stability. |
| `react` / `react-dom` | `19.2.x` | React 19 stable. |
| `typescript` | `^5.9.x` | |

IMPORTANT v10 change: `@storybook/addon-essentials` is REMOVED. `viewport`,
`controls`, `interactions`, and `actions` are now in Storybook core — do NOT install
or list them as addons. Only `docs`, `a11y`, `themes`, `vitest` etc. are separate.

## Install (Bun)

Do NOT run `bunx storybook@latest init` for a monorepo package — it pulls Storybook 10
but scaffolds opinionated files, may add removed addons, and guesses the builder. For a
workspace package, hand-author the four files below and install explicitly:

```bash
# from the Storybook host package dir (e.g. apps/storybook or packages/storybook)
bun add -d \
  storybook@10.4.2 \
  @storybook/react-vite@10.4.2 \
  @storybook/addon-docs@10.4.2 \
  @storybook/addon-a11y@10.4.2 \
  @storybook/addon-themes@10.4.2 \
  vite@^7.0.4 \
  @vitejs/plugin-react@^4.3.4 \
  tailwindcss@4.3.0 \
  @tailwindcss/vite@4.3.0 \
  typescript@^5.9.3

# React is a peer of your stories; if this package renders them, add it too:
bun add react@^19.2.0 react-dom@^19.2.0
```

If you prefer to let the CLI bootstrap and then prune: `bunx storybook@latest init
--builder vite --no-dev` then delete `addon-essentials`, add `@tailwindcss/vite`, and
replace `main.ts` / `preview.ts` with the versions below. Hand-authoring is more
deterministic — prefer it.

## File: `src/styles.css` (Tailwind v4 entry)

> **In this skill, do NOT hand-write the `@theme` tokens shown below.** They come from
> the `@<scope>/tokens` package generated in Phase 4. The real Storybook entry CSS is
> just imports of the tokens + the library's own stylesheet, e.g.:
> ```css
> @import "@<scope>/tokens/tokens.css";          /* runtime vars + [data-theme] switch */
> @import "@<scope>/tokens/tailwind-theme.css";  /* @import "tailwindcss" + @theme inline + @custom-variant dark */
> @source "../../../packages/ui/src";            /* ensure Tailwind scans library component classes */
> ```
> The block below is the *illustrative shape* of what `tailwind-theme.css` contains, so
> you understand the mechanism — not something to retype.

The v4 way: one `@import`, plus a `@theme` block for design tokens. No `@tailwind`
directives, no config file. Theme tokens become CSS variables AND generate utilities.

```css
@import "tailwindcss";

/* Make `dark:` variant respond to [data-theme="dark"] (Storybook theme toggle / app). */
@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));

@theme {
  /* Design tokens -> become CSS vars (--color-brand) AND utilities (bg-brand). */
  --color-brand: oklch(0.62 0.19 256);
  --color-bg: oklch(1 0 0);
  --color-fg: oklch(0.21 0.02 256);

  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;

  --radius-card: 0.75rem;
}

/* Per-theme overrides via [data-theme]. Dark is the default (set on <html>). */
:root,
[data-theme="light"] {
  --color-bg: oklch(1 0 0);
  --color-fg: oklch(0.21 0.02 256);
}

[data-theme="dark"] {
  --color-bg: oklch(0.21 0.02 256);
  --color-fg: oklch(0.98 0 0);
}

/* Apply the theme to the canvas so stories pick up bg/fg. */
html,
body {
  background-color: var(--color-bg);
  color: var(--color-fg);
}
```

## File: `.storybook/main.ts`

```ts
import type { StorybookConfig } from "@storybook/react-vite";
import tailwindcss from "@tailwindcss/vite";

const config: StorybookConfig = {
  // Pick up stories from THIS package AND any sibling workspace UI packages.
  // The second glob reaches into node_modules where workspace:* deps are symlinked.
  stories: [
    "../src/**/*.mdx",
    "../src/**/*.stories.@(js|jsx|mjs|ts|tsx)",
    "../../../packages/ui/src/**/*.stories.@(js|jsx|mjs|ts|tsx)",
  ],
  addons: [
    "@storybook/addon-docs", // separate package in v10
    "@storybook/addon-a11y",
    "@storybook/addon-themes",
    // NOTE: do NOT add addon-essentials/controls/actions/viewport/interactions —
    // they are built into Storybook 10 core.
  ],
  framework: {
    name: "@storybook/react-vite",
    options: {},
  },
  // Inject the Tailwind v4 Vite plugin into Storybook's own Vite pipeline.
  async viteFinal(viteConfig) {
    viteConfig.plugins = viteConfig.plugins ?? [];
    viteConfig.plugins.push(tailwindcss());
    return viteConfig;
  },
};

export default config;
```

## File: `.storybook/preview.ts`

```ts
import type { Preview } from "@storybook/react-vite";
import { withThemeByDataAttribute } from "@storybook/addon-themes";

// Import Tailwind once, globally, so every story gets the utilities + @theme vars.
import "../src/styles.css";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: { color: /(background|color)$/i, date: /Date$/i },
    },
    a11y: { test: "todo" }, // 'error' to fail CI, 'todo' to warn, 'off' to skip
  },
  decorators: [
    withThemeByDataAttribute({
      themes: { dark: "dark", light: "light" },
      defaultTheme: "dark", // dark default per source designs
      attributeName: "data-theme", // writes [data-theme] on <html>
    }),
  ],
};

export default preview;
```

## Theme toggle (dark default + light)

- `withThemeByDataAttribute` adds a paintbrush toolbar control. Each selection writes
  `data-theme="dark"` or `data-theme="light"` onto the preview `<html>` element.
- `attributeName: "data-theme"` + `defaultTheme: "dark"` => dark is the initial canvas.
- Tailwind v4 has no built-in `[data-theme]` awareness, so the `@custom-variant dark`
  line in `styles.css` rewires the `dark:` utility variant to match `[data-theme="dark"]`.
  Without it, `dark:` utilities would key off `prefers-color-scheme` and ignore the toggle.
- Per-theme token values live in the `[data-theme="..."]` blocks; component utilities like
  `bg-bg text-fg` then resolve correctly in both modes.

## File: `package.json` (workspace package)

```json
{
  "name": "@scope/storybook",
  "private": true,
  "type": "module",
  "scripts": {
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build"
  },
  "dependencies": {
    "@scope/ui": "workspace:*",
    "react": "^19.2.0",
    "react-dom": "^19.2.0"
  },
  "devDependencies": {
    "@storybook/addon-a11y": "10.4.2",
    "@storybook/addon-docs": "10.4.2",
    "@storybook/addon-themes": "10.4.2",
    "@storybook/react-vite": "10.4.2",
    "@tailwindcss/vite": "4.3.0",
    "@vitejs/plugin-react": "^4.3.4",
    "storybook": "10.4.2",
    "tailwindcss": "4.3.0",
    "typescript": "^5.9.3",
    "vite": "^7.0.4"
  }
}
```

`bun run storybook` to dev, `bun run build-storybook` to produce a static `storybook-static/`.

## File: `tsconfig.json` (minimal, for the Storybook package)

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
    "noEmit": true,
    "types": ["node"]
  },
  "include": [".storybook/**/*", "src/**/*"]
}
```

## Monorepo: consuming a sibling `@scope/ui` package

1. Root `package.json` declares workspaces, e.g.:
   ```json
   { "workspaces": ["apps/*", "packages/*"] }
   ```
2. The Storybook package depends on the UI package with `"@scope/ui": "workspace:*"`.
   Run `bun install` at the repo root so Bun symlinks `node_modules/@scope/ui` to the
   sibling source.
3. Two ways to surface the sibling's stories (pick one):
   - Add a stories glob pointing at the sibling source (shown in `main.ts` above) — simplest,
     reads `*.stories.tsx` straight from `packages/ui/src`.
   - Or import the UI package by its entry (`import { Button } from "@scope/ui"`) inside
     local stories under `src/`.
4. Importing `@scope/ui` source directly means Vite transpiles its TSX on the fly — no
   pre-build step needed in dev. Ensure the UI package's `package.json` exposes source via
   `exports`/`main` (or rely on the source glob).

## Gotchas (Tailwind v4 in Storybook)

- USE THE VITE PLUGIN, NOT POSTCSS. `@tailwindcss/vite` in `viteFinal` is the supported,
  fastest path. Do not also wire `@tailwindcss/postcss` / a `postcss.config.*` — running
  both double-processes CSS and breaks `@theme` var output.
- MUST import the CSS in `preview.ts` (`import "../src/styles.css"`). If you only add the
  Vite plugin but never import a file containing `@import "tailwindcss";`, no utilities are
  emitted and the canvas is unstyled.
- CONTENT/CLASS DETECTION: Tailwind v4 auto-detects class usage by scanning source files;
  there is no `content` array. In a monorepo it scans the Vite module graph, so classes used
  only inside a sibling `@scope/ui` package ARE picked up as long as those files are imported
  into the Storybook build (via the stories glob or a story import). Classes that never appear
  in any scanned/imported file get tree-shaken away. If a sibling's utility is missing, ensure
  its file is actually reached by a story import or add an explicit `@source` directive in
  `styles.css`, e.g. `@source "../../../packages/ui/src";`.
- `@theme` VS `:root`: only `@theme {}` generates utilities (`bg-brand`). Plain `:root { --x }`
  defines a var but no utility. For per-theme overrides of an existing token, redeclare the var
  inside `[data-theme="..."]` (as above) — keep the token's canonical definition in `@theme`.
- `dark:` VARIANT: without the `@custom-variant dark (&:where([data-theme="dark"] ...))` line,
  `dark:` keys off the OS `prefers-color-scheme`, not the Storybook toggle. Always rewire it.
- VITE VERSION: Storybook 10.4.2 peer-accepts Vite `^5 || ^6 || ^7 || ^8` and `@tailwindcss/vite`
  accepts `^5.2 || ^6 || ^7 || ^8`. Pin one Vite version at the workspace root to avoid two copies
  (duplicate Vite => "plugin applied twice" / HMR oddities). `^7.0.4` is the safe default.
- BUN + STORYBOOK: Storybook runs fine under Bun via its Node compat. Use `bun run storybook`
  (not `bun storybook`) so the package script — not a global — is invoked. If the CLI misbehaves,
  `bunx --bun storybook dev -p 6006` forces Bun's runtime.
```