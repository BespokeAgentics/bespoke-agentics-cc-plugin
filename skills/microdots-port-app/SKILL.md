---
name: microdots-port-app
description: >
  Analyze an entire existing application, interview to settle its shape, then fully port it to the
  MicroDots framework (Effect v4 + Foldkit custom elements). Use whenever someone says "port this
  app to MicroDots", "convert <app> into a MicroDot", "microdotize <app>", "turn this whole app
  into MicroDots", or points at an app directory that should become one or more independently
  built, independently deployed MicroDots. The port is a re-expression, not a copy: parallel
  agents trace the whole app (routes, components, state, schemas, server endpoints, persistence,
  auth, composition seams — file:line cited), a Claude-in-Chrome walk inventories the real UX, a
  composition proposal (how many MicroDots, which tags, what the host brokers) is confirmed by the
  user before any per-dot design, an Effect-optimization register maps every source idiom (React
  state, zod, fetch, express handlers, env, polling) to its target idiom, and a plugin-local port
  memory makes each similar port more deterministic than the last. Lands in either the MicroDots
  monorepo (new:microdot scaffold, host wiring, the repo's own verify) or ANY directory as a
  standalone runnable workspace built on the published @microdots npm packages with a mini-host
  always included. A seeded spec drives a spec-elicitation interview; execution is gated, wave-by-
  wave green, browser-verified. Deploy is never run; the source app is never modified; nothing is
  committed. Distinct from micros-port-feature (extracts ONE feature into the older micros
  workspace): this ports a WHOLE app into the MicroDots framework, anywhere.
argument-hint: "<app-path> [--target <path>] [--app <url>] [--mode full|scaffold|spec] [--dossier-only] [--no-browser] [--slug <name>] [--out <dir>]"
---

Port an entire application into the MicroDots framework.
`$ARGUMENTS`: the source app's path (everything before the first flag), then
the flags in the argument hint.

A port here is a re-expression, not a copy. A MicroDot renders through
Foldkit's Elm architecture, talks over an Effect RPC contract, persists through
a platform-free storage seam, and exposes exactly two things to the world:
attributes in, DOM events out. React, Express, or anything else cannot be
transplanted into that shape. Four translations happen in every app port, and
the dossier exists to feed them:

- **App → composition.** A whole app rarely maps to one MicroDot. The seams
  lane finds the candidate cut lines; a composition proposal (N MicroDots,
  their tags, what the host brokers between them) is confirmed by the user
  before any per-dot design exists.
- **UI → TEA.** Observed screens and states become Model (effect Schema,
  discriminated unions), Messages, `update`, `view`, `subscriptions` — designed
  from behavior, never transliterated from JSX.
- **Data layer → contract + seam.** Observed payloads and traced schemas become
  RpcGroups with tagged errors, plus owned stores behind service interfaces.
- **Context → surface.** Everything the app took ambiently (env, session,
  globals) becomes an attribute, an outbound event, an owned RPC, or an
  explicit cut.

Each translation is driven by the **Effect-optimization register** — the
source-idiom → target-idiom mapping table — which is seeded from the skill's
own **port memory** so that patterns settled in prior ports arrive as
recommendations, not re-derivations.

## Phase 0 — Resolve the run

Parse `$ARGUMENTS`. Then resolve, in order:

1. **Source app** — the path argument, else the cwd. Read-only for the entire
   run. If it is itself a MicroDots workspace, stop: there is nothing to port.
2. **Target** — `--target <path>`, else ask via AskUserQuestion:
   - **MicroDots monorepo** — a path carrying ALL THREE markers: a
     `package.json` whose `workspaces` include `microdots/*`,
     `scripts/new-microdot.ts`, and `AGENTS.md`. Verify the markers before
     trusting any path, supplied or detected.
   - **Standalone directory** — any other directory (existing or new). The
     port lands as a self-contained Bun workspace on the published
     `@bespokeagentics/microdots-*` npm packages, mini-host included. Protocol in
     `references/standalone-scaffold.md`. Preflight NOW: `npm view
@bespokeagentics/microdots-runtime version` — if the packages are not resolvable, say so
     and stop before any analysis; standalone mode cannot work without them.
3. **Memory home** — resolve per `references/memory-protocol.md` and read
   `memory/stack-mappings.md` plus any port records whose stack fingerprint
   matches this source app. Matched rows enter Phase 4 as `prior`
   recommendations. No match is fine; say so and continue.
4. **Slug** — `--slug`, else lower-kebab from the app's name. Names the
   dossier directory and defaults the MicroDot name(s).
5. **Dossier home** — `<target>/docs/ports/<slug>/` (override `--out`). If it
   already exists, re-verify its anchors instead of re-tracing blind, and say
   so in the report.
6. **App URL** — `--app <url>`, else discovery per
   `references/visual-inventory.md` (probe common dev ports; offer to start
   the app's dev command, asking first; never simulate a walk from source).

`--mode` sets how far a run goes: `full` (default) runs every phase through
verify and the memory write; `scaffold` stops after the scaffold; `spec` stops
after the elicitation. `--dossier-only` stops after Phase 5's seeded spec.

## Phase 1 — Trace the whole app (source, read-only)

Launch parallel Explore agents over the source app — they locate code and
return file:line evidence, not opinions. Six lanes, detailed in
`references/tracing.md`: **Surface**, **Behavior**, **Data**, **API**,
**Dependencies**, and — new for a whole-app port — **Seams**: the candidate
composition cut lines (route groups, feature directories, independent state
islands, distinct server concerns) with the coupling evidence for and against
each cut.

Synthesize into `trace.md`: per-lane evidence, the boundary analysis (every
ambient dependency tagged with what it must become), and the seams summary the
composition proposal will consume.

## Phase 2 — Visual inventory (browser, main session)

Run the walk while the trace agents work; cross-reference when both finish.
Drive the browser from the main session, never a subagent — the login gate and
mid-walk questions only work here. Full protocol in
`references/visual-inventory.md`: one ToolSearch batch, fresh tab with an
explicit tabId, the user types all credentials, screenshot **states not
pages** (`ui/state-NN-<label>.png`), capture real network shapes after each
interaction, stop at the brink of anything irreversible. With `--no-browser`
or no reachable app: derive the inventory from code and label every claim
**"not visually verified"** — fabricating a visual claim is the one
unforgivable failure of this phase.

## Phase 3 — Ground in the target

Target law is read **at runtime** — this skill embeds none of it:

- **Monorepo mode**: `AGENTS.md` (layout, invariants, trap table — pull the
  applicable trap rows into a trap register), `docs/reuse-catalog.md` (match
  needs against the Trigger index; verify entries per the catalog's own
  maintenance protocol; fix rotted entries in this run), the trap index in
  `wiki/patterns-and-traps/_index.md`, and the existing MicroDot nearest in
  shape as the working reference.
- **Standalone mode**: the published `@bespokeagentics/microdots-*` package surface (confirm
  the exports you plan to import actually resolve) plus the port memory. If a
  MicroDots monorepo exists on disk anyway, use it **read-only** for catalog
  matching and as the idiom reference — say so in the dossier.

## Phase 4 — Composition, port map, optimization register

Method in `references/composition-and-port-map.md`. Order matters:

1. **Composition proposal first.** From the seams lane + the inventory, draft
   2–3 candidate compositions (each: the MicroDots, their custom-element tags,
   per-dot contract sketch, what the host brokers, what dies at the cut).
   Present via ONE AskUserQuestion with the recommendation first — the user
   confirms before any per-dot design is written. A brokered nudge is an
   optimisation; **a poll is the floor** for every cross-dot dependency.
2. **Per-MicroDot port maps** — public surface (attributes in, events out),
   contract draft, TEA sketch with the two-way state coverage check, data &
   storage, disposition table (`import-shared` / `copy-adapt` / `reimplement`
   / `drop` / `defer` — one row per traced unit).
3. **Effect-optimization register** — one row per source idiom found in the
   trace, mapped to its target idiom (React state → union Model, zod → effect
   Schema, fetch → RPC client, handlers → RpcGroup, env → attributes, polling
   → subscriptions, thrown errors → tagged errors, …), each row citing its
   evidence and its provenance: `standard` / `prior` (from memory, with the
   record named) / `novel` (this port mints it — a memory-write candidate).
4. **Trap register** and **decision register** — the genuinely open decisions
   (D-composition is pre-settled by step 1; D-data, D-auth, D-deploy, D-scope,
   D-ux, D-old-app and any app-specific rows remain), each with options, an
   evidence-backed recommendation, and a status (`open`/`assumed`/`decided`).

## Phase 5 — Seed the spec

Pre-write `spec.md` in the dossier using the spec-elicitation template's own
headers, per the mapping in `references/spec-and-execution.md`: fill every
section the dossier can answer with its citation; embed the decision register
under Assumptions & Open Questions; leave what only the user can answer as
`TODO — not yet elicited`. In monorepo mode, plans are authored in the wiki —
after the interview settles the spec, file it as a `decision` page in
`wiki/plans/active/` per the repo's schema. `--dossier-only` stops here.

## Phase 6 — Elicit (spec-elicitation)

Invoke the `spec-elicitation` skill with the dossier's `spec.md` path. It
reads, assesses, and interviews until every dimension is settled — do not
duplicate its interview, and do not settle register rows on the user's behalf.
When it finishes, flip the settled rows to `decided` in the port map so the
register and the spec never disagree. If the skill is unavailable, leave the
seeded spec + register in place and say plainly the interview still needs to
run.

## Phase 7 — Execute (gated)

Nothing outside the dossier directory is created or edited before this gate.
One AskUserQuestion: confirm the MicroDot name(s) (lower-kebab) and how far to
go — full implementation, scaffold only, or stop at the spec. For a port the
dossier shows to be large, offer the orchestrate handoff as an alternative to
building inline — the spec plus the port maps is exactly the plan it consumes.

On a yes (details in `references/spec-and-execution.md`):

1. **Scaffold.**
   - Monorepo: `bun run new:microdot <name>` per MicroDot, then the wiring
     steps `AGENTS.md` lists (tsconfig paths, vitest aliases, registry,
     `index.html` section + slot, `host-topology.json` route + slot). The
     topology tests are the wiring's own check.
   - Standalone: build the workspace per `references/standalone-scaffold.md`
     — Bun workspace, `@bespokeagentics/microdots-*` from npm with effect pinned to the exact
     peer version, one directory per MicroDot in the confirmed composition,
     and **always a mini-host** (registry + loader from `@bespokeagentics/microdots-host`,
     broker from `@bespokeagentics/microdots-bridge` when the composition needs it).
2. **Implementation waves per MicroDot**, each ending with the workspace's
   check green: contract + client → service + store + migrations + wire tests
   → TEA app + story tests (each observed UI state gets a story test where
   sensible) → element + styles + host wiring. The disposition table is the
   worklist; a disposition that proves wrong mid-wave is corrected in the port
   map, not silently diverged from.
3. **Verify.** Monorepo: invoke the repo's `verify` skill — its browser bar is
   the done bar. Standalone: the equivalent sequence by hand — check green,
   all bundles build, boot the dev script, and confirm in a browser that every
   MicroDot renders real content and polls its service. Green static checks
   alone are not done: `Runtime.embed` forks the runtime and swallows startup
   defects.
4. **Catalog maintenance** (monorepo mode): a genuinely reusable pattern this
   port minted gets its catalog entry and Trigger-index row in this run.

Deploy is never run — point at the target's deploy path and stop.

## Phase 8 — Write the port memory

After verify (or wherever the run stopped — labeled), append the port record
and update the stack mappings per `references/memory-protocol.md`: `novel`
optimization-register rows become new mapping rows; `prior` rows that held get
their confidence incremented; rows that proved wrong get annotated, never
deleted. Remind the user to commit the plugin repo — the skill never commits.

Then report honestly: the composition shipped vs proposed; ported / adapted /
dropped / deferred counts; dispositions corrected mid-flight; what verify
actually observed; traps hit; memory rows added or reinforced; what remains
(deploy, deferred decisions, the source app's fate).

## Hard rules

- **The source app is never modified.** Its retirement is a decision-register
  row, not an action.
- **The port is a re-expression.** Source UI code is never transplanted into
  Foldkit; target conventions win over source idioms everywhere they disagree.
- **Composition is confirmed by the user** before any per-dot design is
  written. Never silently decide the cut.
- **Target law is read at runtime** — AGENTS.md, the reuse catalog, the trap
  index, the published package surface. Never from memory, never from copies
  in this skill. The port memory stores _this skill's own port history_, never
  a copy of the target's rules.
- **You never type credentials**, never bypass CAPTCHAs, and stop at the brink
  of irreversible actions in the walk.
- **No production code before the execution gate.** Dossier artifacts are the
  only writes until Phase 7 says go.
- **Unverified claims are labeled** — "not visually verified", `assumed` —
  never dressed up as findings.
- **Compose by invocation** — spec-elicitation, the monorepo's new:microdot
  and verify, orchestrate — invoked, never reimplemented.
- **Deploy is never run. Nothing is committed** — in the target, the source,
  or the plugin repo.

## Degradation matrix

| Missing                                        | Behavior                                                                                                                                   |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Browser tools unavailable / no runnable app    | Skip Phase 2; derive the UX inventory from code; label every UX claim "not visually verified"; continue                                    |
| `@bespokeagentics/microdots-*` not resolvable on npm           | Standalone mode stops at preflight with the publish instructions; monorepo mode is unaffected                                              |
| No memory home writable                        | Fall back to `~/.claude/bespoke-agentics/port-memory/`; warn that the ledger is outside the plugin repo                                    |
| No matching memory rows                        | Normal for a new stack — proceed; this port seeds the rows                                                                                 |
| spec-elicitation unavailable                   | Leave the seeded spec + decision register; state that the interview still needs to run                                                     |
| Monorepo markers absent from a supplied target | Treat as standalone; say so                                                                                                                |
| Non-interactive run hits a decision point      | Record the recommendation as `assumed — not confirmed`; continue; never silently decide. Composition may NOT be assumed — it stops the run |

## Reference files

| File                                     | Read when                                                                                              |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `references/tracing.md`                  | Phase 1 — the six lanes, agent prompts, `trace.md` format, boundary + seams taxonomy                   |
| `references/visual-inventory.md`         | Phase 2 — tool loading, tab discipline, login gate, state screenshots, network capture                 |
| `references/composition-and-port-map.md` | Phase 4 — composition proposal, per-dot port maps, the Effect-optimization register, decision register |
| `references/standalone-scaffold.md`      | Phases 0 & 7 — target detection, npm dependency set, workspace layout, mini-host wiring, dev harness   |
| `references/spec-and-execution.md`       | Phases 5–7 — spec seeding map, elicitation handoff, execution gate, waves, verify per mode             |
| `references/memory-protocol.md`          | Phases 0 & 8 — memory home resolution, stack fingerprints, mapping-row lifecycle, port records         |
