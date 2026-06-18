# Component conversion playbook

How to port one source component (inline-styled React from a claude.ai export) into a
real, typed, themed library component. This is the universal part; the target-specific
authoring idiom (Untitled UI `sortCx`/`cx`/React Aria, shadcn `cn`, plain custom,
Svelte, Lit) lives in `references/targets/<…>.md`. Read both.

## The mapping, step by step

Source primitives look like this (real example from a Foundry export):

```jsx
function Button({ children, variant='primary', size='md', icon, iconRight, onClick, disabled, type='button' }) {
  const [hover, setHover] = useState(false);
  const sizes = { sm:{padding:'6px 12px',fontSize:12}, md:{padding:'8px 16px',fontSize:13}, lg:{padding:'10px 20px',fontSize:14} };
  const variants = {
    primary:   { background: hover ? 'var(--accent-strong)' : 'var(--accent-default)', color:'#fff' },
    secondary: { background: hover ? 'var(--int-hover)' : 'var(--surface-default)', color:'var(--text-primary)', border:'1px solid var(--border-default)' },
    ghost:     { background: hover ? 'var(--int-hover)' : 'transparent', color:'var(--text-secondary)' },
  };
  return <button onMouseEnter={…} style={{ ...base, ...sizes[size], ...variants[variant] }}>…</button>;
}
```

### 1. Props → typed unions

The analyzer already extracted prop names + defaults. Turn the string-defaulted props
into literal unions; keep defaults:

```ts
type ButtonProps = {
  variant?: 'primary' | 'secondary' | 'ghost' | 'accent';
  size?: 'sm' | 'md' | 'lg';
  icon?: string; iconRight?: string;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  onClick?: () => void;
  children?: React.ReactNode;
};
```

Pull the union members straight from the source's `variants`/`sizes` object keys — they
are the source of truth, not your guess.

### 2. Inline-style colors → utility classes (use `tokens.index.json`)

For every `someProp: 'var(--x)'`, look up `css_var_usage["x"][cssProp]` to get the
utility class. From the Foundry index:

| Source inline style | Utility |
|---|---|
| `background:'var(--accent-default)'` | `bg-accent` |
| `background:'var(--accent-strong)'` (hover) | `hover:bg-accent-strong` |
| `color:'var(--text-primary)'` | `text-fg` |
| `color:'var(--text-secondary)'` | `text-fg-muted` |
| `background:'var(--surface-default)'` | `bg-surface` |
| `border:'1px solid var(--border-default)'` | `border border-border` |
| `background:'var(--int-hover)'` (hover) | `hover:bg-int-hover` |

Hover/press handled by `useState` in the source becomes `hover:`/`active:` variants —
delete the state and the mouse handlers. Literal values the design used directly
(`color:'#fff'`, `borderRadius:6`) become `text-white`, `rounded-md` (6px ≈ your
`--radius-sm`/`md`; match the token, e.g. `rounded-[6px]` if no token fits).

### 3. Numeric/spacing styles → utilities

`padding:'8px 16px'` → `px-4 py-2` (using the token scale; `--sp-4=16`, `--sp-2=8`).
`gap:8` → `gap-2`. `fontSize:13` → `text-button` (or the closest `--text-*`). When a
value is off-scale, use an arbitrary value `p-[7px]` rather than rounding and drifting.

### 4. Compose with the target's class helper

- **Untitled UI**: declare `const styles = sortCx({ common, sizes:{…}, colors:{…} })`
  and merge with `cx(...)`; derive `size`/`color` unions from `keyof typeof styles.*`.
  See `targets/untitled-ui-react.md` for the exact pattern.
- **shadcn / custom React**: `cva()` or a plain `cn(base, variants[variant], sizes[size])`.
- Keep the variant→classes table readable; it's the component's spec.

### 5. Icons: `data-lucide` → a real icon system

Source uses `<i data-lucide="upload-cloud"/>` resolved by a global `lucide.createIcons()`
pass. In the library, import from `lucide-react` and render by name:

```tsx
import { icons } from 'lucide-react';
function Icon({ name, size = 16 }: { name: string; size?: number }) {
  const L = icons[toPascal(name)]; return L ? <L size={size} /> : null;
}
```

Keep the prop as an icon *name string* so page code that passed `icon="upload-cloud"`
still works. (For Svelte/Lit use `lucide-svelte` / `lucide`/SVG per that target.)

### 6. Stories alongside the component

Co-locate `Button.stories.tsx`. Drive `argTypes` from the prop unions so Storybook gives
real controls; add a story per meaningful variant and a "kitchen sink" showing all
sizes × variants:

```tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';
const meta: Meta<typeof Button> = {
  title: 'Primitives/Button', component: Button,
  argTypes: { variant: { control: 'select', options: ['primary','secondary','ghost','accent'] },
              size: { control: 'select', options: ['sm','md','lg'] } },
};
export default meta;
export const Primary: StoryObj<typeof Button> = { args: { children: 'Get started', variant: 'primary' } };
export const AllVariants: StoryObj<typeof Button> = { render: () => (
  <div className="flex gap-3">{['primary','secondary','ghost','accent'].map(v =>
    <Button key={v} variant={v as any}>{v}</Button>)}</div>) };
```

## Fidelity checklist (per component)

- Same visual result in **both** themes (toggle in Storybook and eyeball vs the
  source `screenshots/`). Theme breakage usually means a hard-coded color slipped in
  instead of a semantic token. Use `bg-accent`/`text-fg` etc., not raw hex — *except*
  where the source itself hard-codes meaning-bearing palettes (e.g. `FileIcon` per-file
  type colors, `FindingTypePill`/`SevBadge` per-severity colors). Those are faithful as
  hex; promote them to tokens only if you want them themeable. Don't tokenize brand SVG
  logos — they're assets, not styles.
- Every source variant/size/tone reproduced — don't silently drop the `accent` button
  variant or a `Badge` tone.
- Interactive states (hover/press/focus/disabled) preserved as variants, with a visible
  `focus-visible:` ring for a11y even if the source lacked one.
- Props match the source names so composed pages keep working unchanged.
- No leftover `useState` purely for hover, no `data-lucide`, no `window.*` access.

## Order of work

Port the most-used primitive first (usually `Button`), get it reviewed/looking right in
Storybook, then fan out — later components reuse the same token-class mapping and
patterns, so the first one sets the template. Composite layout components
(`Shell`/`Sidebar`/`TopBar`) come after primitives since they consume them.
