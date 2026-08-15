---
name: microdots-deploy
description: Deploy a built artifact to a hosting target. Handles the host shell or an individual micro-app bundle. Cloudflare Workers static assets is the implemented target; the flow is target-agnostic so others can be added.
disable-model-invocation: true
---

Deploy `$ARGUMENTS` (e.g. `host`, `micro price`, `all`). This publishes
publicly and creates a persistent resource on the user's account — never run the
deploy command without an explicit confirmation in this conversation.

## 1. Decide the artifact

| Argument       | Artifact                                   | Directory            |
| -------------- | ------------------------------------------ | -------------------- |
| `host`         | host shell + every micro-app bundle        | `apps/host/dist`     |
| `micro <name>` | one micro-app bundle only                  | `micros/<name>/dist` |
| `all`          | host shell (already contains every bundle) | `apps/host/dist`     |

A micro-app bundle deployed alone is a CDN artifact: a page anywhere can load it
with a script tag. The host shell is a full site that also serves the bundles
under `/micros`.

## 2. Check the API URLs resolve

`apps/host/src/registry.ts` picks each `apiUrl` **at runtime** by hostname:
localhost during `bun run dev`, the deployed Worker URL everywhere else. One
build works in both places, so there is nothing to edit before building.

What still needs checking: every micro-app in the registry has a real deployed
URL for its non-local branch. A deployed HTTPS page **cannot** call
`http://localhost` — browsers block it as mixed content — so a micro-app whose
service has never been deployed will render its `Failure` state.

If a service is missing, deploy it first (step 4b) and add its URL to the
registry. Never ship a host with a localhost fallback and call the deploy a
success.

## 3. Build

```bash
bun run build
```

Produces `apps/host/dist` (`index.html`, `assets/`, `micros/*.js`) and each
`micros/*/dist/<tag>.js`. Confirm the build succeeded before continuing.

## 4. Target: Cloudflare Workers (static assets)

Pre-flight:

```bash
bunx wrangler whoami
```

Confirm the account is the one intended. If not authenticated, ask the user to
run `bunx wrangler login` themselves — never handle their credentials.

Config lives next to the artifact as `wrangler.jsonc`:

```jsonc
{
  "name": "<project-name>",
  "compatibility_date": "<today>",
  "assets": { "directory": "./dist" },
}
```

With `assets` and no `main`, this is a static-assets-only Worker — no server
code, served from Cloudflare's edge.

**Confirm with the user before deploying**: the project name, the resulting
`https://<name>.<subdomain>.workers.dev` URL, and that it will be publicly
reachable. Wait for a clear yes.

```bash
cd <artifact-dir>/.. && bunx wrangler deploy
```

**`compatibility_date` must not exceed what the local runtime supports.** Set it
past that and `wrangler dev` refuses to boot with "newest date supported by this
server binary is ...". Deploy does not check, so a too-new date ships fine and
only breaks local dev. Use a date the installed wrangler accepts.

## 4b. Target: Cloudflare Workers (Effect RPC service)

A micro-app's service deploys as a Worker with no platform package at all.
`@effect/platform-node` does not run there — `NodeHttpServer` and `node:http` do
not exist.

Each micro-app splits its service into three files:

- `service/handlers.ts` — the `RpcAppLayer` (group + handlers + serialization).
  Shared. **Must not import a platform package.**
- `service/main.ts` — node/Bun entry via `@kit/effect/service`, for local dev.
- `service/worker.ts` — the Cloudflare entry:

```ts
const { handler } = HttpRouter.toWebHandler(RpcAppLayer, {
  middleware: HttpMiddleware.cors(),
});
export default { fetch: (request: Request) => handler(request) };
```

`HttpRouter.toWebHandler` takes the Layer directly and returns a standard
`(Request) => Promise<Response>`.

**Worker isolates are recycled between requests**, so a `Ref` holding counter
state resets to zero and any value derived from it never changes. Derive from
`Clock.currentTimeMillis` instead — it behaves identically under node and
Workers.

`wrangler.jsonc` uses `main` (not `assets`) plus
`"compatibility_flags": ["nodejs_compat"]`, which Effect's internals need.

### CORS on a browser-facing RPC service

Use `microAppCors` from `@kit/effect`, never bare `HttpMiddleware.cors()`. Three
separate things bite here, and each produces a misleading browser error:

1. **Bare `cors()` emits an empty `access-control-allow-headers:` value**
   (`allowedHeaders` defaults to `[]`). Chrome flags it as a malformed CORS
   response and then reports the request as having **no**
   `Access-Control-Allow-Origin` — sending you after the wrong header entirely.
2. **The RPC client sends `traceparent` and `b3`**, not just `content-type`.
   Miss them and the preflight fails with "Request header field traceparent is
   not allowed by Access-Control-Allow-Headers". These only appear once tracing
   is active, so a config can pass locally and fail deployed.
3. **Pass exactly ONE origin.** Effect's cors emits a constant allow-origin
   header for a single origin but switches to a per-request predicate branch for
   two or more. The multi-origin branch did not work in the browser here: curl
   showed a perfect preflight while the actual POST was rejected. A Worker only
   needs the deployed host origin anyway.

Diagnose with the browser, not curl — curl reported correct headers throughout
while the browser refused every POST. `fetch(url, { mode: 'no-cors' })` and a
plain cross-origin `GET` are useful probes: if `GET` returns `type: "cors"` but
`POST` fails, the preflight is the problem, not connectivity.

**A deploy can silently not take effect.** Two `wrangler deploy` runs reported
success while the Worker kept serving older code, and two services with
byte-identical sources behaved differently. Confirm with
`bunx wrangler deployments list` that a new version exists, and redeploy if the
newest timestamp predates your change.

Test locally before deploying — `bunx wrangler dev --port 8787`, then exercise it
through the micro-app's own RPC client rather than hand-rolling the NDJSON
protocol with curl:

```ts
Effect.provide(makeXClientLive("http://localhost:8787"));
```

Confirm CORS too: `curl -i -X OPTIONS localhost:8787/rpc -H "Origin: <host>"`.

## 5. Verify the deployment

**Assets propagate slightly after the CLI reports success.** Loading the URL
immediately can 404 on files that curl fetches fine seconds later — which looks
exactly like a broken deploy. Before diagnosing anything, hard-reload once. If a
bundle 404s in the browser but `curl -o /dev/null -w '%{http_code}'` returns 200,
it is propagation, not a bug.

Do not trust the CLI's success line alone. Load the deployed URL in a browser and
check:

- the page renders
- for a host deploy: each micro-app bundle actually fetched from `/micros/*.js`
  and registered its custom element
- what state the micro-apps settled into, and whether that matches what step 2
  predicted

Report the real observed state. If the micro-apps are showing `Failure` because
the services are local-only, say that explicitly.

## 6. Report

Give the URL, what was deployed, and what genuinely works at that URL versus what
still needs the services deployed.

## Adding a target

Keep steps 1–3 and 5–6 as-is; they are target-agnostic. Add a sibling to step 4
with that provider's pre-flight, config file, confirmation and deploy command.
Anything requiring the user's credentials stays with the user.

Note for a future Cloudflare Workers _service_ target: `@effect/platform-node`
does not run on Workers. An Effect service would need the fetch-based handler
instead of `NodeHttpServer`, with `main` pointing at a Worker entry rather than
using assets-only config.
