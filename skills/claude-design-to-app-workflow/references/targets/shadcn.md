# Target: shadcn/ui conventions

Use when `--library shadcn`. shadcn is a copy-paste-source model (components live in
your repo, not a dependency) built on Radix primitives + `class-variance-authority`
(cva) + a `cn` helper. Tailwind v4 works; shadcn's newer setup is CSS-first like ours.

## Deps (in `@<scope>/ui`)

```
react react-dom lucide-react class-variance-authority clsx tailwind-merge
# + @radix-ui/react-* only for components that need them (dialog, dropdown, switch, tabs…)
```

## Class helper — `src/lib/utils.ts`

```ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }
```

## Component pattern (cva)

```tsx
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md font-medium tracking-tight transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 disabled:opacity-50 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        primary: "bg-accent text-white hover:bg-accent-strong",
        secondary: "bg-surface text-fg border border-border hover:bg-int-hover",
        ghost: "bg-transparent text-fg-muted hover:bg-int-hover",
        accent: "bg-int-subtle text-accent border border-accent hover:bg-int-hover",
      },
      size: { sm: "h-8 px-3 text-button-sm", md: "h-9 px-4 text-button", lg: "h-10 px-5 text-button-lg" },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}
```

## Notes

- Map the design's tokens to shadcn's semantic CSS-variable names if you want stock
  shadcn components to drop in, OR keep the design's role names (`accent`, `surface`,
  `fg`) and just reference them in the cva tables — simpler and more faithful here.
- Pull in a Radix primitive only when the source component is genuinely interactive
  (switch/toggle → `@radix-ui/react-switch`, tabs → `@radix-ui/react-tabs`). Static
  components (Badge, Card, Overline) need no Radix.
- Stories, icons, fidelity: `references/component-conversion.md`.
- If unsure between shadcn and Untitled UI: Untitled UI is larger and React-Aria-based;
  shadcn is leaner and Radix-based. Both are source-in-repo.
