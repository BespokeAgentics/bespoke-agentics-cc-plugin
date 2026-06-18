# Untitled UI React — Port Target Reference

Reference for porting a design-system zip into **Untitled UI React** (the DEFAULT target).
Untitled UI React is a copy-paste, source-in-your-repo component library (like shadcn/ui, NOT an
npm runtime package). The CLI copies `.tsx` source files into the consuming project; you own and
edit them. Open-source base components are MIT-licensed; advanced components + page examples are PRO.

Official docs: https://www.untitledui.com/react/docs/introduction · Repo: https://github.com/untitleduico/react · npm CLI: https://www.npmjs.com/package/untitledui

Versions verified June 2026 (from official docs + repo). Version-pin below reflects what was seen.

---

## Two modes: full Untitled UI vs adapted (DEFAULT for claude.ai exports)

Untitled UI's components wrap **React Aria** and rename props (`isDisabled`, `isPending`,
`isSelected`). That's right when the *source* is already accessibility-structured. But
claude.ai design exports are **plain inline-styled elements** with simple props
(`variant`, `disabled`, `onClick`) — the analyzer reports this as
`source_uses_react_aria: false`. Forcing every primitive into React Aria then fights the
source and breaks faithful page composition for no real gain.

So choose by `source_uses_react_aria`:

- **`false` (the common case) → ADAPTED Untitled UI.** Keep Untitled UI's *token system*
  (the 3-layer `theme.css`) and its *authoring shape* (`styles = sortCx({common,sizes,colors})`
  + `cx`), but author components as plain typed elements (see `custom-react.md`) — **no
  React Aria wrappers, no `is*` prop renames**. Preserve the source prop names so ported
  pages read unchanged. This is what a faithful port wants and is the documented default.
- **`true` → FULL Untitled UI.** Wrap React Aria, use `isDisabled`/`isPending`, install
  `react-aria-components` (the scaffold adds it when this flag is true). Follow the full
  pattern below.

Either way you use the token bridge below and `sortCx`/`cx`. The rest of this file
documents the FULL idiom; apply the parts that fit your chosen mode.

---

## Stack & deps

- **React** v19.2
- **TypeScript** v5.9
- **Tailwind CSS** **v4.2** — this is Tailwind **v4** (CSS-first config via `@theme`, NOT a `tailwind.config.js`-driven v3 setup). Do not author v3-style config.
- **React Aria Components** v1.16 (Adobe) — unstyled accessible primitives; most interactive base components wrap `react-aria-components`.
- Frameworks supported by the CLI: **Next.js** and **Vite**.

**Peer/runtime deps installed for a manual setup** (CLI installs these automatically as needed):

```bash
npm install @untitledui/icons react-aria-components tailwindcss-react-aria-components tailwind-merge tailwindcss-animate
```

- `@untitledui/icons` — free line-icon set (`import { Home01 } from "@untitledui/icons"`). PRO icons: `@untitledui-pro/icons/{line,solid,duocolor,duotone}`.
- `react-aria-components` — accessibility primitives.
- `tailwindcss-react-aria-components` — Tailwind plugin exposing RAC data-state variants.
- `tailwind-merge` — class conflict resolution (used by the `cx` util).
- `tailwindcss-animate` — animation utilities.
- Tailwind plugins are loaded via `@plugin` in CSS (v4 style), not in a JS config.

---

## Scaffold commands

CLI is run via `npx`/`bunx` (no global install). Use `untitledui@latest`.

```bash
# Initialize a NEW project (interactive: asks project name + brand color)
npx untitledui@latest init

# Initialize with framework explicitly
npx untitledui@latest init my-app --nextjs
npx untitledui@latest init my-app --vite

# Add components to an EXISTING project
npx untitledui@latest add button
npx untitledui@latest add button toggle avatar
npx untitledui@latest add --all --type marketing      # bulk add by category

# Control install location / behavior
npx untitledui@latest add button --path src/components/ui
npx untitledui@latest add button --dir ./my-project
npx untitledui@latest add button --overwrite           # also the UPDATE mechanism

# Page examples (many require PRO)
npx untitledui@latest example dashboard-01/05 --example-path src/app/dashboard

# PRO auth
npx untitledui@latest login
```

**What `init` generates:** a full Next.js (or Vite) project with config + the core style files
(`globals.css`, `theme.css`, `typography.css`), the `cx`/helper utils, hooks, and a starter set of
components pre-installed, themed to the chosen brand color.

**What `add` generates:** copies only the requested component source file(s) (plus their internal
deps) into your tree and auto-installs any missing npm deps. It does NOT touch existing files unless
`--overwrite`. The core setup files (`globals.css`, `theme.css`) are required for components to work —
`init` creates them; for a piecemeal manual setup you must add them yourself.

Component categories selectable by the CLI: `base`, `application`, `marketing`, `shared-assets`, `foundations`.

---

## Directory layout

Top level of the source library / a scaffolded project:

```
components/
  base/            # primitives: buttons, inputs, avatar, badges, checkbox, select, toggle, ...
  application/     # composed app UI: tables, modals, sidebars, navigation, date pickers, ...
  foundations/     # icons, logos, dot-grids, rating stars, non-interactive design atoms
  shared-assets/   # illustrations, backgrounds, misc reusable assets
  internal/        # internal-only helpers (not a public category)
hooks/             # use-breakpoint.ts, use-clipboard.ts, ...
utils/             # cx.ts, is-react-component.ts, ...
styles/
  globals.css      # @import "tailwindcss"; @import "./theme.css"; + @plugin lines + base resets
  theme.css        # @theme primitives + :root (light) & .dark-mode (dark) semantic tokens
  typography.css   # text styles
```

**`base/` subfolders (verified):** `avatar`, `badges`, `button-group`, `buttons`, `checkbox`,
`dropdown`, `file-upload-trigger`, `form`, `input`, `progress-indicators`, `radio-buttons`,
`select`, `slider`, `tags`, `textarea`, `toggle`, `tooltip`.

**Naming convention:** kebab-case folders AND files. Each component folder holds one or more
`.tsx` files. Example canonical path:

```
components/base/buttons/button.tsx
components/foundations/...        # icon components etc.
```

Note: filenames are lower-kebab (`button.tsx`), even though the exported symbol is PascalCase (`Button`).
Import alias is `@/` (e.g. `import { cx } from "@/utils/cx"`).

---

## Component authoring pattern (with example)

Conventions every component follows:

1. **`"use client";`** at top (RSC-safe).
2. Wrap a **React Aria Components** primitive (`AriaButton`, `AriaLink`, etc.) rather than a raw element when interaction/accessibility matters.
3. **Style object** declared with `sortCx({...})` — a `common` block plus `sizes` and `colors` maps. `sortCx` is an identity function that exists only so Tailwind IntelliSense will sort classes inside style objects.
4. Variant props are typed as **`keyof typeof styles.sizes` / `keyof typeof styles.colors`** so prop options stay in sync with the style map. Sizes are `xs|sm|md|lg|xl`; colors are semantic (`primary`, `secondary`, `tertiary`, `link-color`, `link-gray`, `*-destructive`).
5. Boolean props use the React Aria convention: **`isDisabled`, `isLoading`, `isPending`** (not `disabled`/`loading`).
6. Final className composed with **`cx(...)`** = an `extendTailwindMerge` instance (resolves Tailwind conflicts; extended to know the custom `display-*` text sizes).
7. Icons are passed as **components** via `iconLeading`/`iconTrailing` (rendered with `data-icon` attr) and detected with the `isReactComponent` helper; `data-*` attributes drive variant styling (e.g. `data-icon-only`, `data-loading`).

The two `cx` utilities (`utils/cx.ts`):

```typescript
import { extendTailwindMerge } from "tailwind-merge";

const twMerge = extendTailwindMerge({
    extend: { theme: { text: ["display-xs","display-sm","display-md","display-lg","display-xl","display-2xl"] } },
});

export const cx = twMerge;                       // merge classes (conflict-aware)
export function sortCx<T extends Record<string, ...>>(classes: T): T { return classes; } // identity; enables IntelliSense sorting
```

Abridged real Button (`components/base/buttons/button.tsx`):

```tsx
"use client";

import type { FC, ReactElement, ReactNode } from "react";
import { isValidElement } from "react";
import type { ButtonProps as AriaButtonProps, LinkProps as AriaLinkProps } from "react-aria-components";
import { Button as AriaButton, Link as AriaLink } from "react-aria-components";
import { cx, sortCx } from "@/utils/cx";
import { isReactComponent } from "@/utils/is-react-component";

export const styles = sortCx({
    common: {
        root: "group relative inline-flex h-max cursor-pointer items-center justify-center outline-brand transition focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        icon: "pointer-events-none size-5 shrink-0 transition-inherit-all",
    },
    sizes: {
        xs: { root: "gap-1 rounded-lg px-2.5 py-1.5 text-sm font-semibold ...", linkRoot: "gap-1 *:data-text:underline-offset-3" },
        sm: { root: "gap-1 rounded-lg px-3 py-2 text-sm font-semibold ...",   linkRoot: "gap-1 *:data-text:underline-offset-3" },
        md: { root: "gap-1 rounded-lg px-3.5 py-2.5 text-sm font-semibold ...", linkRoot: "gap-1 *:data-text:underline-offset-4" },
        lg: { root: "gap-1.5 rounded-lg px-4 py-2.5 text-md font-semibold ...", linkRoot: "gap-1.5 *:data-text:underline-offset-4" },
        xl: { root: "gap-1.5 rounded-lg px-4.5 py-3 text-md font-semibold ...", linkRoot: "gap-1.5 *:data-text:underline-offset-4" },
    },
    colors: {
        primary:   { root: "bg-brand-solid text-white shadow-xs-skeuomorphic ring-1 ring-transparent ring-inset hover:bg-brand-solid_hover ..." },
        secondary: { root: "bg-primary text-secondary shadow-xs-skeuomorphic ring-1 ring-primary ring-inset hover:bg-primary_hover ..." },
        tertiary:  { root: "text-tertiary hover:bg-primary_hover hover:text-tertiary_hover ..." },
        "link-color":           { root: "justify-normal rounded p-0! text-brand-secondary hover:text-brand-secondary_hover ..." },
        "link-gray":            { root: "justify-normal rounded p-0! text-tertiary hover:text-tertiary_hover ..." },
        "primary-destructive":  { root: "bg-error-solid text-white ... outline-error hover:bg-error-solid_hover ..." },
        "secondary-destructive":{ root: "bg-primary text-error-primary ... ring-error_subtle outline-error ..." },
        "tertiary-destructive": { root: "text-error-primary outline-error hover:bg-error-primary ..." },
        "link-destructive":     { root: "justify-normal rounded p-0! text-error-primary outline-error ..." },
    },
});

export interface CommonProps {
    isDisabled?: boolean;
    isLoading?: boolean;
    size?: keyof typeof styles.sizes;     // "xs" | "sm" | "md" | "lg" | "xl"
    color?: keyof typeof styles.colors;   // "primary" | "secondary" | ... | "link-destructive"
    iconLeading?: FC<{ className?: string }> | ReactNode;
    iconTrailing?: FC<{ className?: string }> | ReactNode;
    noTextPadding?: boolean;
    showTextWhileLoading?: boolean;
    children?: ReactNode;
    className?: string;
}

export interface ButtonProps extends CommonProps, Omit<AriaButtonProps, "children" | "className"> {}
interface LinkProps extends CommonProps, Omit<AriaLinkProps, "children" | "className"> { href: NonNullable<AriaLinkProps["href"]>; }
export type Props = ButtonProps | LinkProps;

export const Button = ({ size = "sm", color = "primary", children, className, iconLeading: IconLeading, iconTrailing: IconTrailing,
                         isDisabled: disabled, isLoading: loading, showTextWhileLoading, noTextPadding, ...props }: Props) => {
    const isLinkType = ["link-gray", "link-color", "link-destructive"].includes(color);
    const commonProps = {
        ...props,
        isDisabled: disabled,
        className: cx(
            styles.common.root,
            styles.sizes[size].root,
            styles.colors[color].root,
            isLinkType && styles.sizes[size].linkRoot,
            className,
        ),
        children: /* icon(s) + <span data-text> ... */ null,
    };
    if ("href" in commonProps) return <AriaLink {...commonProps} href={disabled ? undefined : (props as LinkProps).href} />;
    return <AriaButton {...commonProps} type={(commonProps as any).type || "button"} isPending={loading} />;
};
```

Key takeaways for code generation:
- New components should mirror this `styles = sortCx({ common, sizes, colors })` shape and derive prop unions from the style map.
- Compose final classes with `cx(...)`, never string concatenation.
- Reference **semantic tokens** in class names (`bg-brand-solid`, `text-secondary`, `border-primary`), NOT raw palette stops, so dark mode and re-theming work automatically.

---

## Injecting custom tokens

Theming is a **three-layer CSS-variable system** in `styles/theme.css` (Tailwind v4 `@theme` + token layers). Components only reference SEMANTIC tokens; you re-skin a brand by editing primitives + semantic mappings, never the components.

**Layer 1 — primitive palette** inside `@theme` (raw color scales 50→950). To inject a brand's blue scale, replace the `--color-brand-*` stops (and any custom palettes) here:

```css
@theme {
    /* primitive brand scale — REPLACE these with the brand's blue scale */
    --color-brand-50:  rgb(239 246 255);
    --color-brand-500: rgb(59 130 246);
    --color-brand-600: rgb(37 99 235);   /* solid default */
    --color-brand-950: rgb(23 37 84);
    /* gray / error / warning / success scales live here too */
}
```

> Defining `--color-brand-500` inside `@theme` also makes Tailwind utility classes like `bg-brand-500` / `text-brand-600` available automatically (v4 behavior).

**Layer 2 — light semantic tokens** in `:root` (often under `@layer base`). Map primitives to meaning:

```css
:root {
    --color-text-primary: var(--color-neutral-900);
    --color-bg-primary: var(--color-white);
    --color-bg-brand-solid: var(--color-brand-600);   /* what primary buttons use */
    --color-fg-brand-primary: var(--color-brand-600);
    --color-border-primary: var(--color-neutral-300);
    --color-focus-ring: var(--color-brand-500);
}
```

**Layer 3 — dark overrides** in `.dark-mode`, re-binding the SAME semantic token names:

```css
.dark-mode {
    --color-text-primary: var(--color-neutral-50);
    --color-bg-primary: var(--color-neutral-950);
    --color-bg-brand-solid: var(--color-brand-600);
    --color-border-primary: var(--color-neutral-700);
}
```

**Dark/light switching:** Untitled UI uses a **`.dark-mode` (and `.light-mode`) CLASS**, applied to
`<html>`/`<body>` or any subtree — NOT a `[data-theme]` attribute and NOT Tailwind's default `.dark`
class. The custom variant is declared in `globals.css`:

```css
@custom-variant dark (&:where(.dark-mode, .dark-mode *));
```

> If the design-system zip specifies `[data-theme="dark"]` instead, either (a) re-point the
> `@custom-variant dark` selector to `[data-theme="dark"]` and define the dark semantic block under
> `[data-theme="dark"] { ... }`, or (b) toggle the `.dark-mode` class and keep Untitled UI's default.
> Prefer matching Untitled UI's class convention unless the brand mandates the attribute.

**Recommended injection recipe for a brand token set:**
1. Drop the brand's primitive scales (blue/brand, gray, semantic error/warning/success) into `@theme` in `theme.css`, keyed as `--color-brand-*`, `--color-gray-*` (or `--color-neutral-*`), etc.
2. Override the `:root` semantic tokens (`--color-bg-brand-solid`, `--color-fg-brand-primary`, `--color-text-*`, `--color-border-*`, `--color-focus-ring`) to point at the new primitives.
3. Mirror the overrides in `.dark-mode`.
4. Adjust `--font-body`/`--font-display`, `--radius-*`, and `--text-*` in `@theme` to match the brand typography/shape.
5. Leave component `.tsx` files untouched — they read semantic tokens, so the re-skin propagates.

There are also per-component variables (e.g. `--color-button-primary-icon`, `--color-focus-ring`, `--color-toggle-border`) defined in the token layers for fine-grained control.

### Bridge: a claude.ai export's role tokens → Untitled UI semantic names

The export's `tokens.css` already defines semantic roles under `:root` / `[data-theme]`
(`--accent-default`, `--text-primary`, `--surface-default`, …). Don't discard them — map
Untitled UI's semantic tokens onto them so the export's own theme drives Untitled UI
components. In `theme.css`, after dropping the primitive scale into `@theme`:

| Untitled UI semantic token | ← point at export's var |
|---|---|
| `--color-bg-brand-solid` | `var(--accent-default)` |
| `--color-fg-brand-primary` | `var(--accent-default)` |
| `--color-text-primary` | `var(--text-primary)` |
| `--color-text-secondary` | `var(--text-secondary)` |
| `--color-bg-primary` | `var(--surface-default)` |
| `--color-bg-secondary` | `var(--surface-raised)` |
| `--color-border-primary` | `var(--border-default)` |
| `--color-focus-ring` | `var(--accent-default)` |
| `--color-fg-error-primary` / `--color-bg-error-solid` | `var(--status-error-fg)` / deep red |

This keeps the export's `tokens.css` as the single runtime source of truth (and its
`[data-theme]` switch keeps working — re-point `@custom-variant dark` to `[data-theme]`
per the note above). Brand-bespoke components with no Untitled UI equivalent
(`ConfidencePip`, `FindingTypePill`, `StatusDot`…) are authored fresh in the
`sortCx`/`cx` idiom referencing these same semantic tokens. `tokens.index.json` from
`tokens_to_tailwind.py` is still a useful cross-reference for which export var backs
each role.

---

## Gotchas

- **Tailwind v4 only.** No `tailwind.config.js` content array; config is CSS-first via `@theme` + `@plugin` in `globals.css`. Generating v3 config is wrong.
- **Copy-paste model, not a package.** There is no `import { Button } from "untitledui"` runtime import. Components are source files in the repo (`@/components/base/...`). The `untitledui` npm package is just the CLI.
- **Dark mode = `.dark-mode` class**, not `.dark` and not `[data-theme]`. The `dark:` variant is remapped via `@custom-variant`. Don't assume Tailwind's stock dark variant.
- **React Aria boolean props:** use `isDisabled`/`isLoading`/`isPending`/`isSelected`, NOT `disabled`/`checked`. Many components are RAC wrappers and expect RAC prop names.
- **`sortCx` is a no-op** — purely for IntelliSense class sorting. `cx` is the real `tailwind-merge` instance and is extended to know the custom `display-*` text utilities.
- **Filenames are kebab-case, exports are PascalCase** (`button.tsx` exports `Button`). Match this when generating files.
- **Semantic vs primitive tokens:** components must reference semantic tokens (`bg-brand-solid`, `text-secondary`). Hard-coding `bg-brand-600` defeats dark mode / re-theming.
- **Core CSS files are mandatory.** `globals.css` + `theme.css` (+ `typography.css`) must exist or components render unstyled. `init` creates them; manual/piecemeal installs must add them first.
- **PRO gating.** `add --all`, many `application`/`marketing` components, and most `example` pages need `npx untitledui@latest login` (PRO license). Base components are free/MIT.
- **`@/` import alias** is assumed (`@/utils/cx`, `@/components/...`). Ensure `tsconfig.json` paths map `@/*` to project root/`src`.
- **Plugins via `@plugin`:** `tailwindcss-animate` and `tailwindcss-react-aria-components` are loaded in CSS; the RAC plugin is what enables data-state variants used throughout component class strings.
