---
name: microdots-port-prototype
description: >
  Turn a Claude Design prototype into a validated plan for building the same product as a
  composed collection of MicroDots (Effect v4 + Foldkit custom elements). Use whenever someone
  points at a Claude Design export -- a standalone `.html` artifact, a design zip, or an export
  directory -- and says "make this real", "build this as MicroDots", "turn this prototype into an
  app", "microdotize this design", or "what would it take to ship this". A Claude Design artifact
  is not a screenshot: its `__bundler/manifest` carries the original hand-written source, so the
  run begins by extracting a real, traceable source tree, then infers the functionality the
  prototype only mimes -- separating what genuinely works from demo theater (faked latency,
  hardcoded results, no-op handlers) -- confirms every inference in two AskUserQuestion
  interviews, derives MicroDot cut lines from the prototype's own module seams, and writes a
  dossier in exactly the shape `microdots-port-app` consumes before handing execution to it.
  Default runs stop at the validated plan; no production code is written without an explicit
  mode. Distinct from microdots-port-app (traces a REAL app that already has routes, servers and
  persistence) and from funcspec (extracts the functional layer from a Storybook, targeting no
  particular framework): this one starts from a prototype that only pretends to work, and lands
  on MicroDots specifically.
argument-hint: "<artifact.html|dir|zip> [--target <path>] [--mode plan|scaffold|full] [--slug <name>] [--out <dir>] [--serve] [--no-handoff] [--extract-only]"
---

Turn a Claude Design prototype into a MicroDots build plan.
`$ARGUMENTS`: the artifact path (everything before the first flag), then the flags above.

A prototype is not a small app. It has no routes, no server, no persistence and no
auth -- it has **mock data and mimed interactions**. So there is nothing to trace and
everything to infer. That inversion is the whole skill:

- **The artifact is not opaque.** Claude Design ships the original source inside the
  HTML. Phase 1 recovers it deterministically, turning an unreadable 1.8 MB file into a
  source tree with real `file:line` anchors -- which is also precisely what makes the
  Phase 8 handoff work, because `microdots-port-app` can already trace a source tree.
- **Mock data is the entity model.** The arrays a prototype renders from are the best
  evidence of its schema that exists. They are read as evidence, never shipped as truth.
- **Demo theater must be named before it is planned.** `setTimeout(…, 720)` standing in
  for a query is the single highest-value finding in a prototype: every faked wait is a
  service that does not exist yet. Miming is separated from working, out loud.
- **The prototype's seams are the composition evidence.** Which module writes
  `window.DATA` and which screens read it is a real, greppable dependency graph -- the
  candidate MicroDot cut lines, derived rather than invented.
- **Nothing inferred survives unconfirmed.** Two interviews bracket the analysis, exactly
  as `funcspec` does: Stage-1 frames it, Stage-2 validates it.

This skill owns the front half only. Composition proposal, per-dot port maps, the
Effect-optimization register, spec elicitation, scaffolding, waves and verify all belong
to `microdots-port-app`, which is invoked in Phase 8 rather than reimplemented.

## Phase 0 -- Resolve the run

Parse `$ARGUMENTS`, then resolve in order:

1. **Artifact.** Run `scripts/extract_design_bundle.py <artifact> --check`. Exit 2 means
   this is not a Claude Design export: **stop and redirect** -- a real app directory goes
   to `microdots-port-app`, a Storybook goes to `funcspec`, an undecided UI goes to
   `interactive-wireframe`. Do not degrade into reading the HTML by hand.
2. **Target.** `--target <path>`, else detect, else ask. Detection and the standalone
   preflight are target law, not this skill's: follow
   `../microdots-port-app/references/standalone-scaffold.md` (monorepo requires ALL THREE
   markers; standalone requires the `@bespokeagentics/microdots-*` packages to resolve on
   npm, and stops the run at preflight when they do not).
3. **Slug.** `--slug`, else lower-kebab from the artifact's `<title>` (Phase 1 reports it).
4. **Dossier home.** `<target>/docs/ports/<slug>/` unless `--out`. If it exists already,
   re-verify its anchors rather than re-deriving blind, and say so.
5. **Mode.** `--mode plan` (default) stops at the validated dossier and spec.
   `scaffold` and `full` are passed through to `microdots-port-app` at the Phase 8
   handoff -- this skill still writes no production code itself.
   `--extract-only` stops after Phase 2. `--no-handoff` stops after Phase 7.

## Phase 1 -- Extract the source tree

    python3 scripts/extract_design_bundle.py <artifact> --out <dossier>/_src

Deterministic, no judgment: the bundler template declares each script's role and load
order, so app source, vendor libraries, fonts and the design-token stylesheets separate
exactly, and every manifest entry is accounted for. Read `references/extraction.md` for
the format, the **two export shapes** (`babel-modules` -- many modules; `dc-runtime` --
the whole app as one inline component, which changes what Phase 2 classifies), what the
script guarantees, and what it deliberately refuses to guess. Report the shape, counts
and title before spending analysis on the wrong artifact.

`_src/` is the run's evidence base. **Every later claim cites `_src/app/<file>:<line>`.**

## Phase 2 -- Inventory and classify

Main thread, mechanical, from `_src/index.json` plus targeted greps
(`references/extraction.md` §Classification gives the grep set). Assign every app module
exactly one role: `screen` · `data-store` · `ui-kit` · `chrome` (nav/shell) ·
`scaffold` (Claude Design's own tooling -- the tweaks panel is always this, and always
dies at the port) · `vendor-global`. Record the `window.*` read/write graph in the same
pass: it is the seam evidence Phase 5 consumes.

Write `<dossier>/prototype-inventory.json` and report the classification. A module whose
role is unclear is listed as `unclassified` and asked about in Stage-1 -- never silently
bucketed.

## Phase 3 -- Stage-1 interview (frame the analysis)

AskUserQuestion, per `references/interview-protocol.md` §Stage-1. Settles product
purpose, real users and roles, backend reality, auth, non-goals, integration targets,
and the two questions only a prototype raises: **which screens are the product and which
are demo filler**, and **how faithful the visual design must stay**. The digest goes to
`<dossier>/context.md`, under ~30 lines, and is passed verbatim to every Phase 4 agent.

## Phase 4 -- Functional inference (parallel agents)

Chrome and data-store modules first, sequentially -- they carry the route map and the
entity evidence every screen inherits. Then **all screen modules simultaneously**, one
`prototype-screen-analyst` agent each, dispatched in a single message. Each gets its
module path, `context.md`, the chrome/data profiles, the schema at
`assets/templates/screen-profile.schema.json`, the taxonomy at
`references/functional-inference.md`, and a disjoint `output_path`.

Agents return affordances, operations, entities, states, navigation, **theater findings**
and ambiguities -- each cited, each confidence-tagged. They never ask the user; an
ambiguity is recorded for Stage-2, not resolved. Validate each profile against the schema
as it lands; re-run a failure once with the error, then do that module in the main thread.

## Phase 5 -- Synthesis and seams

Main thread -- this is judgment, not mechanics. Per `references/functional-inference.md`
§Synthesis, merge the profiles into `<dossier>/synthesis.json`: entity model, route map,
feature inventory clustered into domains, shared services, the consolidated theater
register, and the consolidated ambiguity register ordered blocking-first.

Then the piece `microdots-port-app` cannot derive from a prototype and needs: the
**seams analysis**. Cross the `window.*` graph with the feature domains to produce
candidate cut lines, each with its evidence for, what crosses it, and what would have to
be host-brokered. This is evidence for Phase 8's composition proposal -- **it is not the
composition decision**, which belongs to `microdots-port-app` and its user gate.

## Phase 6 -- Stage-2 interview (validate everything)

The alignment gate, per `references/interview-protocol.md` §Stage-2: confirm or cut each
domain's features; confirm each theater finding as *must become real* / *stays mocked for
now* / *drop*; resolve blocking ambiguities; set P0/P1/P2. Update `synthesis.json` and the
profiles in place. **A blocking ambiguity is never deferred silently** -- ask, or get
explicit permission to defer and mark it 🔴.

## Phase 7 -- Write the dossier

Per `references/dossier-and-handoff.md`, render the validated state into the artifact
names `microdots-port-app` already reads, so the handoff needs no translation:
`trace.md` (from `_src`, with the client/server split stated honestly as *no server
existed*), `ui-inventory.md` (from the screen profiles, every row labeled
`derived from prototype source` unless `--serve` produced real screenshots),
`functional-spec.md`, `seams.md`, and `dossier-manifest.json` -- the machine-readable
declaration of which of port-app's phases are already satisfied and by what evidence.

`--serve` optionally serves `_src/shell.html` and walks it in a browser for real state
screenshots, following `../microdots-port-app/references/visual-inventory.md`. Without it,
every UX claim is labeled **"not visually verified"**. Fabricating a visual claim is the
one unforgivable failure of this phase.

## Phase 8 -- Hand off to microdots-port-app

Invoke the `microdots-port-app` skill with the dossier path as `--out`, `_src/` as the
source app, the resolved target and slug, `--no-browser` (unless `--serve` ran), and the
resolved `--mode`. State in the invocation that the dossier is pre-populated and that
`dossier-manifest.json` declares which phases to skip and which to re-verify. It then
runs its own Phases 3-8: ground in the target, propose composition (**user-gated**),
write the port maps and Effect-optimization register, seed and elicit the spec, and -- in
`scaffold`/`full` -- scaffold, implement in waves and verify.

`--no-handoff` stops here with the dossier as the deliverable; say plainly that
composition and the spec have not been settled.

Then report: what was extracted, how much was theater, what Stage-2 confirmed and cut,
where the run stopped, and what the handoff decided versus what remains open.

## Hard rules

- **The artifact is never modified**, and nothing outside the dossier directory is
  written before the Phase 8 handoff.
- **Evidence or ambiguity.** Every behavior in the dossier cites `_src/app/<file>:<line>`
  or an interview answer. Two readings means ask, not pick.
- **Theater is named, never quietly upgraded.** A faked interaction becomes a planned
  service only by a Stage-2 answer, and the register records which.
- **Mock data is evidence, not seed data.** It types the entity model; whether any of it
  ships is a Stage-2 decision.
- **Seams are evidence, not the composition.** This skill never decides the cut --
  `microdots-port-app` proposes it and the user confirms it.
- **Compose by invocation.** `microdots-port-app`, `spec-elicitation` and the target's own
  generators are invoked, never reimplemented; target law is read at runtime.
- **Unverified claims are labeled** -- "not visually verified", "inferred", `assumed`.
- **Reject cleanly.** A non-Claude-Design input is redirected to the right skill, not
  half-handled.
- **Nothing is committed. Deploy is never run.**

## Degradation matrix

| Missing | Behavior |
| --- | --- |
| Input is not a Claude Design artifact | Stop at Phase 0 with the redirect; never fall back to reading the HTML by hand |
| Artifact has a manifest but no template | Extraction exits 3; roles and load order are unrecoverable. Offer to proceed with modules named by UUID and every role tagged `unclassified` -- say the confidence cost out loud |
| Unrecognized export shape (`bundle_shape: "unknown"`, 0 app modules) | The extractor warns and still writes everything. Proceed only with every module `unclassified`, and state the confidence cost before Stage-1 rather than after |
| Vendored globals unresolvable (an external design-system global) | Record as an external dependency in the seams analysis and a D-scope row; never guess its API |
| Browser unavailable or `--serve` not passed | Skip the walk; label every UX claim "not visually verified"; continue |
| `@bespokeagentics/microdots-*` not resolvable and target is standalone | Stop at Phase 0 preflight per the standalone-scaffold reference -- extraction without a viable target wastes the run |
| `microdots-port-app` unavailable | Stop after Phase 7; deliver the dossier; state plainly that composition, spec and execution still need to run |
| Non-interactive run hits a decision point | Record the recommendation as `assumed -- not confirmed`; continue. Blocking ambiguities may NOT be assumed -- they stop the run |

## Reference files

| File | Read when |
| --- | --- |
| `references/extraction.md` | Phases 1-2 -- bundle format, what the script guarantees vs refuses, the classification grep set |
| `references/functional-inference.md` | Phases 4-5 -- the affordance taxonomy, theater detection, mock-data entity extraction, synthesis and seams |
| `references/interview-protocol.md` | Phases 3 & 6 -- both question banks, batching rules, answer → state conversions |
| `references/dossier-and-handoff.md` | Phases 7-8 -- dossier artifact formats, `dossier-manifest.json`, the handoff contract |
| `assets/templates/screen-profile.schema.json` | Phase 4 -- the profile contract every agent writes to |
| `../microdots-port-app/references/standalone-scaffold.md` | Phase 0 -- target detection and standalone preflight (target law; read, never copied) |
| `../microdots-port-app/references/visual-inventory.md` | Phase 7 -- browser walk protocol when `--serve` is passed |
