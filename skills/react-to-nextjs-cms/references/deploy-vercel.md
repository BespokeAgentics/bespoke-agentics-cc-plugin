# Deploy target: Vercel (native Next.js)

The lower-friction self-hosted Tina target. Next.js runs natively (Node serverless), so `TinaNodeBackend`
and **either** datalayer work with no adapter or compatibility flags. Verified against
`github.com/tinacms/tina-self-hosted-demo` + tina.io/docs/self-hosted/starters/nextjs-vercel (mid-2026).

## Why Vercel is smoother than Cloudflare

- Official one-click reference: `tinacms/tina-self-hosted-demo` (Deploy-with-Vercel button).
- **Native Node runtime** — the Tina backend `(req,res)` handler and the MongoDB driver both "just run"; no
  `nodejs_compat`, no OpenNext build step, no `wrangler.jsonc`.
- Vercel **auto-injects git env vars** (`VERCEL_GIT_REPO_OWNER`/`_SLUG`/`COMMIT_REF`) — `tina/database.ts`
  already falls back to them, so you often only set the token + secret + datalayer creds.

## No adapter, minimal config

`package.json` scripts:
```json
{ "dev": "TINA_PUBLIC_IS_LOCAL=true tinacms dev -c \"next dev\"",
  "build": "tinacms build && next build",
  "start": "next start" }
```
`next.config.mjs` is just the `transpilePackages` + `/admin` rewrite from `self-hosted-backend.md` — no
OpenNext hook. The Tina backend route (`pages/api/tina/[...routes].ts`) is unchanged and needs no
`vercel.json` (Next.js API catch-all routes work natively; the standalone-function variant with a
`vercel.json` rewrite is only for non-Next deployments).

## Datalayer: Upstash Redis or MongoDB Atlas

Both work on Vercel — this is the platform's advantage.

- **`--db upstash`** (default): **Vercel KV was discontinued (Dec 2024)** and migrated to Upstash. Provision
  **Upstash for Redis via the Vercel Marketplace** (Storage → Marketplace → Upstash), which injects
  `KV_REST_API_URL` + `KV_REST_API_TOKEN` — exactly what `upstash-redis-level` reads. **Do not tell the user
  to "create a Vercel KV store"** — that product is gone.
- **`--db mongodb`**: set `MONGODB_URI` to an Atlas connection string (`mongodb+srv://` is fine on Node).
  Use the `MongodbLevel` variant in `tina/database.ts` (see `self-hosted-backend.md`). Choose this when the
  user prefers document storage; it's a first-class option on Vercel and the reason someone might pick Vercel
  over Cloudflare.

## Media: S3 or R2 via `next-tinacms-s3`

Standard S3 (or any S3-compatible endpoint incl. R2) through `next-tinacms-s3`; env `S3_ACCESS_KEY`,
`S3_SECRET_KEY`, `S3_BUCKET`, `S3_ENDPOINT`, `S3_REGION`. For a simple site `--media git` (images under
`public/uploads`, committed) is fine.

## Deploy flow

1. Push the app to a GitHub repo (Tina commits content there via the GitHub provider).
2. Create a Vercel project from it.
3. Storage → Marketplace → **Upstash for Redis** (or set `MONGODB_URI`).
4. Set env: `GITHUB_PERSONAL_ACCESS_TOKEN`, `NEXTAUTH_SECRET` (owner/repo/branch auto-fill from Vercel git).
   Set `TINA_PUBLIC_IS_LOCAL=false` (or leave unset) in prod.
5. Deploy → visit `/admin`, log in with the seed user, change the password.

## Gotchas

- **Vercel KV is gone** — always say "Upstash via Marketplace," never "Vercel KV."
- Keep the Tina backend route on the default Node runtime (don't force edge).
- `transpilePackages` is still required (same four packages).
- The same self-hosted caveats apply (no search, build-time branch, media strategy) — see
  `self-hosted-backend.md`.
