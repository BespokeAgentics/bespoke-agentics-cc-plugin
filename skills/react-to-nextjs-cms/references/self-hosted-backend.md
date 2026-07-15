# Self-hosted TinaCMS backend (database, route, auth, env)

The backend wiring shared by both deploy targets. Verified against `github.com/tinacms/tina-self-hosted-demo`.
Package majors (mid-2026): `tinacms` v3 · `@tinacms/cli` v2 · `@tinacms/datalayer` v2 · `tinacms-authjs` v24 ·
`tinacms-gitprovider-github` v4 · `next-auth` v4 (NOT v5) · `upstash-redis-level` v1 · `mongodb-level` v0.
Pin the tested set (see `assets/templates/package.*.json`) rather than `@latest`.

## The four modules

Self-hosted Tina is: a **git provider** (source of truth — GitHub), a **database adapter** (an index/cache
over the content — Upstash Redis or MongoDB), an **auth provider** (Auth.js by default), and the
**datalayer** glue (`@tinacms/datalayer`). The DB is *not* the source of truth — content is the Markdown/JSON
in Git.

## `tina/database.ts`

`createLocalDatabase()` for local dev/static builds; `createDatabase({ gitProvider, databaseAdapter })` in
prod. The `TINA_PUBLIC_IS_LOCAL` flag switches them.

```ts
import { createDatabase, createLocalDatabase } from "@tinacms/datalayer";
import { RedisLevel } from "upstash-redis-level";
import { GitHubProvider } from "tinacms-gitprovider-github";

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === "true";
const token  = process.env.GITHUB_PERSONAL_ACCESS_TOKEN as string;
const owner  = (process.env.GITHUB_OWNER  || process.env.VERCEL_GIT_REPO_OWNER) as string;
const repo   = (process.env.GITHUB_REPO   || process.env.VERCEL_GIT_REPO_SLUG) as string;
const branch = (process.env.GITHUB_BRANCH || process.env.VERCEL_GIT_COMMIT_REF || "main") as string;

if (!branch) throw new Error("No branch: set GITHUB_BRANCH or VERCEL_GIT_COMMIT_REF.");

export default isLocal
  ? createLocalDatabase()
  : createDatabase({
      gitProvider: new GitHubProvider({ branch, owner, repo, token }),
      databaseAdapter: new RedisLevel<string, Record<string, unknown>>({
        redis: {
          url:   (process.env.KV_REST_API_URL as string)   || "http://localhost:8079",
          token: (process.env.KV_REST_API_TOKEN as string) || "example_token",
        },
        debug: process.env.DEBUG === "true",
      }),
      namespace: branch,          // per-branch content isolation (top-level option)
    });
```

**MongoDB variant** (`--db mongodb`, Vercel/Node only — see `deploy-cloudflare.md` for why not Workers):
```ts
import { MongodbLevel } from "mongodb-level";
// …
databaseAdapter: new MongodbLevel<string, Record<string, any>>({
  collectionName: `tinacms-${branch}`,   // per-branch isolation via collection name
  dbName: "tinacms",
  mongoUri: process.env.MONGODB_URI as string,
}),
// (drop the top-level `namespace` when using Mongo)
```

## The backend route — `pages/api/tina/[...routes].ts`

**This is a Pages-Router file even in an App-Router app.** Tina's `TinaNodeBackend` returns a Node
`(req, res)` handler, not an App-Router `Request→Response` route — there is no official
`app/api/tina/[...routes]/route.ts`. `pages/api/*` and `app/*` coexist fine in one Next.js project; both
deploy targets support it. This single catch-all serves the GraphQL content API (`/api/tina/gql`) and the
auth endpoints (`/api/tina/auth/*`).

```ts
import { TinaNodeBackend, LocalBackendAuthProvider } from "@tinacms/datalayer";
import { TinaAuthJSOptions, AuthJsBackendAuthProvider } from "tinacms-authjs";
import databaseClient from "../../../tina/__generated__/databaseClient";

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === "true";

const handler = TinaNodeBackend({
  authProvider: isLocal
    ? LocalBackendAuthProvider()
    : AuthJsBackendAuthProvider({
        authOptions: TinaAuthJSOptions({ databaseClient, secret: process.env.NEXTAUTH_SECRET as string }),
      }),
  databaseClient,
});

export default (req: any, res: any) => handler(req, res);
```

- **Never** add `export const runtime = "edge"` here (Node handler; needs `nodejs_compat` on Cloudflare).
- Note the current API is `authProvider:` + `LocalBackendAuthProvider` / `AuthJsBackendAuthProvider`. Some
  tina.io doc pages still show the older `authentication:` + `*Authentication()` names — **use the
  `AuthProvider` form** (it's what the runnable demo uses).

## `next.config.mjs`

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["tinacms", "tinacms-authjs", "@tinacms/datalayer", "tinacms-gitprovider-github"],
  async rewrites() {
    return [{ source: "/admin", destination: "/admin/index.html" }];
  },
};
export default nextConfig;
```

**`transpilePackages` for those four is mandatory** — they ship untranspiled and Next will fail to compile
without it. This is the single most common self-hosted breakage.

## Auth & the seed user

Prod auth is username/password via Auth.js; users are stored as content in the DB, seeded from
`content/users/index.json`:
```json
{ "users": [ { "name": "Admin", "email": "admin@yourco.com", "username": "admin",
  "password": { "value": "changeme123", "passwordChangeRequired": true } } ] }
```
Tell the client to log in at `/admin` with these and change the password immediately (`passwordChangeRequired`
forces it). `NEXTAUTH_SECRET` signs the JWTs.

## Environment variables

| Var | Purpose |
|---|---|
| `TINA_PUBLIC_IS_LOCAL` | `"true"` locally → local DB + local auth; `"false"`/unset in prod. `TINA_PUBLIC_*` is browser-exposed. |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | token the backend commits content with (repo Contents: read/write) |
| `GITHUB_OWNER` / `GITHUB_REPO` / `GITHUB_BRANCH` | content repo coords (Vercel auto-fills via `VERCEL_GIT_*`) |
| `NEXTAUTH_SECRET` | Auth.js JWT secret (`openssl rand -hex 16`) |
| `KV_REST_API_URL` / `KV_REST_API_TOKEN` | Upstash Redis creds (`--db upstash`) |
| `MONGODB_URI` | Mongo connection string (`--db mongodb`) |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `S3_BUCKET` / `S3_ENDPOINT` / `S3_REGION` | external media (`--media r2|s3`) |

Cloud-only vars (`NEXT_PUBLIC_TINA_CLIENT_ID`, `TINA_TOKEN`, `NEXT_PUBLIC_TINA_BRANCH`) must be **absent**
for self-hosted — their presence flips Tina toward Cloud mode.

## Scripts & local flow

```json
"scripts": {
  "dev":   "TINA_PUBLIC_IS_LOCAL=true tinacms dev -c \"next dev\"",
  "build": "tinacms build && next build",
  "start": "next start"
}
```
`tinacms dev` generates the typed client into `tina/__generated__/`, runs a local content server, and
spawns `next dev`. Locally you need no GitHub/Redis/secret — `createLocalDatabase()` + `LocalAuthProvider`
handle it and `/admin` auth is bypassed. `tina/__generated__/` is gitignored (via `tina/.gitignore`
containing `__generated__`); `tina/tina-lock.json` is committed; `public/admin/` is a build artifact
(gitignored).

## What self-hosted does NOT give you (state these in hand-off)

- **No search** — the self-hosted backend has no search endpoints (Tina Cloud does).
- **Branch switching is build-time only** — no runtime branch switch in the editor.
- **No managed media CDN / Media Manager** — use static git media (`public/`) or wire S3/R2 yourself.
- **No editorial workflow** (protected-branch PR review) — that's a Cloud/Enterprise feature.
- **You own ops** — the DB adapter, GitHub token, auth secret, reindexing, scaling.
