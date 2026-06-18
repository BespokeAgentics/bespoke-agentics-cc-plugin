# Target: custom React (plain, no framework opinions)

The simplest React target: typed components, Tailwind v4 classes, a tiny `cn` helper.
Use when `--library custom --framework react`, or when the user wants a dependency-light
library without Untitled UI's React Aria layer or shadcn's Radix layer.

## Deps (in `@<scope>/ui`)

```
react react-dom lucide-react clsx tailwind-merge
```

## Class helper — `src/lib/cn.ts`

```ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));
```

## Component pattern

Keep it boring and explicit. A `variants`/`sizes` lookup of class strings, merged by
`cn`, with literal-union props (pulled from the source's own variant keys):

```tsx
import { cn } from "../lib/cn";

const VARIANTS = {
  primary:   "bg-accent text-white hover:bg-accent-strong",
  secondary: "bg-surface text-fg border border-border hover:bg-int-hover",
  ghost:     "bg-transparent text-fg-muted hover:bg-int-hover",
  accent:    "bg-int-subtle text-accent border border-accent hover:bg-int-hover",
} as const;
const SIZES = {
  sm: "px-3 py-1.5 text-button-sm",
  md: "px-4 py-2 text-button",
  lg: "px-5 py-2.5 text-button-lg",
} as const;

export type ButtonProps = {
  variant?: keyof typeof VARIANTS;
  size?: keyof typeof SIZES;
  icon?: string; iconRight?: string;
  disabled?: boolean;
} & React.ButtonHTMLAttributes<HTMLButtonElement>;

export function Button({ variant = "primary", size = "md", className, icon, iconRight, children, ...rest }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center gap-2 rounded-md font-medium tracking-tight whitespace-nowrap",
        "transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
        VARIANTS[variant], SIZES[size], className,
      )}
      {...rest}
    >
      {icon && <Icon name={icon} size={14} />}
      {children}
      {iconRight && <Icon name={iconRight} size={14} />}
    </button>
  );
}
```

## Notes

- Deriving unions from `keyof typeof VARIANTS` keeps props and styles in lockstep — add
  a variant and the type updates for free.
- Spread native element props (`...rest`) so `onClick`, `type`, `aria-*` just work; no
  need to re-declare each one the source listed.
- For form controls (`Input`, `Toggle`, `Textarea`), prefer native elements + classes;
  reach for React Aria only if you need richer a11y than native gives. If you want that
  out of the box, use the `untitled-ui-react` target instead.
- Everything else (icons, stories, fidelity checklist) follows
  `references/component-conversion.md`.
