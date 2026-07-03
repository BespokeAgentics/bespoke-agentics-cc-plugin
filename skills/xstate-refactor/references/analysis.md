# Phase 1 — Behavior Discovery

Goal: recover the statechart the code already implements, with evidence. The output,
`behavior-map.md`, is the ground truth every later phase builds on. If it's wrong, the migration is
a rewrite; if it's right, the migration is a translation.

## What "state" means here

The implicit state of a feature is the cross-product of everything that changes its behavior:

- **State variables**: `useState`/`useReducer` values, class fields, module-level `let`, store slices
  (Redux/Zustand/Jotai/context), refs used as flags (`isMountedRef`, `hasFetchedRef`).
- **Derived conditions**: every distinct boolean expression that gates behavior
  (`isLoading && !data`, `retries < 3`, `status === 'draft' || status === 'review'`).
- **In-flight effects**: pending promises, active timers/intervals, open sockets/subscriptions,
  AbortControllers — these are states even when no variable names them.
- **External state the feature reads**: URL params, localStorage, feature flags — record them as
  inputs (future machine `input`/context), not states.

## Launch the discovery agents

Launch in parallel (single response, multiple Agent calls), all `Explore` type, all read-only:

1. **State inventory agent** — every state variable and derived condition in the target files, each
   with `file:line`, type, initial value, and every write site. Have it explicitly enumerate the
   representable combinations of boolean/enum flags and mark which combinations the code guards
   against vs. which are reachable but unhandled.
2. **Event & effect agent** — every way state changes: user events (handlers), system events
   (promise resolution/rejection, timers, subscriptions, prop changes, route changes), and the side
   effects each triggers (fetches, mutations, navigation, analytics). For each: trigger → state
   writes → effects, with `file:line`.
3. **UI dependency agent** — every render decision keyed on state: conditional JSX, ternaries,
   early returns, `disabled`/`aria-*`/`className` toggles, portal/modal mounting, spinner/skeleton/
   toast triggers. For each: which state condition drives it, what the user sees, `file:line`. Also
   sweep *outside* the target files for consumers: components that receive this state via props or
   read the same store slice — the migration's blast radius.

Scope note: if the target is one component, agents 1–2 stay within it plus its custom hooks; agent 3
always sweeps consumers. If the target is a flow spanning files, give each agent the full file list.

## Synthesize `behavior-map.md`

You write this yourself from the agents' reports. Structure:

```markdown
# Behavior Map — {TARGET_SLUG}

## Target files
{list with one-line role each}

## State inventory
| Variable/condition | Kind | Initial | Written at | Notes |

## Implicit states
The distinct behavioral modes the code actually has. Name them provisionally
(idle / submitting / retrying...). For each: the flag combination that means it,
its UI (from agent 3), and file:line evidence.

## Impossible-but-representable states
Flag combinations the types allow but the logic never intends
(e.g. isLoading && isSuccess). For each: reachable in practice? (trace a path or
mark "unreachable but unguarded"). These become interview questions.

## Events & transitions
| From (implicit state) | Trigger | To | Side effects | Evidence |

## Side-effect inventory
Every effect with lifecycle notes: cancelled on unmount? raceable? retried?
(These become invoked/spawned actors.)

## UI touchpoints
| State/condition | UI element | What user sees | file:line |
Include consumers outside the target files.

## Inputs (external reads)
URL/store/flags/props feeding the logic — future machine input/context.

## Untraced paths & open questions
Anything you could not follow (dynamic dispatch, opaque store logic). Never guess.
```

## Quality bar

- Every claim carries `file:line`. No evidence → it goes under open questions, not in the map.
- Enumerate honestly: if 4 booleans give 16 combinations and only 5 are meaningful, say so — that
  gap *is* the argument for the migration, and Phase 2 turns it into the machine's shape.
- Record what the code *does*, including bugs. A setState-after-unmount warning path or a double-
  submit race is a finding to surface, not to silently fix. The user decides in Phase 3.
