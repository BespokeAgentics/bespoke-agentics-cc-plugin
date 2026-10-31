# Phases 0 & 7 — Target detection and the standalone scaffold

Two target modes. Monorepo mode delegates scaffolding to
`microdots-new-micro`'s repository-extension mode — never rebuild it here. This file
exists for **standalone mode**: a runnable MicroDots workspace in an arbitrary
directory, built on the public `@bespokeagentics/*` npm packages.

**The generator builds the standalone workspace. Never hand-write it.**
`@bespokeagentics/create-microdots-host` writes the root `package.json` (exact
framework pins, the template's own devDependency ranges, and `overrides`),
`tsconfig.json`, the vite configs, the dev and build
scripts, a topology-driven host and two worked MicroDots. This file covers how to
run it, what to keep exactly as generated, what it leaves to you, and the
invariants the finished port must hold. The public quickstart covers the same
first run: https://microdots.cloud/docs/quickstart. If that page does not load,
the site has not launched yet, and the generator's npm README has the same steps.

## Target detection (Phase 0)

A path is the MicroDots monorepo only when ALL THREE hold:

1. Its `package.json` `workspaces` include `microdots/*`.
2. `scripts/new-microdot.ts` exists.
3. `AGENTS.md` exists at its root.

Anything else is standalone. When the user names a directory that does not
exist yet, nothing but the dossier (`docs/ports/<slug>/`) is written there
before Phase 7.

## Standalone preflight (Phase 0 — before any analysis)

```bash
bun --version
npm view @bespokeagentics/create-microdots-host version
ls -A <target> 2>/dev/null   # must print nothing, or only `docs`
```

- **The target must be absent, empty, or hold only `docs/`.** The generator
  refuses any other directory at Phase 7 (`target directory is not empty`), and
  it counts dotfiles, so a `.git` or `.DS_Store` is enough to refuse. Check now:
  Phase 1 writes the dossier into the target, so a refusal found at Phase 7
  strands a finished analysis in the wrong place. If `ls -A` prints anything
  but `docs`, ask the user for another directory before Phase 1. Never delete
  or move their files to make room.
- **Bun is required.** The generator's bin is a TypeScript file run by Bun, and
  the generated workspace's scripts are Bun scripts. No Bun means stop and say so.
- **The packages are public.** No npm account, token or org membership is
  needed. An `E404` or a timeout here is a registry, proxy or network problem,
  or a `.npmrc` that sends the `@bespokeagentics` scope to another registry. It
  is never a permissions problem. Report the exact error and stop. Never ask
  for a token.

## Scaffold (Phase 7, step one): run the generator

```bash
bunx @bespokeagentics/create-microdots-host <dir> --css <plain|tailwind> --yes
```

- **Leave the command unversioned.** It resolves npm's `latest` tag, and the
  generator's templates are the one source of the version set. Do not pin a
  version here, and do not copy versions from this skill into the workspace.
- **`--css plain`** unless the port's styles are Tailwind. `tailwind` adds
  `tailwindcss` and `@tailwindcss/vite`. `--yes` keeps the run non-interactive.
- **It runs `bun install` itself.** `--no-install` skips that step.
  `--help` prints the current flags. Trust `--help` over this file if they
  disagree.
- **The target must be empty or absent.** Otherwise it exits 1 with
  `target directory is not empty: <path>` and writes nothing. The Phase 0
  preflight admitted only an absent, empty or `docs/`-only target. If it holds
  only `docs/` (the dossier from Phases 1–5), move `<target>/docs/` to a
  temporary sibling directory, run the generator, then move `docs/` back. The
  template writes no `docs/`, so nothing collides. If anything else has
  appeared since Phase 0, stop and ask the user. Never delete their files, and
  move nothing but `docs/`, which goes straight back.

Before writing any port code, run `bun run check` and `bun run build` and make
sure both are green. Then run `bun run dev` and confirm the two worked dots
render at `http://localhost:5190`. That proves the toolchain before the port
adds anything that could be blamed.

What you get (the generated `README.md` is the authority on details):

```
<target>/
  package.json  tsconfig.json  types.d.ts  vitest.config.ts   # keep as generated
  scripts/      # dev.ts, build.ts, discover.ts (the registry, read from each dot's package.json), check-tokens.ts, …
  host/         # topology.json (routes, placements, slots, wires), index.html, src/main.ts, vite config on :5190
  microdots/scope-picker/  microdots/pulse/                    # worked dots; services on :3201 and :3202
```

## Keep the generated `package.json` verbatim

Its `dependencies` and `overrides` are exact pins that move together, as is the
`@bespokeagentics/microdots-vite-plugin` devDependency. The other
devDependencies (`typescript`, `vite`, `vitest`, `oxlint`, the `@types/*`,
`happy-dom`, and Tailwind's two) are the template's own caret ranges. Keep both
as generated. Add the port's own dependencies. Never re-pin, upgrade, widen,
narrow or "tidy" the generated ones. A new
`@effect/*` package gets an exact version whose `peerDependencies` accept the
pinned `effect` (usually the same RC), never a range.

**Keep the `overrides` block.** It pins `@effect/platform-node-shared`, a
transitive dependency of `@effect/platform-node`, to a build that works with the
pinned `effect`. Without it, bun resolves the newest
`@effect/platform-node-shared`, which is built against a later `effect`.
`bun install`, `bun run check` and `bun run build` all stay green. Only booting
a service fails:

```text
error: Cannot find module 'effect/<module>' from '…/node_modules/@effect/platform-node-shared/dist/<File>.js'
```

The missing module changes from release to release (reproduced 2026-10-30:
`effect/process/ChildProcess` from `NodeChildProcessSpawner.js`), but the
message keeps this shape. When you see it, restore `overrides` from the
generator's template. Do not chase the missing module.

Also keep `@types/bun` in `devDependencies` and
`"types": ["bun", "node", "vite/client"]` in `tsconfig.json`. A store on
`bun:sqlite` typechecks only because of them.

The packages ship **raw TypeScript source**, so consumers must be Bun + Vite,
which the generator guarantees. This is also an asset: the installed source
under `node_modules/@bespokeagentics/*/src/` is readable, and it is the
authority on every wiring question. **Read the installed source before writing
wiring code.** This file states the invariants. It never freezes a copy of an
API.

## Add the port's MicroDots

The generated README's "Add or rename a MicroDot" section is the procedure. For
each dot in the confirmed composition:

1. Copy a worked dot to `microdots/<name>/`. Use `pulse` for a dot that polls
   its service and shows a readout, and `scope-picker` for a dot that emits an
   event.
2. In its `package.json`, set `name`, `microdot.tags`, `microdot.port` and
   `microdot.bundle`. Discovery fails loudly on a duplicate tag, port or bundle.
   Keep `exports` holding only `./contract` (invariant 10 below).
3. In `src/surface.ts`, set `tag` to the same value as `microdot.tags`. The
   worked dot hard-codes its own (`tag: 'starter-pulse'`). `bun run build`
   fails on a mismatch (`[manifest] … surface tags … do not match package.json
microdot.tags`), and under `bun run dev`, where the manifest plugin only
   warns, both bundles define the same element. For clarity, rename the
   contract's RPC group and RPCs too (`PulseRpcs`, `GetHeartbeat`).
4. In `service/main.ts`, set the same port and `allowedOrigins` (see CORS
   below). Both are literals there; the README's steps do not mention them.
5. In `host/topology.json`, add a placement (a route mount), its slot in
   `slotManifest.slots`, and any wire.

Do not add a registry, host HTML or process-list edit. Discovery and the
topology cover them. Remove an unused worked dot completely: its directory, its
mounts, its slots and its wires. The host throws at startup on a registered tag
that no route mounts, and on a declared slot that nothing uses. The `/reports`
and `/settings` routes mount tags that no dot registers yet, and they render a
"Routed, not built" placeholder. Replace or remove them.

**Rewrite `host/src/topology.test.ts` with the topology.** Its test
`declares the direct scope-to-pulse wire` describes the worked dots: it asserts
exactly one wire, a `direct` transform of a `string` field, and that both ends
are registered tags. Adding a wire, or removing `pulse` or `scope-picker`,
turns `bun run check` red. Replace that test with assertions about the port's
own wires. The file's other tests are generic; keep them.

## CORS

**A Bun service (`service/main.ts`, `makeRpcService`).** Each generated service
passes an explicit `allowedOrigins` to `makeRpcService`. The list holds the
host's `http://localhost:5190` and `http://127.0.0.1:5190`. **An explicit list
replaces the runtime's default `MICRODOT_ORIGINS`. It does not extend it**
(`allowedOrigins ?? MICRODOT_ORIGINS` in the runtime's `src/service.ts`), and
the default does not include `:5190`. Every origin that loads a bundle goes in
every service's list. A local origin (another dev port, a preview) needs both
spellings, `localhost` and `127.0.0.1`. A deployed `https` origin has only one.
When an origin is missing, the preflight still answers 204 but carries no
`access-control-allow-origin`, and the dot reports that it could not reach the
service. It looks like a dead backend, not a CORS miss.

**A Worker entry (`service/worker.ts`, `makeMicroDotWorker`).** It takes no
`allowedOrigins` and never reads `MICRODOT_ORIGINS`. It reads the
comma-separated `MICRODOT_ALLOWED_ORIGINS` binding (a `vars` entry in the
Worker's wrangler config), else the `fallbackOrigins` option passed to
`makeMicroDotWorker`. **With neither, it answers no cross-origin request at
all** (`readAllowedOrigins(env)` falling back to `options.fallbackOrigins ?? []`
in the runtime's `src/worker.ts`). Every Worker entry needs the deployed host's
origin in one of the two.

## What the generator does not do

- **Port anything.** The worked dots are examples to replace. The dossier, the
  composition, the contracts, the services and the TEA apps are still Phases
  1–7's work.
- **Persist.** Pulse's counter lives in memory. A store seam (`bun:sqlite`, D1)
  is yours to add.
- **Deploy.** The generated dots have no `service/worker.ts` and no wrangler
  config. If D-deploy chose Workers, each Worker entry is one call to
  `makeMicroDotWorker` from `@bespokeagentics/microdots-runtime/worker`, with
  `fallbackOrigins` or the `MICRODOT_ALLOWED_ORIGINS` binding set. Without
  either it denies every origin (see CORS).
- **Add origins, ports, secrets or auth gates** beyond its own two dots on
  `:5190`.
- **Touch an existing workspace.** It refuses a non-empty directory, never
  upgrades a workspace it made, and runs no `git init`.
- **Verify in a browser.** A green `bun run check` proves nothing about
  rendering.

## The invariants the scaffold must satisfy

These are the monorepo's breakable rules, restated only as a checklist. When
the monorepo is on disk, its `AGENTS.md` and invariant pages are the authority.
The generated host and worked dots already satisfy 1, 2, 6 and 10. A dot copied
from a worked dot keeps 6 and 10. Keep it that way.

1. **The host imports no MicroDot code.** The host loads each dot's built
   bundle by URL (discovery builds the registry). A value import from
   `microdots/*` is a bug.
2. **One route table.** `host/topology.json` is the only place a route, slot or
   wire is declared. Host code decodes it.
3. **Configuration arrives as attributes**, service base URLs included. Never
   build-time env.
4. **Each bundle is self-sufficient**, its CSS included. effect + foldkit are
   duplicated per bundle by default. Independence beats deduplication.
5. **Cross-dot comms are host-brokered.** In a generated workspace that means a
   `wires` entry in `host/topology.json`. Dots never reach for each other.
   **A poll is the floor**: a brokered nudge only ever speeds up a poll that
   already works.
6. **Mount via `@bespokeagentics/microdots-element`.** A mount container
   without an `id` renders blank with a clean console. `defineMicroDot` owns
   that invariant.
7. **CORS origins are registered, not improvised.** See CORS above.
8. **Secrets fail closed.** A dot needing a secret refuses to serve without it.
   Test the unset case.
9. **Worker entries only if D-deploy chose Workers**, and then each is one call
   to `makeMicroDotWorker`. A dot whose port needs a long-lived runtime
   (streaming, child processes, an Agent SDK) gets **no Worker entry,
   deliberately**. Write that into the dot's README so nobody adds one.
10. **A MicroDot owns its whole stack; only its contract leaves the
    directory.** Its `package.json` `exports` holds only `./contract`
    (`src/contract.ts`). Nothing outside `microdots/<name>/` imports its app,
    service or store.

## Scaffold order (Phase 7)

1. Run the generator (above). Run `bun run check` and `bun run build`, and
   confirm both worked dots render.
2. Add one directory per MicroDot in the confirmed composition, contract first,
   copied from a worked dot (all five steps under "Add the port's MicroDots").
3. Update `host/topology.json` (placements, slots and wires), rewrite the wire
   test in `host/src/topology.test.ts` to match, and remove the worked dots the
   port does not use.
4. `bun run check` must be green **before** the implementation waves begin. A
   scaffold that does not check green is not a scaffold. It is debt with
   directories.

## Verify (standalone done bar)

Run `microdots-verify` (read `${CLAUDE_PLUGIN_ROOT}/skills/microdots-verify/SKILL.md`
and follow it). It handles standalone layouts too. The bar is:

1. `bun run check` green.
2. `bun run build`: every bundle and the host build.
3. Boot `bun run dev` and open the host (`http://localhost:5190`, or the URL
   the `dev` output prints).
4. Confirm **every** MicroDot renders real content and polls its service.
   Watch the network tab for the RPC calls. `Runtime.embed` forks the runtime
   and swallows startup defects, so a clean console proves nothing. For a blank
   dot, run the program's `start` effect directly and inspect the `Exit`
   (`cause.reasons[0].defect`).
5. Change an attribute on a mounted element and confirm the dot reacts.
   Unmount and remount it and confirm it survives.

Report what the browser actually showed. Built is not verified.

## Appendix: only if the generator fails

Do not hand-roll the workspace from memory. A hand-written dependency set is
how this skill's earlier versions came to ship stale pins and no `overrides`.
Instead:

1. Report the generator's exact error. That error is the defect to fix.
2. If the user still wants to go on, reproduce what the generator does, from
   its own templates:

   ```bash
   npm pack @bespokeagentics/create-microdots-host   # in a scratch directory
   tar -xzf bespokeagentics-create-microdots-host-*.tgz
   ```

   Copy `package/templates/base/` into the empty target, then copy
   `package/templates/<plain|tailwind>/` over it. Rename `_gitignore` to
   `.gitignore` and each `*.template.ts` to `*.ts`. In every file, replace
   `__PROJECT_NAME__` with the target's lower-kebab directory name and
   `__CSS_MODE__` with the CSS mode. Then run `bun install`. These are the
   steps of `scaffold()` in the package's `src/index.ts`. Read that function
   first in case they have changed.
