# Target: Svelte 5 (runes)

Use when `--framework svelte`. Components are rewritten as Svelte 5 runes components.
The source's React logic (`useState` for hover, prop destructuring) maps cleanly to
runes. Tailwind v4 + the same token layer apply unchanged.

> When generating Svelte, use the Svelte MCP tools: `list-sections` →
> `get-documentation` for anything you're unsure about, and run `svelte-autofixer` on
> each component until it returns no issues before moving on. This matches the project's
> global Svelte workflow and catches runes mistakes early.

## Stack

- Svelte 5 + TypeScript + Vite, Tailwind v4 (`@tailwindcss/vite`), `lucide-svelte` for icons.
- Storybook: `@storybook/svelte-vite` (swap the framework package in `main.ts`; the
  Tailwind `viteFinal` wiring and `[data-theme]` toggle from `references/storybook.md`
  are identical). Stories use `@storybook/addon-svelte-csf` (`*.stories.svelte`) or CSF.

## Component pattern

```svelte
<!-- Button.svelte -->
<script lang="ts">
  import type { Snippet } from 'svelte';
  type Props = {
    variant?: 'primary' | 'secondary' | 'ghost' | 'accent';
    size?: 'sm' | 'md' | 'lg';
    icon?: string;
    disabled?: boolean;
    onclick?: () => void;
    children?: Snippet;
  };
  let { variant = 'primary', size = 'md', icon, disabled, onclick, children }: Props = $props();

  const VARIANTS = {
    primary:   'bg-accent text-white hover:bg-accent-strong',
    secondary: 'bg-surface text-fg border border-border hover:bg-int-hover',
    ghost:     'bg-transparent text-fg-muted hover:bg-int-hover',
    accent:    'bg-int-subtle text-accent border border-accent hover:bg-int-hover',
  };
  const SIZES = { sm: 'px-3 py-1.5 text-button-sm', md: 'px-4 py-2 text-button', lg: 'px-5 py-2.5 text-button-lg' };
</script>

<button
  {disabled}
  {onclick}
  class="inline-flex items-center gap-2 rounded-md font-medium tracking-tight transition-colors
         disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40
         {VARIANTS[variant]} {SIZES[size]}">
  {#if icon}<Icon name={icon} size={14} />{/if}
  {@render children?.()}
</button>
```

## Mapping notes

- `useState(hover)` + mouse handlers → delete; use `hover:` Tailwind variants.
- React `children` → a `Snippet` rendered with `{@render children?.()}`.
- React `onClick`/`onChange` → Svelte `onclick`/`oninput` (lowercase, Svelte 5 event
  attributes). Two-way controls (`Input`, `Toggle`) use `bind:value`/`bind:checked` or
  a `value` prop + `onchange` callback to mirror the source's controlled pattern.
- Hooks/`useEffect` for icon rendering disappear — `lucide-svelte` renders directly.
- Keep prop names aligned with the source so ported pages read the same.

Tokens, fidelity checklist, and page-demo rebuilding are the same as the React path
(`references/component-conversion.md`, `references/tokens-and-tailwind.md`).
