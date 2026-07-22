# Phase 1 — Structural grounding

Read before Phase 1. The job: for every decided element in `intended-model.md`, find where the **implementation** realizes it (`file:line`) and mark it honored / drifted / missing. This is code-vs-decision parity — it runs even under `--no-browser`, and it is where the "did we build what we settled" answer comes from.

## Why this is the floor

Measured parity (Phase 2) proves the *rendered result* matches; grounding proves the *code implements the decision*. A build can render correctly today and still have silently dropped a decided behaviour that only shows in a state you couldn't reach. Grounding catches that — and it is the only pass available when no app is running.

## Launch parallel Explore agents

Cluster the intended model into 2–5 groups (fewer on `quick`, more on `deep`) — e.g. one per structural region, one for the decisions, one for the states/roles, one for labels/enums. Launch one `Explore` agent per cluster **in a single response**. Give each agent:

- the relevant slice of `intended-model.md` (the decisions/contract/states/labels it owns),
- the grounding cache's `Surface anchors` and token/label rows (the bridge from wireframe vocabulary to real `path:line`),
- `APP_URL`'s route, if known, as a hint to the component that renders it.

Each agent returns, per item:

| Item | Locate | Mark |
|---|---|---|
| **Decision** ("flat rail, no accordions") | the component/prop/branch that implements the chosen behaviour | `honored` (code does the settled thing) · `drifted` (code does a variant) · `missing` (no implementation found) — each with `file:line` |
| **Contract invariant** ("one sticky element") | the DOM/CSS structure that would satisfy or break it | honored / at-risk / broken, with the `file:line` that decides it |
| **State** (role × entity) | the conditional render / permission gate for that state | implemented / partial / missing |
| **Label / enum** ("Internal Review") | the string constant or i18n key the UI renders | matches / stale / hardcoded-differently |

And the payoff question every agent must answer: **"what did the build likely MISS vs. the decided design?"** — a decided empty-state with no implementation, a role branch that renders the same as another, a label map that still shows the raw enum.

## Grounding rules

- **Never fabricate a `file:line`.** If an element can't be located, that is itself a finding ("Decision D4 — the disclosure-remembers-state behaviour — no implementation found; searched `useDisclosure`, `localStorage`, the panel component"). An unfindable decision is a likely `missing`.
- **Distinguish drift from evolution here only structurally** — whether the code does *a* thing vs. *the decided* thing. Whether a drift is an acceptable evolution is the interview's call (Phase 3), not the agent's.
- **Cite both sides.** Every row carries the intended reference (decision id / spec §) and the as-built `file:line`.
- Optional accelerator: Rig MCP tools (`rig_search`, `rig_callers`, `rig_impact`, `rig_node`) seed the work-list — never a dependency; plain Explore is the baseline.

Synthesize all agents into `{ANALYSIS_DIR}/grounding-map.md`: one section per cluster, a table of `item · verdict · intended ref · file:line · note`, then a "likely missed" list. This map + the measured diff are what Phase 3 interviews over.
