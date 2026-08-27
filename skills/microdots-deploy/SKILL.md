---
name: microdots-deploy
description: Route a deploy of a MicroDots workspace. When the workspace ships the deploy MicroDot, the operator drives it from the deploy screen. The wrangler path is emergency-only for the host shell or a single already-built bundle, and never handles credentials.
disable-model-invocation: true
---

# Deploy

Deploying publishes publicly and creates a persistent resource on the user's
account. **Never run a deploy command without an explicit confirmation in this
conversation.**

## 0. Route the deploy

```bash
ls -d microdots/deploy micros/deploy 2>/dev/null   # does the workspace ship the deploy dot?
```

| Workspace ships a deploy MicroDot | Route                                                        |
| --------------------------------- | ------------------------------------------------------------ |
| Yes                               | **Operator path** — the deploy screen. Not this skill's job. |
| No                                | The emergency wrangler path below.                            |

**Operator path.** The deploy MicroDot owns Connect, preflight, deploy, promote,
rollback and history. Send the operator to the deploy route on the running host
(read the host URL from the `dev` output — do not guess a port) and stop there.

Do **not** `wrangler deploy` a MicroDot that the deploy screen can see. That CLI
**never builds**; the screen's `build-fresh` check exists precisely because the
CLI path ships a stale `dist/`.

## Credentials

OAuth is primary, a scoped API token is the headless fallback, and **the deploy
service holds the grant**. This skill does not.

| Do                                                              | Do not                                                       |
| --------------------------------------------------------------- | ------------------------------------------------------------ |
| Tell the operator to Connect on the deploy screen               | Paste a token into chat, an RPC payload, or a command line   |
| Point at the deploy dot's `.env.example` for the OAuth client id / API token names | Run `wrangler login` on their behalf        |
| Leave `adoptServiceToken` argument-less — the service reads its own env | Put `CLOUDFLARE_API_TOKEN` in a shell the agent runs  |

"Never handle their credentials" holds **for this skill**. The deploy service
holding an OAuth refresh token in a `0700` vault is a different process, on
loopback, fail-closed when unset. Do not collapse the two.

## Emergency: wrangler, host or one static bundle only

Use this only when the operator explicitly wants a **hand** publish of the host
shell or a single already-built bundle, and has confirmed the account.

| Argument       | Artifact                             | Directory                    |
| -------------- | ------------------------------------ | ---------------------------- |
| `host`         | host shell + copied MicroDot bundles | `apps/host/dist`             |
| `micro <name>` | one MicroDot browser bundle          | `<dot-dir>/<name>/dist`      |
| `all`          | same as `host`                       | `apps/host/dist`             |

`<dot-dir>` is `microdots/` on current workspaces, `micros/` on older ones —
resolve it, and match the bundle URL prefix the host registry actually uses.
A bundle deployed alone is a CDN artifact: any page can load it with a script
tag. The host shell is a full site that also serves the bundles.

Services that have never been deployed will `Failure` on a live HTTPS page
(mixed content). Deploy the service before, or alongside, the bundle.

```bash
bun run build          # also emits worker modules at <target>/dist-worker/index.js
bunx wrangler whoami   # wrong account → the OPERATOR runs `bunx wrangler login`
```

Then `bunx wrangler deploy` from the artifact's own package. Confirm the project
name and the public URL first.

## Worker entry invariant

A Worker **service** entry is a single call to `makeMicroDotWorker` in
`service/worker.ts`, imported from the runtime package's `/worker` entry — never
a module-scope `toWebHandler`, and never the Node `/service` entry. CORS is the
runtime's `microAppCors`, never a bare `HttpMiddleware.cors()`.

```bash
grep -rn "makeMicroDotWorker\|toWebHandler" <dot-dir>/*/service/worker.ts
```

A module-scope `toWebHandler` is the defect that makes a Worker serve one
request and then hang.

## After

Hard-reload the URL — assets propagate late. Report what the browser actually
shows, not what the CLI said.
