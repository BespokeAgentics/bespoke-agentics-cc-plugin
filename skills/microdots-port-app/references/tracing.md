# Phase 1 — Tracing the whole app

`trace.md` is the evidence base for everything downstream: the composition
proposal, the public surfaces, the contract drafts, the TEA sketches, and the
spec all cite it. Its job is to be _complete and neutral_ — every place the
app's behavior lives, every dependency it has, every ambient thing it consumes,
with file:line anchors — and to editorialize nothing. Dispositions, designs and
the composition itself come later, with the target-side constraints in hand.

## Scoping before tracing

The scope is the whole app, so the scoping question is the app's _edges_, not
which feature. Establish before launching agents: the app root and what is
inside it (a quick `ls` + the package.json scripts tell you the client/server
split), what is vendored vs. depended on, and whether the directory holds one
app or several (a workspace root pointed at by mistake → ask which member).
Anything the user said about the app is a hint — verify it before building on
it.

## The six lanes

Run the lanes as parallel Explore agents — they locate code and return
evidence, and are read-only by construction. One agent per lane is the
default; merge lanes for a small app, split them further for a sprawling one.
Every agent prompt should demand: file:line for every claim, short verbatim
excerpts only where definitional, and an explicit "not found / not applicable"
rather than silence for anything absent.

### 1. Surface

Every route/page/view the app serves, its navigation structure, and the
component tree per view — each component with its props, local state, and
conditional renders. Include the shell (layout, nav, toasts, error
boundaries): in a whole-app port the shell either becomes the mini-host's
concern or dies at the cut, and either way it must be visible.

### 2. Behavior

What the app _does_: user events handled, state transitions, side effects,
timers and polling intervals, websocket/SSE subscriptions, optimistic updates,
debounces, retries, validation rules (client and server), derived/computed
values. This lane feeds the TEA sketches directly — Foldkit needs behavior,
not markup — so precision here is worth more than anywhere else. Capture rules
as rules ("submit disabled until title non-empty, `Form.tsx:88`"), not as
descriptions of code.

### 3. Data

The types/schemas/models the app reads and writes, and where each is defined —
name the schema library explicitly (zod, io-ts, hand-rolled): it is an
optimization-register row. Persistence: tables/collections/keys/files, the
queries that touch them, migrations, indexes. Then the coupling finding:
**which views/features read and write the same data** — shared data is the
strongest argument against a composition cut, and the seams lane consumes this
list.

### 4. API

Client side: every endpoint called, with request/response shapes as declared
(Phase 2 checks them against the wire). Server side: every handler, grouped by
concern; external/third-party services touched — an Agent SDK, an LLM API, a
mail sender each force decisions (D-deploy, secrets) later. Auth: session
reads, token usage, permission checks — each is a boundary crossing, because a
MicroDot has no ambient session (auth in the target is per-call and
fail-closed, and secrets fail closed).

### 5. Dependencies

npm packages the app actually exercises (the closure of the traced files'
imports, not the lockfile). For each: shallow use (one call — trivially
reimplemented) or structural (the app is built around it). Structural
dependencies with no Effect-native equivalent are decision-register rows, not
surprises.

### 6. Seams

The lane the composition proposal consumes. Candidate cut lines through the
app, each with evidence for and against:

- **Route groups** that never share client state (for: independent; against:
  a shared store subscription found by the data lane).
- **Feature directories** with disjoint import closures.
- **Independent state islands** — subtrees whose state never crosses a
  boundary except through the server.
- **Distinct server concerns** — handler groups touching disjoint tables.
- **Different change cadences or audiences** (an admin surface vs. the public
  surface).

For each candidate cut: what crosses it today (props, store reads, shared
tables, direct calls), and therefore what the cut would force (a brokered
event, a poll, a shared service, or a merge). A seam with heavy crossings is
still worth recording — "do not cut here" is composition evidence too.

## Boundary analysis

List everything the app consumes ambiently that will **not** come along, and
tag each crossing with what it must become:

| Crossing                 | Examples                                      | Becomes                                                                 |
| ------------------------ | --------------------------------------------- | ----------------------------------------------------------------------- |
| Configuration            | env vars, build flags, base URLs              | **Attribute** — the mounting host chooses, never the build              |
| Ambient session/auth     | `useSession()`, middleware, role checks       | **Auth decision** — usually a per-call gate or nothing; never a session |
| Shared data across seams | tables multiple candidate dots touch          | **Data-ownership decision** — one dot owns it, or the cut moves         |
| Cross-view signals       | "tell the rest of the app something happened" | **Event out**, host-brokered; **a poll is the floor**                   |
| Shared code              | design system, utils, stores                  | **Reimplement or drop** — resolved per unit in the disposition table    |
| Shell affordances        | global nav, toasts, error boundaries          | **Mini-host concern or cut** — a MicroDot does not own the page         |
| External services        | LLM/Agent SDKs, third-party APIs, webhooks    | **Service-side call** — flag deploy-target and secret consequences      |

Each row cites the trace evidence that discovered it. A crossing missing here
is a design surprise later, found at implementation time when it is most
expensive.

## `trace.md` format

```markdown
# Trace — <app> (<source path>)

Date · source path · scope note (what was included/excluded and why)

## Summary

3–6 sentences: what the app is, its client/server split, how big it is.

## Surface

| What | Where | Notes |
(routes, views, components — one row each, file:line; the shell has its own rows)

## Behavior

Rules and transitions, one bullet each, every one anchored.

## Data

Schema library named · types/schemas · persistence · queries — then:

### Cross-view readers/writers of the same data

| Data | Who touches it | file:line |

## API

Called · served (grouped by concern) · external services · auth touchpoints.

## Dependencies

| Dependency | Kind (npm/internal) | Usage depth (shallow/structural) | file:line |

## Seams

| Candidate cut | Evidence for | Evidence against (what crosses) | file:line |

## Boundary analysis

The crossings table (taxonomy above), every row anchored.

## Not found / uncertain

What was looked for and not found. Absence stated is evidence; absence
unstated is a landmine.
```

## Rules

- The source app is read-only. Tracing never "cleans up" anything it finds.
- Neutrality: no dispositions, no composition verdicts, no target-system
  design in `trace.md`. The seams lane presents evidence; Phase 4 proposes.
- An unfindable anchor is reported as unfindable — never silently dropped,
  never guessed into existence.
