# Phase 1 — Tracing the feature path

`trace.md` is the evidence base for everything downstream: the surface design,
the contract draft, the TEA sketch, and the spec all cite it. Its job is to be
*complete and neutral* — every place the feature lives, every dependency it
has, every boundary it crosses, with file:line anchors — and to editorialize
nothing. Dispositions and designs come later, once the micros-side constraints
are in hand; a trace that pre-decides them will quietly hide options.

## Scoping before tracing

Resolve the feature pointer to a concrete starting set before launching
agents. A quick grep for the pointer's obvious tokens (route path, component
name, on-screen label) tells you whether it names one thing or three. Three →
ask the user which; non-interactive → pick the reading with the strongest
evidence, log it as `assumed` in the decision register, and scope the trace to
it. Anchors the user supplied (a file, a line, a component name) are hints —
verify each before building on it; codebases move faster than the memories
pointing at them.

## The five lanes

Run the lanes as parallel Explore agents — they locate code and return
evidence, and are read-only by construction. One agent per lane is the default;
merge lanes for a small feature, split them further for a sprawling one. Every
agent prompt should demand: file:line for every claim, short verbatim excerpts
only where definitional, and an explicit "not found / not applicable" rather
than silence for anything absent.

### 1. Surface
Where the feature manifests to a user: routes/pages, navigation entries,
modals, embedded widgets. The component tree that renders it — each component
with its props, local state, and conditional renders. Include what *surrounds*
it (layout, shell chrome it sits inside) because that context is exactly what
will not come along.

### 2. Behavior
What the feature *does*: user events handled, state transitions, side effects,
timers and polling intervals, websocket/SSE subscriptions, optimistic updates,
debounces, retries, validation rules (client and server), derived/computed
values. This lane feeds the TEA sketch directly — Foldkit needs behavior, not
markup — so precision here is worth more than anywhere else. Capture the rules
as rules ("submit disabled until title non-empty and date valid,
`Form.tsx:88`"), not as descriptions of code.

### 3. Data
The types/schemas/models the feature reads and writes, and where each is
defined. Persistence: tables/collections/keys, the queries that touch them,
migrations that created them, indexes that matter. Then the finding this lane
exists for: **every other reader and writer of the same data**. A feature that
"owns" a table another page also renders is not separable without a decision;
shared data is the most common hidden coupling in any extraction, and the
data-ownership row of the decision register is built from this list.

### 4. API
Client side: every endpoint the feature calls, with request/response shapes as
the code declares them (Phase 2 later checks them against the wire). Server
side: the handlers behind those endpoints, and any endpoints the feature
*serves* to other parts of the app. External/third-party services touched.
Auth: session reads, token usage, permission checks, role gates — each one is
a boundary crossing, because a micro-app has no ambient session (auth in the
target system is per-call and fail-closed).

### 5. Dependencies
npm packages the traced files actually exercise (not the whole lockfile — the
closure of the traced files' imports). Internal shared modules: utilities,
design-system components, contexts/stores, i18n, feature flags. For each,
note whether the feature uses it shallowly (one formatting call — trivially
reimplemented) or structurally (a shared store it subscribes to — a real
crossing).

## Boundary analysis

The synthesis step, and the reason the trace exists. List everything the
feature touches that will **not** come along, and tag each crossing with what
it must become. The taxonomy:

| Crossing | Examples | Becomes |
|---|---|---|
| Configuration | env vars, build flags, base URLs | **Attribute** — the mounting host chooses, never the build |
| Ambient session/auth | `useSession()`, middleware, role checks | **Auth decision** — usually a per-call gate or nothing; never a session |
| Shared data | tables other features read/write | **Data-ownership decision** — own it, import once, or keep reading the source system |
| Outbound notifications | "tell the app something happened" | **Event out** — a CustomEvent the host may broker |
| Shared code | design system, utils, stores | **Reimplement or drop** — resolved per unit in the disposition table |
| Shell affordances | global nav, toasts, error boundaries | **Cut or event** — the micro does not own the page |
| External services | third-party APIs, webhooks | **Service-side call** — likely new ground in the workspace; flag it |

Each row cites the trace evidence that discovered it. The table's rows are the
raw material for Phase 4's public surface and decision register — a crossing
missing here is a design surprise later, found at implementation time when it
is most expensive.

## `trace.md` format

```markdown
# Trace — <feature> (<source repo>)
Date · source path · pointer as given · scope note (what was included/excluded and why)

## Summary
3–6 sentences: what the feature is, where it lives, how big it is (files/LOC touched).

## Surface
| What | Where | Notes |
(routes, components — one row each, file:line)

## Behavior
Rules and transitions, one bullet each, every one anchored.

## Data
Types/schemas · persistence · queries — then:
### Other readers/writers of the same data
| Data | Who else touches it | file:line |

## API
Called · served · external · auth touchpoints — anchored tables.

## Dependencies
| Dependency | Kind (npm/internal) | Usage depth (shallow/structural) | file:line |

## Boundary analysis
The crossings table (taxonomy above), every row anchored.

## Not found / uncertain
What was looked for and not found; what remains ambiguous. Absence stated is
evidence; absence unstated is a landmine.
```

## Rules

- The source repo is read-only. Tracing never "cleans up" anything it finds.
- Neutrality: no dispositions, no target-system design in `trace.md`.
- An unfindable anchor is reported as unfindable — never silently dropped,
  never guessed into existence.
