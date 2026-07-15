---
name: "bespokeagentics:react-to-nextjs-cms"
description: "Bootstrap a runtime-Babel React prototype (a claude.ai 'omelette' site — JSX transpiled in-browser, a _ds design-system bundle, image-slot, a tweaks/edit-mode panel, content hardcoded in JSX) into a real, deployable Next.js (App Router) app with self-hosted TinaCMS, so the end user can edit the site inline / in-place — no formal CMS. Externalizes baked-in copy into Git-backed content files, models it as Tina collections/blocks, and wires useTina+tinaField visual editing. Ships a --deploy cloudflare|vercel switch (Cloudflare via OpenNext + Upstash Redis + R2; Vercel native). Runs in ultracode mode: component/page porting and content externalization fan out across parallel subagent waves."
argument-hint: "<source-dir> [--deploy cloudflare|vercel] [--db upstash|mongodb] [--tina self-hosted|cloud] [--editing visual|forms] [--media git|r2|s3] [--pages all|a,b] [--name <slug>] [--out <dir>]"
allowed-tools: Skill(react-to-nextjs-cms), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# React prototype → Next.js + TinaCMS

Run the `react-to-nextjs-cms` skill: turn a runtime-Babel React prototype into a Next.js App-Router
app whose content the end user can edit **in place**, backed by **self-hosted TinaCMS** (open source,
Git-backed — no formal CMS), deployable to Cloudflare (default) or Vercel.

## Arguments

Parse from `$ARGUMENTS`:

```
<source-dir> [--deploy cloudflare|vercel] [--db upstash|mongodb] [--tina self-hosted|cloud]
             [--editing visual|forms] [--media git|r2|s3] [--pages all|<comma-list>]
             [--name <slug>] [--out <dir>]
```

- `<source-dir>` (required) — the prototype folder (the one containing `index.html` + `site/*.jsx` + `_ds/`). If omitted, ask.
- `--deploy` — deploy target. Default `cloudflare` (OpenNext on Workers). `vercel` is the lower-friction Tina path.
- `--db` — Tina datalayer. Default `upstash` (Redis over HTTP — runs on both platforms). `mongodb` is Vercel-only in practice.
- `--tina` — `self-hosted` (default, open source) or `cloud` (managed).
- `--editing` — `visual` (default, on-page click-to-edit) or `forms` (/admin dashboard only).
- `--media` — `git` (default, static) / `r2` / `s3`.
- `--pages` — which prototype pages to port. Default `all`.
- `--name` / `--out` — app name and output dir (both derived by default).

## Process

Invoke the `react-to-nextjs-cms` skill and forward `$ARGUMENTS`. The skill will:

1. **Analyze** — run `scripts/analyze_prototype.py` to inventory the runtime-Babel prototype (pages,
   `_ds` design system, image-slots, the tweaks/EDITMODE block, fonts, and the hardcoded
   `content_candidates`); read the key source.
2. **Plan & confirm** — the target stack, deploy target + datalayer + media (surfacing the
   Cloudflare-vs-Vercel tradeoff), the content model (collections/blocks), the editable-fields
   inventory, and the pages — before writing anything.
3. **Scaffold** — run `scripts/scaffold_nextjs_tina.py` to write the Next.js + self-hosted Tina
   skeleton (config, database, backend route, `/admin`, deploy config for `--deploy`); `npm install`.
4. **Tokens** — carry the `_ds` design tokens into a Tailwind v4 `@theme` layer.
5. **Port (ultracode)** — golden-reference port + conventions contract, then dependency-wave fan-out of
   `component-porter` agents for the design system + pages (RSC/client split, `next/image`, lucide).
6. **Model content** — externalize each page's baked copy/images into `content/*.json`, define the Tina
   collections/blocks, and wire `useTina` + `tinaField` so every editable element is click-to-edit.
7. **Backend & deploy** — finalize datalayer/auth/media and the target's deploy config.
8. **Verify & hand off** — reconciler sweep, `tinacms dev` + build, env checklist, deploy command, and
   the honest self-hosted caveats (no search, build-time branch, media strategy).

## Output

A deployable Next.js + self-hosted TinaCMS app in `--out` (default `./<name>-app`): the design faithfully
reproduced, the content externalized into `content/**` and editable in place, and the deploy config for
Cloudflare or Vercel wired. Wiki-ingested when a vault exists. Companion to
`/bespokeagentics:funcspec-evaluate` and `claude-design-to-app-workflow` (`design-zip-to-library`).
