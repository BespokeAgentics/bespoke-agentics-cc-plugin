# Tokens → Tailwind v4 (and theming)

`scripts/tokens_to_tailwind.py <tokens.css> --out-dir packages/tokens/src` writes two
files. This explains them, the theming model, and the cleanups you should review.

## What the script emits

**`tailwind-theme.css`** — `@import "tailwindcss";` + (if the source has themes) a
`@custom-variant dark (…)` rewire + an `@theme inline { … }` block mapping the design's
vars into Tailwind namespaces:

```css
@theme inline {
  /* color */
  --color-accent: var(--accent-default);
  --color-fg:     var(--text-primary);
  --color-surface: var(--surface-default);
  --color-border: var(--border-default);
  /* text */  --text-button: var(--fs-button);
  /* radius */ --radius-md: var(--radius-md);
  /* spacing */--spacing-4: var(--sp-4);
  /* shadow */ --shadow-card: var(--shadow-card);
}
```

**`tokens.index.json`** — structured token data plus `css_var_usage`, the map the
component converter uses:

```jsonc
"css_var_usage": {
  "accent-default": { "background": "bg-accent", "color": "text-accent",
                      "border-color": "border-accent", ... },
  "text-primary":   { "color": "text-fg", "background": "bg-fg", ... }
}
```

## Why `@theme inline` (don't change this)

`inline` makes generated utilities reference `var(--accent-default)` **at use-site**
rather than copying its value. The source sheet defines `--accent-default` differently
under `:root`/`[data-theme="dark"]` vs `[data-theme="light"]`, so a single `bg-accent`
class follows the theme toggle automatically. A non-inline `@theme` would freeze the
value and break light mode. Keep `inline`.

## The two-layer CSS, assembled

Your library's entry stylesheet (e.g. `packages/ui/src/styles/index.css`) imports, in
order:

```css
@import "@<scope>/tokens/tokens.css";          /* 1. runtime vars + [data-theme] switch (verbatim source) */
@import "@<scope>/tokens/tailwind-theme.css";  /* 2. tailwind + @theme inline mapping */
```

Then carry over anything from the source sheet that isn't a token: `@keyframes`
(`shimmer`, `pulse`, `fade-up`…), base element rules, the noise/grain overlay, and the
font `@import` (or self-host). The analyzer lists the font URLs under `tokens.fonts`.

## Theme toggle

**Resolving the default theme.** The source can disagree with itself — e.g. `tokens.css`
comments "Dark theme is default" while `app.jsx` boots `localStorage.theme || 'light'`.
Pick the design's *intended* default (the token sheet's stated default and what the
`screenshots/` show), set `preview.ts`'s `defaultTheme` to it, and note the discrepancy in
your hand-off summary. It's a one-line flip if the user wants the other.

The source uses `document.documentElement.setAttribute('data-theme', theme)` with a
default. Preserve that:

- Storybook: `withThemeByDataAttribute({ themes: { dark:'dark', light:'light' },
  defaultTheme: '<source default>', attributeName: 'data-theme' })` (see
  `storybook.md`).
- App/library demo: a small toggle that flips `data-theme` on `<html>`.

The emitted `@custom-variant dark (&:where([data-theme="dark"], …))` line means any
`dark:` utilities you write also follow `[data-theme]` rather than OS preference — keep
it so the two systems agree.

## Cleanups to review (the script is a strong draft, not final)

1. **Role-color names.** The script renames common roles to avoid awkward utilities:
   `text-primary → fg`, `text-secondary → fg-muted`, `surface-default → surface`,
   `border-default → border`, `accent-default → accent`. Skim `color_var_to_token` in
   `tokens.index.json`; rename anything that reads oddly for *this* design before you
   start porting (you'll be typing these classes a lot).
2. **Primitive scales vs semantic tokens.** Raw scales (`--blue-500`) become
   `--color-blue-500` (fine for escapes), but prefer the semantic roles (`bg-accent`)
   in components so theming works. Use raw scale utilities only where the source did.
3. **Spacing.** `--sp-4: 16px` → `--spacing-4`. Tailwind v4's numeric spacing already
   covers `p-4` etc.; the mapping just makes the design's exact steps available. If the
   source steps match Tailwind's 4px base (they usually do), you can often use stock
   `p-4`/`gap-2` and reserve the custom ones for off-scale values.
4. **`border` collision.** `--color-border` gives `border-border`; that's intentional
   (Tailwind's bare `border` sets width). `border border-border` = 1px in the token
   color. Confirm it reads acceptably or rename to `--color-line`.

## Untitled UI target

When `--library untitled-ui-react`, don't ship `tailwind-theme.css` as-is — fold the
mapping into Untitled UI's `styles/theme.css` 3-layer convention (primitive scales in
`@theme`, semantic tokens in `:root`, dark overrides) but **re-point its dark variant
to `[data-theme]`** instead of `.dark-mode`, since claude.ai exports use the attribute.
Details and the exact recipe are in `references/targets/untitled-ui-react.md`.

## Token JSON (Tokens Studio / DTCG)

If the export ships raw token JSON instead of (or alongside) a compiled CSS sheet, the
analyzer marks it `tokens` role. Flatten it to CSS custom properties first
(`--group-subgroup-name: value`, resolving `{alias.references}`), write that as the
`tokens.css` runtime layer, then run `tokens_to_tailwind.py` on it. Most claude.ai
exports already ship the compiled CSS (the JSON is the *source*), so the CSS path is
the common one.
