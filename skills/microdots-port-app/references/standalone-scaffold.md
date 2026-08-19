# Phases 0 & 7 — Target detection and the standalone scaffold

Two target modes. Monorepo mode delegates scaffolding to the repo's own
`bun run new:microdot` and wiring rules — never rebuild those here. This file
exists for **standalone mode**: bootstrapping a runnable MicroDots workspace in
an arbitrary directory from the published `@bespokeagentics/microdots-*` npm packages.

## Target detection (Phase 0)

A path is the MicroDots monorepo only when ALL THREE hold:

1. Its `package.json` `workspaces` include `microdots/*`.
2. `scripts/new-microdot.ts` exists.
3. `AGENTS.md` exists at its root.

Anything else is standalone. When the user names a directory that does not
exist yet, create it at scaffold time (Phase 7), never earlier.

## Standalone preflight (Phase 0 — before any analysis)

```
npm view @bespokeagentics/microdots-runtime version
```

All five must resolve: `@bespokeagentics/microdots-runtime`, `@bespokeagentics/microdots-element`,
`@bespokeagentics/microdots-theme`, `@bespokeagentics/microdots-host`, `@bespokeagentics/microdots-bridge`.

**The packages are private** (restricted access on the `@bespokeagentics`
org), so an E404/E403 here usually means missing auth, not a missing package:
the machine needs an npm account in the org, or a granular read token for the
scope, configured via `npm login` or an `//registry.npmjs.org/:_authToken`
line in `~/.npmrc`. The user does that themselves — never handle their token.
If access cannot be arranged, stop and say so — the packages are published
from the MicroDots monorepo (`wiki/plans/active/publish-microdots-packages.md`
there holds the pipeline); standalone mode cannot proceed without them, and
pretending otherwise wastes the whole analysis.

The packages ship **raw TypeScript source** — consumers must be Bun + Vite,
which this scaffold guarantees. This is also an asset: the installed packages
under `node_modules/@bespokeagentics/microdots-*/src/` are readable source, and they are the
runtime authority for every wiring question below. **Read the installed source
before writing wiring code** — this file gives the layout and the invariants,
never a frozen copy of an API.

## Dependency set

Pin what the packages' peer dependencies demand — `bun install` warnings are
the check, and the effect pin is exact on purpose (v4 RCs break between RCs):

| Dependency                                                             | Version                                                                                      | Why                                         |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `@bespokeagentics/microdots-runtime` `element` `theme` `host` `bridge` | `^0.1.0`                                                                                     | the framework                               |
| `effect`                                                               | exactly the peer version `@bespokeagentics/microdots-runtime` declares (e.g. `4.0.0-rc.108`) | HTTP + RPC live in core `effect/unstable/*` |
| `@effect/platform-node`                                                | same exact version as `effect`                                                               | the service entry's platform binding        |
| `@effect/platform-browser`                                             | same exact version as `effect`                                                               | browser bindings                            |
| `foldkit`                                                              | the range `@bespokeagentics/microdots-element` declares                                      | the UI layer                                |
| `vite`                                                                 | current major                                                                                | bundling; resolves the raw-TS packages      |
| `typescript`                                                           | current 5.x                                                                                  | `tsc --noEmit` is the check script          |
| `@types/node` (dev)                                                    | current                                                                                      | foldkit's msgpackr types reference `Buffer` |

Tailwind (`@tailwindcss/vite`) only if the port's styles use it — the theme
CSS from `@bespokeagentics/microdots-theme` is plain CSS and needs no build.

**tsconfig requirements, verified against the published packages** (a fresh
consumer was typechecked and vite-built with exactly these): `strict`,
`noEmit` + `allowImportingTsExtensions` (the packages' raw TS imports carry
`.ts` extensions), `moduleResolution: "bundler"`, `lib: ["esnext", "dom",
"dom.iterable"]` (effect's types use `Disposable`/`AsyncDisposable` — `es2022`
lib fails), `types: ["node"]`, plus the project's own strictness
(`exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`). A `declare module
'*.css'` declaration file covers the theme CSS imports under tsc.

## Workspace layout

```
<target>/
  package.json          # "workspaces": ["microdots/*", "host"]; scripts below
  tsconfig.json         # strict; exactOptionalPropertyTypes; noUncheckedIndexedAccess; no baseUrl
  docs/ports/<slug>/    # the dossier (already there from Phases 1–5)
  scripts/dev.ts        # spawns every service + the host's vite dev, prefixed output, Ctrl-C stops all
  host/                 # the mini-host — ALWAYS present
    package.json
    index.html          # one section + slot container per custom-element tag
    vite.config.ts
    topology.json       # THE one place routes and slots are declared
    src/main.ts         # registry + loader via @bespokeagentics/microdots-host; broker via @bespokeagentics/microdots-bridge if the composition needs it
  microdots/<name>/     # one per MicroDot in the confirmed composition
    package.json        # "microdot": { "tag": ..., "port": ... }; exports ONLY "./contract"
    src/contract.ts     # RpcGroup — the ONLY thing that leaves the directory
    src/client.ts       # RPC client, a function of the base URL
    src/app.ts          # Foldkit TEA (Model/Message/update/view/ports)
    src/element.ts      # registration via @bespokeagentics/microdots-element
    src/entry.ts        # bundle entry; importing it registers the element
    src/styles.css      # the dot's OWN stylesheet (import @bespokeagentics/microdots-theme tokens)
    service/handlers.ts # RpcGroup handlers — platform-free
    service/main.ts     # service entry via @bespokeagentics/microdots-runtime/service, own port (310N)
    service/store*.ts   # storage as a Context.Service, if stateful
    vite.config.ts      # lib build → ONE self-contained ES module per tag
```

Root `package.json` scripts: `dev` (scripts/dev.ts), `build` (every dot's
bundle, then the host), `check` (`tsc --noEmit` across the workspace, plus
tests if any were written).

## The invariants the scaffold must satisfy

These are the monorepo's breakable rules, restated only as a checklist — when
the monorepo is on disk, its `AGENTS.md` and invariant pages are the
authority:

1. **The host imports no MicroDot code.** The mini-host loads each dot's built
   bundle by URL/script tag; a value import from `microdots/*` is a bug.
2. **One route table.** `host/topology.json` is the only place a route or slot
   is declared; host code decodes it.
3. **Configuration arrives as attributes** — service base URLs included. Never
   build-time env.
4. **Each bundle is self-sufficient**, its CSS included. effect + foldkit are
   duplicated per bundle by default; independence over deduplication.
5. **Cross-dot comms are host-brokered** (`@bespokeagentics/microdots-bridge`); dots never
   reach for each other. **A poll is the floor** — a brokered nudge only ever
   accelerates a poll that already works.
6. **Mount via `@bespokeagentics/microdots-element`** — a mount container without an `id`
   renders blank with a clean console; `defineMicroDot` owns that invariant.
7. **CORS origins are registered, not improvised** — the service helpers in
   `@bespokeagentics/microdots-runtime` take the allowed origins; the mini-host's dev origin
   must be among them or every call fails as "could not reach the service".
8. **Secrets fail closed** — a dot needing a secret refuses to serve without
   it; test the unset case.
9. **Worker entries only if D-deploy chose Workers** — and then each is one
   call to `makeMicroDotWorker`. A dot whose port needs a long-lived runtime
   (streaming, child processes, an Agent SDK) gets **no Worker entry,
   deliberately** — write that into the dot's README so nobody adds one.

## Mini-host wiring

`host/src/main.ts` does four things, in this order, deriving every API detail
from the installed `@bespokeagentics/microdots-host` source (and from the monorepo's
`apps/host/src/` when it is on disk, read-only):

1. Decode `topology.json` (routes + slot manifest).
2. Build the registry: per dot — tag, bundle URL, service base URL, the
   attributes the port map defined.
3. Mount each dot into its declared slot via the loader; every slot in the
   manifest must exist in `index.html` and vice versa — a mismatch renders as
   a blank page, so check it explicitly at startup.
4. If the composition brokers anything: wire `@bespokeagentics/microdots-bridge` so the
   nudges flow — after confirming the poll-only path already works.

## Scaffold order (Phase 7)

1. Root: `package.json`, `tsconfig.json`, `bun install` — resolve the
   dependency set completely before writing any source.
2. One MicroDot directory per dot, contract-first, service on its own port
   (3101, 3102, … unless taken).
3. The mini-host: `topology.json` → `index.html` → `main.ts`.
4. `scripts/dev.ts`, then `bun run check` green **before** the implementation
   waves begin — a scaffold that does not check green is not a scaffold, it is
   debt with directories.

## Verify (standalone done bar)

The monorepo's verify skill is unavailable here; run its bar by hand:

1. `bun run check` green.
2. `bun run build` — every bundle and the host build.
3. Boot `bun run dev`; open the mini-host in a browser.
4. Confirm **every** MicroDot renders real content and polls its service —
   watch the network tab for the RPC calls. `Runtime.embed` forks the runtime
   and swallows startup defects, so a clean console proves nothing; a blank
   dot means running the program's `start` effect directly and inspecting the
   `Exit` (`cause.reasons[0].defect`).
5. Change an attribute on a mounted element and confirm the dot reacts;
   unmount/remount and confirm it survives.

Report what the browser actually showed. Built is not verified.
