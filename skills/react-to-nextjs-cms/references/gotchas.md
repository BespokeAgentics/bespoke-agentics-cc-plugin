# Gotchas — the cross-cutting failure catalog

The recurring ways a Next.js + self-hosted Tina build breaks. Skim before Phase 8; consult when something
fails. Most are one-liners that cost an hour if missed.

## Build / config

- **Missing `transpilePackages`.** `tinacms`, `tinacms-authjs`, `@tinacms/datalayer`,
  `tinacms-gitprovider-github` ship untranspiled — omit them from `transpilePackages` and `next build`
  fails to compile. #1 self-hosted breakage.
- **No `/admin` rewrite.** Without `{ source: "/admin", destination: "/admin/index.html" }` the admin SPA
  (built to `public/admin/`) 404s at `/admin`.
- **`public/admin/` committed or missing.** It's a build artifact of `tinacms build` — gitignore it, and
  make sure `tinacms build` runs before `next build` (the `build` script order matters).
- **`tina/__generated__/` committed / `tina-lock.json` ignored.** Invert it: ignore `tina/__generated__/`
  (via `tina/.gitignore` = `__generated__`), commit `tina/tina-lock.json`.
- **Wrong auth API names.** Use `authProvider:` + `LocalBackendAuthProvider`/`AuthJsBackendAuthProvider`
  (route) and `LocalAuthProvider`/`UsernamePasswordAuthJSProvider` (config). Older docs show
  `authentication:`/`*Authentication()` — those are stale.
- **Import path for the AuthJS config provider** is literally `tinacms-authjs/dist/tinacms`.

## Runtime / editing

- **`data-tina-field` on a React component.** Components can't receive arbitrary DOM attributes — the
  outline won't appear. Put it on a real element (`<h1>`, `<p>`, `<img>`); pass `tinaField(...)` down as a
  prop and spread it onto the inner element.
- **Editing stale content in App Router.** App Router caches aggressively; edits look like they didn't
  save. Put `export const revalidate = 0` (or `dynamic = "force-dynamic"`) on editable routes, or pass
  `{ fetchOptions: { next: { revalidate: 0 } } }` to the query.
- **`useTina` not fed the full result.** The Server Component must pass the whole
  `{ data, query, variables }` into the client component; passing only `data` disables live editing.
- **Cloud env vars leaking into self-hosted.** `NEXT_PUBLIC_TINA_CLIENT_ID`/`TINA_TOKEN`/
  `NEXT_PUBLIC_TINA_BRANCH` present → Tina tries Cloud mode. Keep them unset for self-hosted.
- **Block discriminator confusion.** On disk the field is `_template`; in query results it's `__typename`
  (`PageBlocks<Template>`). Switch on `__typename` in the render.

## Platform

- **`export const runtime = "edge"` anywhere** breaks Cloudflare (OpenNext is Node-only) and the Tina Node
  backend on both hosts. Never set it; strip it if the prototype-derived code has it.
- **`nodejs_compat` / compat date on Cloudflare.** Required, date ≥ 2024-09-23, or the Tina backend throws
  on Node built-ins.
- **`next-on-pages` on Cloudflare.** Deprecated/archived — use `@opennextjs/cloudflare` (Workers).
- **MongoDB on Cloudflare Workers.** Raw TCP + no SRV DNS + connection churn = fragile. Use Upstash Redis on
  CF; keep MongoDB for Vercel.
- **"Vercel KV" on Vercel.** Discontinued Dec 2024 — provision Upstash via the Vercel Marketplace instead.
- **Worker bundle size.** The Tina stack is heavy vs. the ~10 MiB (paid) Worker limit; monitor on CF.

## Versions (mid-2026, pin these)

`tinacms` ^3 · `@tinacms/cli` ^2 · `@tinacms/datalayer` ^2 · `tinacms-authjs` ^24 ·
`tinacms-gitprovider-github` ^4 · `next-auth` ^4 (**not** 5/Auth.js-v5 beta) · `upstash-redis-level` ^1 ·
`mongodb-level` ^0 · `@opennextjs/cloudflare` latest + `wrangler` ≥ 3.99. `react-dnd` +
`react-dnd-html5-backend` are peer requirements of the Tina admin — include them. `mongodb-level` is pre-1.0;
flag its immaturity if the user picks MongoDB.

## Content / fidelity

- **Half-externalized pages.** If any visible copy still can't be clicked-to-edit, it's still hardcoded.
  Grep the ported components for string literals that match `content_candidates`.
- **Losing the motion/design.** The prototype's `enhance.js` reveal and the exact token colors are part of
  fidelity — port them, don't drop them. Verify against the rendered `*.html` snapshot.
- **Shipping the tweaks panel or `<image-slot>`.** Those are prototype scaffolding — replace with Tina
  fields + `next/image`, don't carry them into the app.
