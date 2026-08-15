# Effect micro-apps — agent contract (fixture edition)

A micro-app ships as one self-contained ES module that registers a custom
element. A host page loads it with a script tag and configures it with
attributes — no framework, no build step, no shared runtime. Each micro-app
owns its contract, its Effect RPC service, its Foldkit runtime and its RPC
client. It exposes attributes going in and DOM events coming out — that is the
entire public surface.

## Layout contract

A micro-app is `micros/<name>/` containing: `src/contract.ts` (RpcGroup +
Effect Schema types — the only thing shared across the wire), `src/client.ts`
(a function of `baseUrl`), `src/app.ts` (the Foldkit program: Model, Message,
update, view, subscriptions), `src/element.ts` (`defineMicroApp` — attributes
in, CustomEvents out), `src/entry.ts`, `src/styles.css`, `service/handlers.ts`
(`RpcAppLayer` — no platform imports), `service/main.ts` (Bun/dev entry),
`service/worker.ts` (Cloudflare entry), plus `package.json`, `vite.config.ts`,
`wrangler.jsonc`.

## Hard rules

- **A micro-app owns its whole stack.** Nothing outside its directory may
  import anything but its `contract`, types only.
- **The host imports no micro-app code.** A value import is a bug.
- **Configuration arrives as attributes, never build-time env.** An arbitrary
  host must be able to point a micro-app at its own backend, so
  `makeXClientLive` is a function of `baseUrl`.
- **Cross-micro-app communication is brokered by the host.** Outbound port →
  `CustomEvent` → host listener → attribute on the other micro-app.
- **`service/handlers.ts` may not import any platform package.** Storage,
  secrets, credentials become a `Context.Service`; each entry provides its own
  layer.
- **No in-memory state in a Workers service.** Isolates recycle between
  requests; derive from `Clock` or persist through the store seam.
- **Auth is a per-call gate, never a session.** `SecretGate` from
  `@kit/effect/secret`, fail-closed: unset or blank secret rejects everything.
- **Semantic tokens only.** Palette literals (`bg-white`, hex) are banned;
  `@kit/theme` tokens keep dark mode working. Never import
  `@kit/theme/page.css` into a micro.
- **Before building a feature some micro-app already has, consult
  `docs/reuse-catalog.md`.**
- **Done means verified in a browser.** `Runtime.embed` forks the runtime, so
  a startup defect is a blank micro-app with a clean console. Green static
  checks are not done.

## Trap table (excerpt)

| Trap | Consequence | Rule |
|---|---|---|
| Mount container without an `id` | Blank micro-app, clean console | Everything mounts through `@kit/element`'s `mountPoint` |
| `@kit/effect/service` imported browser-side | Bundle grows by hundreds of kB; may break on Workers | Browser code imports `@kit/effect` only |
| `Ref`-held counter state on Workers | Value resets every request, "never changes" | Derive from `Clock.currentTimeMillis` or persist |
| Bare `HttpMiddleware.cors()` on a service | Browser reports missing allow-origin, misleading | Use `microAppCors` from `@kit/effect` |
| Reading `container.innerHTML` to verify render | Always looks empty — embed replaces the node | Assert against the parent or `document.body` |
| Boolean-flag Model states | Impossible states representable, blank-on-poll | Discriminated unions; AsyncData with Refreshing |
