---
name: react-to-nextjs-cms
description: >-
  Bootstrap a runtime-Babel React prototype (a claude.ai "omelette"-style site — JSX
  pages transpiled in-browser by @babel/standalone, a `_ds` design-system bundle, an
  image-slot custom element, a tweaks/edit-mode panel, and content hardcoded in JSX)
  into a real, deployable **Next.js (App Router) app with self-hosted TinaCMS** so the
  end user can edit the site **inline / in-place** — no formal CMS. Externalizes the
  baked-in content into Git-backed content files, models it as Tina collections/blocks,
  and wires `useTina`+`tinaField` visual editing. Ships a `--deploy cloudflare|vercel`
  switch (Cloudflare via OpenNext + Upstash Redis + R2; Vercel native). Use when someone
  says "make this prototype editable", "turn the ProTec/omelette site into a Next.js app
  with a CMS", "add TinaCMS to my React site", "inline editing without a CMS", "convert
  this in-browser-Babel React SPA to Next.js", "let my client edit the copy", or points
  you at a static React prototype folder and asks for an editable, deployable version.
  Companion to `claude-design-to-app-workflow` (that skill recovers the component library
  from a design zip; this one turns a prototype site into an editable, deployed app).
  Runs in ultracode mode: component/page porting and content externalization fan out
  across parallel subagent waves.
---

**Invocation.** The user points you at a prototype (a folder like `…/protec-website/site`,
or an `index.html` that loads React + `@babel/standalone` from a CDN) and optionally passes
flags, e.g. `/react-to-nextjs-cms "…/Protec website planning/site" --deploy vercel --db mongodb`.
Parse the source path and any `--flag value` tokens (see Configuration). If no path is given,
ask for it; if no flags, use the defaults (**Cloudflare + Upstash + self-hosted + visual editing**).

You convert a **runtime-Babel React prototype** into a **production Next.js App-Router app whose
content is editable in place by a non-developer**, backed by **self-hosted TinaCMS** (open source,
Git-backed — the content lives as Markdown/JSON in the repo, no third-party CMS). The input is the
kind of site the claude.ai "omelette" starter produces: `index.html` pulls `react`, `react-dom`,
and `@babel/standalone` off a CDN and `<script type="text/babel">`-loads `site/*.jsx` pages that
consume a `_ds/<id>/_ds_bundle.js` design system; images go through an `<image-slot>` custom
element; a `tweaks-panel.jsx` provides an authoring-time edit mode (postMessage → disk) that only
works inside the starter's harness. **All real copy is hardcoded in the JSX.** Your job is to lift
that into a Next.js app where the design is faithfully reproduced, the content is externalized into
Tina collections, and every editable string/image is click-to-edit on the live page.

The defining work is **content externalization + Tina wiring**, not just a framework port. A pretty
Next.js clone that still hardcodes its copy has missed the point — the deliverable is *editable*.

## When to use

Use this for any "prototype → editable, deployable app" request. The user may hand you only a folder
and a goal ("make the ProTec site something the client can edit", "add a CMS", "get this off the
in-browser-Babel setup"). They may not name the steps — infer them. This skill is **dynamic**: it
inspects whatever prototype it's handed (page count, design system, image slots, tweak knobs all
vary) and generates from that. It is not specialized to ProTec.

**Not this skill:** a design *zip* → component library + Storybook is `claude-design-to-app-workflow`
(`design-zip-to-library`). If the user wants only the library, use that. If they have a zip *and*
want an editable deployed app, run that skill first for a clean component library, then this one to
wire it into Next.js + Tina (this skill also handles a raw prototype directly).

## Configuration (flags)

Read these from `args` (or ask if ambiguous). Sensible defaults mean you can run with none.

| Flag | Default | Options | Effect |
|------|---------|---------|--------|
| `--deploy` | `cloudflare` | `cloudflare`, `vercel` | Deploy target. Cloudflare = OpenNext on Workers; Vercel = native. Both always emitted-able. See `references/deploy-cloudflare.md` / `deploy-vercel.md`. |
| `--db` | derived | `upstash`, `mongodb` | Tina datalayer. **`upstash` (Redis over HTTP) is the only one that runs on Cloudflare Workers**; `mongodb` (raw TCP) is Vercel-only in practice. Default: `upstash` for cloudflare, `upstash` for vercel (pick `mongodb` only if the user wants document storage on Vercel). |
| `--tina` | `self-hosted` | `self-hosted`, `cloud` | Open-source self-hosted backend (default) vs Tina Cloud (managed — adds search, runtime branch switch, media CDN; not open source). |
| `--editing` | `visual` | `visual`, `forms` | `visual` = on-page click-to-edit (`useTina`+`tinaField`); `forms` = `/admin` dashboard only. |
| `--media` | derived | `git`, `r2`, `s3` | Where images live. Default: `git` (static, simplest); `r2` for cloudflare at scale; `s3` for vercel. |
| `--name` | derived | any | App/package name + Worker name. Derived from the source (e.g. `protec`). |
| `--out` | `./<name>-app` | any path | Where the Next.js app is written. Don't write into the prototype's folder. |
| `--pages` | `all` | `all`, comma-list | Which prototype pages to port (e.g. `home,services`). |

`--deploy` drives the defaults for `--db` and `--media` and which config templates are emitted. When
a requested combination is unsafe (e.g. `--deploy cloudflare --db mongodb`), **warn and proceed only
if the user insists** — MongoDB from a Worker has no SRV DNS and connection-churn problems
(`references/deploy-cloudflare.md`). The best-trodden path is **Cloudflare + Upstash + self-hosted +
visual**; lean on it unless flags say otherwise.

## The pipeline

Work through these phases in order. Each builds on the last. The two bundled scripts remove the rote
inventory/scaffold work so effort goes into faithful porting, content modeling, and Tina wiring.

**Ultracode orchestration.** Phases 0–4 and 6–7 are main-thread (global decisions: analysis, scaffold,
tokens, content model, backend, deploy). Phase 5 delegates the per-file work — every design-system
component and every page — to parallel `component-porter` subagents in dependency waves. Phase 6's
content externalization fans a `content-porter` per page in parallel. Phase 8 opens with a
`reconciler` sweep. The main thread never bulk-ports; it writes the contract, gates the waves, and
judges results. Protocol: `references/parallel-porting.md`.

### Phase 0 — Preflight

1. Node ≥ 20 (`node -v`); a package manager (prefer `pnpm`, else `npm`). If missing, print the install line and stop.
2. Resolve the source path from `args`. If none, ask. Print it so a wrong folder is obvious.
3. Resolve flags (Configuration). Pick `--out` (default `./<name>-app`); never write into the prototype's own folder.

### Phase 1 — Analyze the prototype (deep, not shallow)

Run the bundled analyzer — it inventories so you don't have to:

```bash
python3 <skill>/scripts/analyze_prototype.py "<source-dir>" --out <work>/analysis.json
```

It writes `analysis.json` with: `runtime` (confirms in-browser Babel + the React/Babel CDN tags),
`html_entries`, `pages` (each `site/*.jsx` + the `<script>` that mounts it), the **design system**
(`_ds` id, `tokens/*.css`, `_ds_manifest.json`, `_ds_bundle.js`, the `window.*` namespace),
`components` (name + props, from the bundle/manifest), `image_slots` (uses of `<image-slot>` /
`image-slot.js`), the `tweaks` block (the `EDITMODE-BEGIN/END` defaults + `TweakRadio/Select/…`
knobs — candidate Tina fields), `fonts`, and **`content_candidates`** — the hardcoded strings/images
in the JSX that should become editable. See `references/analysis.md`.

Then **read the actual source** the manifest points to — at minimum the design-system tokens, one or
two page JSX files, and the tweaks panel — to learn *how* it's built and to sanity-check the content
inventory. `references/analysis.md` covers the runtime-Babel prototype anatomy in full.

### Phase 2 — Plan & confirm

Before scaffolding (it writes many files) and before any deploy-specific choices, show a tight plan:
the target stack (Next.js App Router + TS + Tailwind v4 + self-hosted Tina), the resolved
**deploy target + datalayer + media** and *why* (surface the Cloudflare-vs-Vercel tradeoff —
`references/deploy-cloudflare.md` §tradeoffs), the **content model** (the collections + the
blocks/sections you'll model each page as — `references/content-modeling.md`), the **editable-fields
inventory** (what becomes click-to-edit), the pages to port (`--pages`), and the app layout. This is
*confirm the model*, not re-derive it. Proceed; adjust to corrections.

### Phase 3 — Scaffold the Next.js + Tina app

Run the bundled scaffolder — it writes the whole skeleton (Next App Router app, Tailwind v4, the Tina
config/database/backend route, the `/admin` wiring, env template, seed user, and the **deploy config
for `--deploy`**) with the correct dependency set, and the empty tree builds clean:

```bash
python3 <skill>/scripts/scaffold_nextjs_tina.py \
  --out <name>-app --name <name> \
  --analysis <work>/analysis.json --deploy <cloudflare|vercel> --db <upstash|mongodb>
cd <name>-app && pnpm install   # or npm install
```

The layout it produces (see `references/self-hosted-backend.md`):

```
<name>-app/
├── package.json            # next + tinacms stack + tailwind (+ @opennextjs/cloudflare if CF)
├── next.config.mjs         # transpilePackages (the 4 Tina pkgs) + /admin rewrite (+ OpenNext dev hook if CF)
├── tina/
│   ├── config.tsx          # defineConfig: authProvider, contentApiUrlOverride, build, media, collections
│   ├── database.ts         # createDatabase: GitHubProvider + RedisLevel|MongodbLevel  (createLocalDatabase when local)
│   └── collections/        # one file per collection (page, …)
├── pages/api/tina/[...routes].ts   # TinaNodeBackend (Pages-Router file; coexists with app/)
├── app/                    # App Router: layout.tsx, page.tsx (RSC fetch) + client components (useTina)
├── content/                # externalized content (md/mdx/json) + users/index.json seed
├── public/                 # static assets + built admin SPA (public/admin, gitignored)
├── wrangler.jsonc          # CF only: OpenNext worker + nodejs_compat + assets
├── open-next.config.ts     # CF only
└── .env / .env.example
```

The scaffolder pre-writes every config file from verified templates (`assets/templates/`), so Phases
4–7 are mostly *filling* a working skeleton, not configuring one.

### Phase 4 — Tokens & design system

Port the prototype's `_ds` design system into the app:
1. Copy the token sheets (`_ds/<id>/tokens/*.css` + `styles.css`) into the app and generate a Tailwind
   v4 `@theme` layer so the design's `--flame-500`/`--ink-700`/etc. drive utilities. The inline-style →
   utility-class mapping and the `@theme inline` theming model are the **same playbook** as the sibling
   skill — reuse `claude-design-to-app-workflow/references/tokens-and-tailwind.md`.
2. Carry the fonts (`@import` or `next/font`), keyframes, and the `enhance.js` motion layer (scroll
   reveal, hero load-in) as a small client effect or CSS. Preserve the design exactly.

### Phase 5 — Port the design system + pages (parallel waves)

Follow `references/component-porting.md` (Next.js specifics) + `references/parallel-porting.md` (the
ultracode protocol). In brief: port the most-used primitive yourself as the **golden reference** and
write `<work>/conventions.md`; build dependency waves (leaf DS components → composites → pages);
fan out one `component-porter` per item per wave; gate `tsc --noEmit`/`next build` between waves. The
key Next.js judgment calls: **Server Component by default, `"use client"` only where a component is
interactive or calls `useTina`**; `<image-slot>` → `next/image` bound to a Tina `image` field;
`data-lucide` → `lucide-react`; `window.ProTec*` globals → real imports.

### Phase 6 — Content modeling & Tina schema (the heart)

This is where "editable" is won. Follow `references/content-modeling.md` + `references/tina-schema.md`:
1. **Externalize** each page's hardcoded copy/images into a `content/` file. Model a marketing page as
   a **blocks list** (`object` + `list: true` + `templates: [hero, services, cta, …]`) so the editor can
   reorder/add sections — the page-builder pattern.
2. **Define collections** in `tina/config.tsx` (+ `tina/collections/*.ts`), including `TinaUserCollection`.
3. **Wire visual editing**: the App-Router page is a Server Component that fetches via the generated
   client, passes `{data, query, variables}` into a `"use client"` component that calls `useTina`, and
   every editable element carries `data-tina-field={tinaField(obj, "prop")}` so clicking it on the live
   page focuses that field in the sidebar. Map the old `tweaks-panel` knobs (accent, hero layout, …)
   to Tina fields where they should stay editable.
   Content-externalization fans out: one `content-porter` per page, in parallel.

### Phase 7 — Backend, auth, media & deploy config

Finalize per `references/self-hosted-backend.md` + `references/deploy-<target>.md`:
- `tina/database.ts` datalayer for `--db` (Upstash `RedisLevel` or `MongodbLevel`), `GitHubProvider`,
  and the `TINA_PUBLIC_IS_LOCAL` local/prod split (`createLocalDatabase()` locally).
- `pages/api/tina/[...routes].ts` (`TinaNodeBackend`, Auth.js in prod / `LocalBackendAuthProvider` local).
  **Never mark this route `runtime = "edge"`.**
- Media for `--media` (`git` static, or `r2`/`s3` via `next-tinacms-s3`).
- Deploy config: Cloudflare (`wrangler.jsonc` + `open-next.config.ts`, `nodejs_compat`, build via
  `opennextjs-cloudflare build && … deploy`) or Vercel (native; provision Upstash via Marketplace since
  Vercel KV was sunset Dec 2024). Fill the env checklist.

### Phase 8 — Verify & hand off

- **Reconciliation sweep first:** one `reconciler` agent over `app/` + `tina/` + `content/` fixes idiom
  drift (RSC/client boundary consistency, stray hardcoded copy a porter missed, `data-tina-field` on
  real elements not React components, token-class vs raw hex) and reports judgment calls.
- Local check: `pnpm dev` runs `tinacms dev -c "next dev"`; open `/` and confirm click-to-edit works
  (edit mode → click a heading → sidebar focuses the field), then `/admin` loads.
- Build check: `tinacms build && next build` (CF: `opennextjs-cloudflare build`) — report real output;
  if it fails, fix or surface it, don't claim success it didn't earn. Consult `references/gotchas.md`.
- Hand off: env checklist (GitHub token, `NEXTAUTH_SECRET`, datalayer creds), the deploy command for the
  target, how to change the seed admin password, and the **self-hosted caveats** (no search, build-time
  branch only, media strategy). Summarize what became editable and any judgment calls.
- Offer the next step: point the client at `/admin` to set their password, or `--deploy` the other target.

## Reference map

Read these as the phase calls for them — don't preload everything.

| Need | Read |
|------|------|
| Interpret `analysis.json`; runtime-Babel prototype anatomy; content-candidate judgment | `references/analysis.md` |
| Runtime-Babel JSX → Next.js App Router (RSC/client split, next/image, lucide, globals, motion) | `references/component-porting.md` |
| Externalize baked content → collections/blocks; map tweak knobs → fields | `references/content-modeling.md` |
| `tina/config.tsx`, field types, blocks, `useTina`/`tinaField`, `/admin`, preview router, caching | `references/tina-schema.md` |
| `database.ts`, `[...routes].ts`, auth, env, local/prod split, the demo file layout | `references/self-hosted-backend.md` |
| Cloudflare deploy: OpenNext, wrangler, Upstash, R2, gotchas + the CF-vs-Vercel tradeoff | `references/deploy-cloudflare.md` |
| Vercel deploy: native, Upstash-via-Marketplace/Mongo, git env fallbacks, gotchas | `references/deploy-vercel.md` |
| Wave construction, porter contract, between-wave gates, reconciliation | `references/parallel-porting.md` |
| The cross-cutting failure catalog (transpilePackages, edge ban, caching, admin rewrite, version pins) | `references/gotchas.md` |
| Token sheet → Tailwind v4 `@theme` (shared) | `claude-design-to-app-workflow/references/tokens-and-tailwind.md` |
| Port one component's styles/props (shared playbook) | `claude-design-to-app-workflow/references/component-conversion.md` |

## Principles

- **Editable is the deliverable.** A faithful Next.js clone that still hardcodes its copy has failed the
  brief. Every headline, paragraph, list item, phone number, and image the client would want to change
  must be a Tina field, click-to-edit on the page.
- **Recover, don't redesign.** The prototype already encodes taste — tokens, spacing, type scale, motion.
  Lift it faithfully; don't "improve" it.
- **Content is Git, not a database.** Self-hosted Tina's datalayer is a cache/index; the source of truth
  is Markdown/JSON committed to the repo. That's the "no formal CMS" promise — respect it.
- **The datalayer decides the platform.** Upstash Redis (HTTP) runs everywhere; MongoDB (TCP) is
  Vercel-only in practice. Choose the store before the host, not after.
- **Scripts do the rote part.** Inventory and scaffold are deterministic; let the bundled scripts do them.
- **The orchestrator owns taste; the agents own throughput.** Conventions decided once (golden reference +
  contract), enforced everywhere (porters follow, reconciler sweeps). Parallelism never votes on idiom.
- **Report honestly.** If `next build` fails, say so with the error. Half-wired editing is in-progress,
  not done. Name the self-hosted caveats (no search, build-time branch) rather than letting them surprise.
