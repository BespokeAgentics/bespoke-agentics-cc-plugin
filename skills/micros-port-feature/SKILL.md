---
name: microdots-port-feature
description: >
  Extract a feature from an existing application and port it into a standalone micro-app in the
  Effect/Foldkit micros workspace. Use whenever someone says "port X into a micro", "extract this
  feature into a standalone micro-app", "carve the <thing> out of <app>", "turn this feature into
  its own micro", or points at functionality in a running product that should become an
  independently deployable micro-app. The port is a re-expression, not a copy: parallel agents
  trace the feature's full path through the source repo (routes, components, state, data
  structures, persistence, API surface, auth — file:line cited), a Claude-in-Chrome walk takes a
  visual inventory of the real UX (screenshots per state, live network payload shapes) behind a
  login gate where the user types all credentials, the micros workspace's own AGENTS.md and
  docs/reuse-catalog.md are read at runtime to match prior art, and everything lands in a port
  dossier: trace map, UI inventory, port map (attributes-in/events-out surface, contract draft,
  TEA sketch, per-unit dispositions), and a decision register. A partial spec pre-written from the
  dossier seeds a spec-elicitation interview; only after the spec is settled does execution run —
  new-micro scaffold, implementation waves each ending green, verify's browser check. Deploy is
  never run; the source repo is never modified; nothing is committed. Degrades gracefully: no
  running app or browser → code-derived UX inventory, honestly labeled. Distinct from new-micro
  (scaffolds fresh and ports prior art between micros in the same workspace): this one extracts a
  feature from a FOREIGN codebase and carries it across the boundary.
argument-hint: "'<feature>' [--source <path>] [--micros <path>] [--app <url>] [--mode full|scaffold|spec] [--dossier-only] [--no-browser] [--slug <name>] [--out <dir>]"
---

Port a feature out of an existing application into a standalone micro-app.
`$ARGUMENTS`: a feature pointer (free text, a route, a component name — usually
quoted, everything before the first flag), then the flags in the argument hint.

A port here is a re-expression, not a copy. A micro-app renders through
Foldkit's Elm architecture, talks over an Effect RPC contract, persists through
a platform-free storage seam, and exposes exactly two things to the world:
attributes in, DOM events out. Source code written for React, Express, Rails or
anything else cannot be transplanted into that shape. What carries the feature
across is evidence — a file:line-cited trace of what the code does, a visual
inventory of what the user actually experiences, and the real payload shapes on
the wire — plus explicit decisions about everything the boundary cut severs.
This skill gathers the evidence, forces the decisions, and only then builds.

Three translations happen in every port, and the dossier exists to feed them:

- **UI → TEA.** Observed screens and states become a Model (Effect Schema),
  Messages, `update`, `view`, `subscriptions` — designed from behavior, never
  transliterated from JSX.
- **Data layer → contract + seam.** Observed payloads and traced schemas become
  an RpcGroup with tagged errors, plus an owned store behind a service
  interface when the feature is stateful.
- **Context → surface.** Everything the feature silently took from its old app
  (env, session, global stores, the shell) must become an attribute, an
  outbound event, an RPC the micro owns, or an explicit cut. Designing that
  surface is the hardest work of the port; the boundary analysis exists to make
  every crossing visible before anyone commits to a shape.

## Phase 0 — Resolve the run

Parse `$ARGUMENTS`. Then resolve, in order:

1. **Source repo** — `--source <path>`, else the current working directory. The
   source is where the feature lives today; it is read-only for the entire run.
   If the cwd turns out to be the micros workspace itself and no `--source` was
   given, ask for the source repo — porting between micros in the same
   workspace is `new-micro`'s prior-art protocol, not this skill.
2. **Micros workspace** — `--micros <path>`, else the cwd if it looks like one
   (a `package.json` with `micros/*` in `workspaces`, plus
   `scripts/new-micro.ts` and `docs/reuse-catalog.md`), else ask once via
   AskUserQuestion. Verify whichever path wins actually carries those three
   markers before trusting it — a wrong target repo makes every later phase
   nonsense.
3. **Slug** — `--slug`, else lower-kebab derived from the feature pointer. It
   names the dossier directory and is the default micro name (confirmed at the
   execution gate; the generator will reject anything that is not lower-kebab).
4. **Dossier home** — `<micros>/docs/ports/<slug>/` (override with `--out`).
   If it already exists, treat its artifacts as a prior run's: re-verify their
   anchors instead of re-tracing blind, and say so in the report.
5. **App URL** — `--app <url>`, else discovery per
   `references/visual-inventory.md` (probe common dev ports; offer to start
   the repo's dev command, asking first; never simulate a walk from source).

If the feature pointer plausibly matches more than one thing in the source repo
(a quick grep tells you), ask which one before spending trace effort. When no
user is available to ask (a non-interactive run), pick the evidence-backed
reading, record it in the decision register as `assumed`, and never decide
silently.

`--mode` sets how far a run goes: `full` (default) runs every phase through
verify; `scaffold` stops after the new-micro scaffold; `spec` stops after the
elicitation. `--dossier-only` stops earlier still — after Phase 5's seeded
spec, before any interview — for preparing a port now and settling it later.

## Phase 1 — Trace the feature path (source repo, read-only)

Launch parallel Explore agents over the source repo — they locate code and
return file:line evidence, not opinions. Five lanes, detailed in
`references/tracing.md`:

1. **Surface** — routes/pages/nav where the feature manifests; the component
   tree that renders it, with props and local state.
2. **Behavior** — events, state transitions, side effects, timers/polling/
   sockets, optimistic updates, validation rules.
3. **Data** — the types/schemas/models involved; persistence (tables,
   collections, keys), the queries that touch them, and **every other
   reader/writer of the same data** — shared tables are the most common hidden
   coupling and drive the data-ownership decision later.
4. **API** — endpoints the feature calls and serves, request/response shapes,
   external services, auth/session touchpoints and permission checks.
5. **Dependencies** — npm packages the traced files actually exercise;
   internal shared modules (utils, design system, contexts) they lean on.

Synthesize into `trace.md`: the per-lane evidence plus the **boundary
analysis** — an honest list of everything the feature touches that will not
come along, each crossing tagged with what it must become (attribute, event,
owned RPC/data, external call, or cut). Do not assign dispositions yet; Phase 4
does that with the micros-side constraints in hand. Anchors the user supplied
are hints, not gospel — verify them like anything else.

## Phase 2 — Visual inventory (browser, main session)

Run the walk while the trace agents work; cross-reference when both finish.
Drive the browser from the main session, not a subagent — the login gate and
any mid-walk question to the user only work here. Full protocol in
`references/visual-inventory.md`; the shape:

- Load the Claude-in-Chrome tools in **one** ToolSearch batch; call
  `tabs_context_mcp` first; create a fresh tab and pass its explicit tabId to
  every call.
- **Login gate before any capture**: the user logs in and clears
  banners/consent themselves. You never type credentials, never bypass
  CAPTCHAs.
- Walk the feature and screenshot **states, not pages** —
  `ui/state-NN-<label>.png` — noting per state: the components on screen
  (cross-referenced to the trace), the data shown, microcopy, and available
  interactions. Hunt empty/loading/error states where reachable. Filling forms
  to surface validation is fine; submitting mutations needs the user's OK in
  the moment; stop at the brink of anything irreversible.
- After each interaction, capture the feature's real traffic with
  `read_network_requests`: method, path, representative request/response
  shapes, secrets and PII redacted. Observed payloads ground the contract
  draft in reality rather than in code-reading alone.
- If the walk exposes sensitive production data, say so and ask whether
  screenshots or structure-only notes should land in the dossier.

Write `ui-inventory.md`: the state catalog, interaction log, network-shape
table, and an explicit list of states not reached and why. With `--no-browser`,
no browser tools, or no reachable app, skip the walk, derive the UX inventory
from code, and label every such claim **"not visually verified"** — the
degradation matrix at the bottom of this file governs; fabricating a
visual claim is the one unforgivable failure of this phase.

## Phase 3 — Ground in the micros workspace

Read the workspace's own law **at runtime** — this skill deliberately embeds
none of it, because an embedded copy would rot and then lie:

- `AGENTS.md` — the layout contract, the hard rules, and the trap table.
  Extract the rows that plausibly apply to this port into a trap register.
- `docs/reuse-catalog.md` — match the feature's needs against the Trigger
  index; note matched pattern IDs. Verify entries per the catalog's own
  maintenance protocol (`ls` listed paths; on a miss, grep the Key symbols;
  fix rotted entries in this run, not in a TODO).
- The existing micros — pick the one closest in shape (poll-only display,
  stateful + gated, streaming) as the working reference for Phase 4 and the
  implementation waves.

## Phase 4 — Port map + decision register

Synthesize everything into `port-map.md` — the implementer's worklist and the
decision feed for the spec. Format and method in `references/port-map.md`:

1. **Public surface** — every boundary crossing from the trace resolved into
   attributes in (name, type, who sets it) and events out (name, payload, who
   listens). This is the cut line, formalized.
2. **Contract draft** — RPC names, payload/success schemas derived from
   observed network shapes intersected with traced types, tagged errors from
   observed failures and validation rules.
3. **TEA sketch** — Model states, Messages, subscriptions, view zones. Every
   state observed in Phase 2 must map to a Model state, and every Model state
   must have a decided view — a total mapping, both directions.
4. **Data & storage** — owned tables, the storage-seam shape, migrations,
   seeding.
5. **Disposition table** — one row per traced unit:
   `source file:line → disposition → target`, disposition ∈ `import-shared` /
   `copy-adapt` / `reimplement` / `drop` / `defer`.
6. **Trap register** — the applicable trap-table rows, cited.
7. **Decision register** — the genuinely open decisions, each with id,
   options, an evidence-backed recommendation, and a status
   (`open` / `assumed` / `decided`): data ownership (fresh start, one-off
   import, or keep reading the source system), auth model, deploy target
   (Workers vs a long-lived runtime, with the in-memory-state consequences),
   scope cuts, UX fidelity, single vs multi element, and what happens to the
   feature in the old app. This register is the interchange format the spec
   interview consumes.

## Phase 5 — Seed the spec

Pre-write `spec.md` in the dossier using the spec-elicitation template's own
section headers, per the mapping table in
`references/spec-and-execution.md`: fill every section the dossier can answer,
each claim carrying its citation (trace anchor, screenshot, or network shape);
embed the decision register under Assumptions & Open Questions; leave what only
the user can answer as the template's `TODO — not yet elicited`. A seeded
section the evidence cannot support is worse than a TODO — the interview exists
to fill gaps, not to audit fabrications. `--dossier-only` stops here.

## Phase 6 — Elicit (spec-elicitation)

Invoke the `spec-elicitation` skill with the dossier's `spec.md` path as its
argument. Its first phase reads the file, assesses completeness, and interviews
until every dimension is settled — the pre-written spec is the documented way
to hand it context, and a well-seeded spec naturally shrinks the interview to
the decisions that are actually open. Do not duplicate its interview here, and
do not resolve decision-register rows yourself that the interview should
settle. If the skill is unavailable, leave the seeded spec and the register in
place and say plainly that the interview still needs to run.

## Phase 7 — Execute (gated)

Nothing in the micros workspace outside the dossier directory is created or
edited before this gate. One AskUserQuestion: confirm the micro name
(lower-kebab), and how far to go — full implementation, scaffold only, or stop
at the spec. For a port the dossier shows to be large (a multi-thousand-line
feature), offer the orchestrate handoff as an alternative to building inline —
the spec and port map are exactly the plan it consumes.

On a yes, in order (details in `references/spec-and-execution.md`):

1. **Scaffold** — invoke the `new-micro` skill with `<name>` plus a brief
   distilled from the spec that names the catalog-matched needs, so its own
   prior-art protocol ports the matched patterns. Never reimplement the
   scaffold or wiring here.
2. **Implementation waves**, each ending with `bun run check` green:
   contract + client → service + store + migrations + wire tests → TEA app +
   story tests (each observed UI state gets a story test where sensible —
   that is what behavior preservation means here) → element + styles +
   multi-tag conversion if needed. The disposition table is the worklist; a
   disposition that proves wrong mid-wave is corrected in `port-map.md`, not
   silently diverged from.
3. **Verify** — invoke the `verify` skill. Its browser bar is the done bar;
   green static checks alone do not make a port done.
4. **Catalog maintenance** — if the port shipped a genuinely reusable pattern,
   append the catalog entry and Trigger-index row in this run.

Deploy is never run by this skill — point at the `deploy` skill and stop.

Then report honestly: what was ported, adapted, dropped, deferred; dispositions
changed mid-flight; what verify actually observed; traps hit; catalog entries
added or fixed; and what remains (deploy, deferred data decisions, the old
app's fate).

## Hard rules

- **The source repo is never modified.** The old app's retirement is a
  decision-register row, not an action.
- **The port is a re-expression.** Source UI code is never transplanted into
  Foldkit; workspace conventions win over source-app idioms everywhere they
  disagree.
- **Workspace law is read at runtime** — AGENTS.md, the reuse catalog, the
  trap table. Never from memory, never from copies in this skill.
- **You never type credentials**, never bypass CAPTCHAs, and stop at the brink
  of irreversible actions in the walk.
- **No production code before the execution gate.** Dossier artifacts are the
  only writes until Phase 7 says go.
- **Unverified claims are labeled** — "not visually verified", "not walked",
  `assumed` — never dressed up as findings.
- **Compose by invocation** — spec-elicitation, new-micro, verify are invoked,
  never reimplemented.
- **Deploy is never run. Nothing is committed.**

## Degradation matrix

| Missing                                     | Behavior                                                                                                                           |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Browser tools unavailable                   | Skip Phase 2; derive the UX inventory from code; label every UX claim "not visually verified"; continue                            |
| No running app, none startable with consent | Same as above — never simulate a walk from source                                                                                  |
| Login wall the user cannot clear            | Inventory what is reachable; unreached states listed as "not walked" with the reason                                               |
| Native dialog freezes the extension         | Ask the user to dismiss it in the browser, re-run `tabs_context_mcp`, resume                                                       |
| No micros workspace found or confirmed      | Offer trace + inventory only, written to `--out` or `<source>/plans/ports/<slug>/`, labeled partial; Phases 3–7 need a real target |
| spec-elicitation unavailable                | Leave the seeded spec + decision register; state that the interview still needs to run                                             |
| Non-interactive run hits a decision point   | Record the recommendation as `assumed — not confirmed` in the register; continue; never silently decide                            |

## Reference files

| File                               | Read when                                                                                                                 |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `references/tracing.md`            | Phase 1 — the five lanes, agent prompts, `trace.md` format, boundary-analysis taxonomy                                    |
| `references/visual-inventory.md`   | Phase 2 — tool loading, tab discipline, login gate, state screenshots, network capture, gotchas, `ui-inventory.md` format |
| `references/port-map.md`           | Phases 3–4 — catalog matching, surface design, contract drafting, TEA translation, dispositions, decision register        |
| `references/spec-and-execution.md` | Phases 5–7 — spec seeding map, elicitation handoff, execution gate, waves, verify, report                                 |
