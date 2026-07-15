# Deploy target: Cloudflare (OpenNext on Workers)

Default target. Next.js runs on Cloudflare Workers via the **OpenNext** adapter; Tina's datalayer is
**Upstash Redis** (HTTP — the only store that runs on the Workers runtime); media is **R2**. Verified
against opennext.js.org/cloudflare and developers.cloudflare.com (mid-2026).

## Adapter: `@opennextjs/cloudflare` (NOT `next-on-pages`)

`@cloudflare/next-on-pages` is **deprecated and archived** (Sep 2025). Cloudflare's own guidance: use the
**OpenNext Cloudflare adapter**, which deploys to **Workers** (not Pages). Emit only the OpenNext path.

```bash
npm install @opennextjs/cloudflare@latest
npm install -D wrangler@latest            # >= 3.99
```

App Router, RSC, SSR, SSG/ISR, Server Actions, Middleware, Image Optimization are all supported.
**Edge runtime is NOT supported** — remove any `export const runtime = "edge"` (Tina's Node backend route
must stay on the default Node runtime anyway).

## `wrangler.jsonc`

```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "main": ".open-next/worker.js",
  "name": "<APP_NAME>",
  "compatibility_date": "2025-03-01",
  "compatibility_flags": ["nodejs_compat", "global_fetch_strictly_public"],
  "assets": { "directory": ".open-next/assets", "binding": "ASSETS" },
  "services": [{ "binding": "WORKER_SELF_REFERENCE", "service": "<APP_NAME>" }]
  // R2 for OpenNext incremental cache (optional):
  // "r2_buckets": [{ "binding": "NEXT_INC_CACHE_R2_BUCKET", "bucket_name": "<APP_NAME>-cache" }]
}
```
- **`nodejs_compat` is required** (Tina backend, datalayer, auth, GitHub provider all need Node built-ins),
  and `compatibility_date` must be **≥ 2024-09-23** for it to take effect. Bump the date freely; keep it ≤ today.

## `open-next.config.ts`

```ts
import { defineCloudflareConfig } from "@opennextjs/cloudflare";
// Optional R2 incremental cache (bind NEXT_INC_CACHE_R2_BUCKET in wrangler.jsonc):
// import r2IncrementalCache from "@opennextjs/cloudflare/overrides/incremental-cache/r2-incremental-cache";
export default defineCloudflareConfig({
  // incrementalCache: r2IncrementalCache,
});
```

## `next.config.mjs` addition

Keep the `transpilePackages` + `/admin` rewrite (from `self-hosted-backend.md`) and add the OpenNext dev
hook so `next dev` sees Cloudflare bindings:
```js
import { initOpenNextCloudflareForDev } from "@opennextjs/cloudflare";
initOpenNextCloudflareForDev();
// … export default nextConfig (with transpilePackages + rewrites)
```

## `package.json` scripts

```json
{
  "dev":     "TINA_PUBLIC_IS_LOCAL=true tinacms dev -c \"next dev\"",
  "build":   "tinacms build && next build",
  "preview": "opennextjs-cloudflare build && opennextjs-cloudflare preview",
  "deploy":  "opennextjs-cloudflare build && opennextjs-cloudflare deploy",
  "cf-typegen": "wrangler types --env-interface CloudflareEnv cloudflare-env.d.ts"
}
```
Deploy = `opennextjs-cloudflare build && opennextjs-cloudflare deploy` (wraps `wrangler deploy`). Add a
`.dev.vars` with `NEXTJS_ENV=development`.

## Datalayer: Upstash Redis (the whole reason CF works)

Cloudflare Workers can't open raw TCP reliably, so **MongoDB (`mongodb-level`) is a bad fit on Workers**:
no SRV DNS (`mongodb+srv://` fails — you'd need a seed-list URI), connection churn per stateless request,
Atlas connection-limit pressure. **`upstash-redis-level` uses `@upstash/redis`, a REST/HTTP client built
for edge — it runs on Workers unchanged.** So on Cloudflare, **use `--db upstash`**. Provision an Upstash
Redis DB, put its REST URL/token in `KV_REST_API_URL`/`KV_REST_API_TOKEN`. If the user demands MongoDB on
Cloudflare, warn loudly and suggest deploying to Vercel instead (or moving the Tina backend to Node).

## Media: R2 via `next-tinacms-s3`

R2 is S3-compatible — use `next-tinacms-s3` with an endpoint override:
```ts
// media handler config
endpoint: process.env.S3_ENDPOINT,            // https://<ACCOUNT_ID>.r2.cloudflarestorage.com
region: "auto",
credentials: { accessKeyId: process.env.S3_ACCESS_KEY!, secretAccessKey: process.env.S3_SECRET_KEY! },
// bucket: process.env.S3_BUCKET
```
For a simple site, `--media git` (images committed under `public/uploads`) is fine and needs none of this.
Note: R2 is used for two different things — OpenNext's incremental cache and Tina media — use **separate
buckets**.

## Gotchas

- **No edge runtime** anywhere; the Tina route stays Node.
- **Worker size**: Next + `@tinacms/datalayer` + GraphQL + auth is heavy; Workers compress-limit is ~3 MiB
  (free) / ~10 MiB (paid). Paid is usually fine — watch it.
- **`nodejs_compat` + compat date** as above, or the Tina backend throws on Node built-ins.
- The Tina backend route lives in `pages/api/` even though the app is App Router — OpenNext supports both.

## Cloudflare vs Vercel (surface this in Phase 2)

Cloudflare works but there's **no official Tina-on-Cloudflare reference** and no Tina datalayer adapter for
CF-native storage (KV/D1/R2) — you ride Upstash. **Vercel is the lower-friction Tina target**: an official
one-click `tina-self-hosted-demo`, native Node runtime, both DB adapters work, and git env vars are
auto-injected. Recommend Cloudflare when the user is already on Cloudflare (like the ProTec site) or wants
Workers/R2; recommend Vercel when they want the smoothest Tina path or need MongoDB. Both are one flag apart.
