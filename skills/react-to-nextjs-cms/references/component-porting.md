# Porting runtime-Babel JSX → Next.js App Router

How to turn one prototype component (a `window`-exported, inline-styled React function transpiled in the
browser) into a real Next.js App-Router component. The **style/prop/token mapping is the shared playbook**
in `claude-design-to-app-workflow/references/component-conversion.md` (inline `style={{…var(--x)…}}` →
Tailwind utility classes via the token map, string-defaulted props → typed unions, `data-lucide` →
`lucide-react`) and `…/tokens-and-tailwind.md` — read those. This file covers only what's **Next.js- and
Tina-specific**.

## The Server/Client boundary — the first decision for every component

Next.js App Router renders Server Components by default. Choose per component:

- **Server Component (no directive)** — the default. Pure presentational design-system pieces (`Button`,
  `Card`, `Badge`, `SectionEyebrow`, static layout) that take props and render markup. Faster, smaller
  bundle, can be `async`.
- **`"use client"`** — required when the component:
  - calls a hook (`useState`/`useEffect`/`useTina`),
  - attaches event handlers (`onClick`, `onMouseEnter`),
  - uses browser APIs (`IntersectionObserver`, `window`, `matchMedia`),
  - or is the component that runs `useTina` for live editing (see `tina-schema.md`).

Rule of thumb for these prototypes: **the design-system primitives are Server Components; the page
"view" component that calls `useTina` is a Client Component; interactive bits (mobile nav toggle, the old
hover/reveal effects) are small Client Components.** Keep the client boundary as low in the tree as
possible — wrap the interactive leaf, not the whole page.

```tsx
// Server Component — the common case
export function Button({ variant = "primary", size = "md", icon, children, ...rest }: ButtonProps) {
  return <button className={cn(BASE, VARIANTS[variant], SIZES[size])} {...rest}>{icon && <Icon name={icon}/>}{children}</button>;
}
```

```tsx
"use client";           // only where needed
import { useEffect } from "react";
export function ScrollReveal({ children }: { children: React.ReactNode }) {
  useEffect(() => { /* IntersectionObserver — the enhance.js reveal, ported */ }, []);
  return <div className="protec-reveal">{children}</div>;
}
```

## `window.*` globals → real imports

The prototype wires everything through globals: `window.ProTecDesignSystem_<id>.Button`,
`window.ProTecHome`, `window.ProTecShared`. Replace each with an ESM import:

| Prototype | Next.js |
|---|---|
| `window.ProTecDesignSystem_37762d.Button` | `import { Button } from "@/components/ds/button"` |
| `<window.ProTecHome …>` mounted in `index.html` | `app/(site)/page.tsx` renders `<Home …>` from `@/components/pages/home` |
| `window.ProTecShared.Header` | `import { Header } from "@/components/shared/header"` |
| `window.FINDINGS` / other shared data | a real module import or props |

Suggested tree: `components/ds/*` (design system), `components/shared/*` (header/footer/eyebrow),
`components/blocks/*` (the editable page sections — see `content-modeling.md`), `app/**` (routes).

## `<image-slot>` → `next/image` bound to a Tina field

The prototype's `image-slot.js` renders a placeholder that can hold an uploaded image. In the app, an
image is **content**: it comes from a Tina `image` field and renders through `next/image`.

```tsx
import Image from "next/image";
// data.hero.image is a Tina image field (a public path or media URL)
<Image
  src={data.hero.image}
  alt={data.hero.imageAlt ?? ""}
  width={1200} height={800}
  data-tina-field={tinaField(data.hero, "image")}   // click the image on the page → focus the field
  className="…"
/>
```

For remote media (`--media r2|s3`), add the host to `images.remotePatterns` in `next.config.mjs`. For
`--media git`, images live under `public/` and `src` is a root-relative path — no config needed.

## Motion layer (`enhance.js`) → a client effect

`site/enhance.js` injects keyframes and wires scroll-reveal / hero load-in / card lift after React mounts.
Port it as either (a) pure CSS in `globals.css` for the keyframes + a tiny `"use client"`
`<Reveal>`/effect for the `IntersectionObserver`, or (b) a single client `SiteMotion` component mounted in
the layout. Respect `prefers-reduced-motion` exactly as the original did. Don't let motion depend on a
class React re-render can clobber — the original guards against this; keep that.

## Fonts

Prototype loads Google Fonts via `<link>`. Prefer `next/font/google` (self-hosts, no layout shift, no
extra request) in `app/layout.tsx`; fall back to an `@import` in `globals.css` if a font isn't on Google
Fonts. Match the families the analyzer listed under `fonts`.

## Fidelity checklist (per component)

- Renders identically to the prototype (eyeball against the giant rendered `*.html` snapshot).
- Server/Client chosen correctly — no `"use client"` on a purely presentational primitive; no hook/handler
  in a Server Component (Next will error).
- Props keep the source names so page code composes unchanged.
- No leftover `window.*`, no `data-lucide` global pass, no in-browser-Babel assumptions.
- Semantic token utilities (`bg-[--flame-500]` / `text-ink-700` per your Tailwind theme), not stray hex —
  except meaning-bearing brand colors the design hardcodes.
- Any element that shows editable content carries a `data-tina-field` (added in Phase 6, but leave the
  prop threaded so it's a one-line add).

## Order of work

Port the most-used design-system primitive first (usually `Button`) as the golden reference, verify it
builds, then fan out per `parallel-porting.md`. Shared chrome (`Header`/`Footer`) and the page views come
after the primitives they consume.
