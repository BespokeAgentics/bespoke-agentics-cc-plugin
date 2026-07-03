# Phase 2 — State Model Design

Goal: turn the behavior map into a statechart the user can read, critique, and approve. The output,
`state-model.md`, is a design document — no application code changes yet.

## Choosing the style (`--style auto`)

Recommend the *simplest* structure that makes the behavior explicit:

- **Flat machine** — one dimension of behavior, ≤ ~7 states, effects are simple invocations.
  (Toggle, fetch-with-retry, confirmation dialog.)
- **Hierarchical statechart** — states share behavior a parent can own (a global `CANCEL` from any
  `active.*` substate), or a mode contains its own sub-flow (wizard steps inside `editing`). Nesting
  earns its place when it *removes* repeated transitions; never nest for taxonomy.
- **Parallel states** — two independent concerns today live in one component and change together
  (e.g. `validation` and `submission` regions of a form). Parallel regions in one machine beat two
  machines when they must be coordinated by guards; otherwise prefer two actors.
- **Actor system** — dynamic collections (one actor per upload/row/connection), long-lived processes
  (socket managers), or logic shared across UI trees. Spawned children own their lifecycle; the
  parent holds refs in context. Promise/callback/observable actors (`fromPromise`, `fromCallback`,
  `fromObservable`) are the default home for every side effect from the behavior map's inventory.
- **Not XState** — 2–3 states, one event, no async races: recommend a plain reducer or
  `@xstate/store`, and say so in the plan. Credibility matters more than adoption.

## Design rules

- **States are named after what the user/system is doing**, in domain language: `reviewing`,
  `uploading`, `awaitingPayment` — not `state1`, not `loadingTrue`. Prefer the vocabulary already in
  the codebase and behavior map.
- **Context vs. states**: finite modes → states; unbounded data (form values, fetched items, retry
  counts) → context. If you find yourself encoding data in state names (`retry1`, `retry2`), it's a
  context counter with a guard.
- **Every side effect becomes an actor or an action.** Invoked actors for effects tied to a state's
  lifetime (auto-cancelled on exit — this is how the machine fixes the "setState after unmount" class
  of bug for free; note where that applies). Spawned actors for effects that outlive states. Fire-and-
  forget (analytics, logging) → actions.
- **Guards carry the business rules** (`retries < MAX`, `isValid`). Name them meaningfully; each
  guard traces back to a condition in the behavior map.
- **Impossible states must be unrepresentable.** For each impossible-but-representable combination
  in the behavior map, show which aspect of the design eliminates it. That table is the migration's
  clearest payoff and belongs in the plan.
- **Divergences are explicit.** Anywhere the model forbids something the code allowed (or handles
  something the code dropped), list it under "Behavioral divergences" — each becomes an interview
  question in Phase 3. Default posture: preserve behavior, surface bugs, let the user choose.

## `state-model.md` structure

```markdown
# State Model — {TARGET_SLUG}

## Recommendation
{flat machine | statechart | actors} because {one paragraph, grounded in the behavior map}.
If "not XState", say so here and stop the design at a sketch.

## Statechart
​```mermaid
stateDiagram-v2
  [*] --> idle
  idle --> submitting: SUBMIT
  ...
​```

## States
| State | Meaning | Entry/exit actions | Invoked actors | From behavior-map states |

## Events
| Event | Payload | Sent by (user/system) | Handled in |

## Context
Typed shape with initial values; note which behavior-map variables land here vs. became states.

## Guards & actions
| Name | Logic | Traces to (behavior-map condition, file:line) |

## Actors
| Actor | Kind (fromPromise/fromCallback/spawned machine) | Wraps (effect from inventory) | Lifecycle |

## Impossible states eliminated
| Old combination | Why it was possible | How the model forbids it |

## Behavioral divergences (need user confirmation)
| # | Old behavior | New behavior | Why |

## UI coverage matrix (draft)
{per references/ui-coverage.md — every state × UI, gaps marked ⚠}

## Open questions
```

## Mermaid discipline

The diagram is the artifact most users actually read. Keep it accurate to the tables (same state
names, all transitions present), use `note` annotations sparingly for guards, and for parallel/
hierarchical models show composite states properly (`state active { ... }`). If the machine exceeds
~15 states, add a second, simplified overview diagram above the full one.
