# Run state — formats & resume rules

Everything under `{RUN_DIR}` exists so a run can survive context compaction, a session restart, or
a user interrupt. Write state transitions **as they happen** — a state file that's updated in
batches at the end protects nothing.

```
{PROJECT_DIR}/.orchestrate/{RUN_SLUG}/
├─ work-order.md        # grounded phases, owners, anchors, gates (written at end of Phase 0)
├─ state.md             # phase/item statuses + run facts (updated continuously)
└─ reports/             # one verbatim subagent return per file
   ├─ ground-{cluster}.md
   ├─ wave1-{item}.md
   ├─ smoke.md
   └─ review.md
```

Add `.orchestrate/` to the project's ignore file if it isn't ignored (one line in `.git/info/exclude`
is enough — don't edit a tracked `.gitignore` uninvited).

## state.md

```markdown
# Orchestration state: {RUN_SLUG}
plan: {PLAN_PATH}
branch: {branch}
base_ref: {BASE_REF}
depth: {DEPTH}
flags: {flags passed}
preexisting_dirt: |
  {verbatim `git status --short` from pre-flight}
gates:
  - {command}            # discovered at pre-flight
model_substitutions: {none | "opus unavailable → inherit"}

## Phases
| phase | status | notes |
|---|---|---|
| P plan-draft | done/skipped | {plan path} |
| 0 ground     | done | {N anchors, N contradictions} |
| G0 confirm   | done | {user decisions, verbatim-short} |
| wave 1       | in-progress | |
| ...          | pending | |
| S smoke      | pending | |
| R review     | pending | |
| W close-out  | pending | |

## Items
| item | wave | model | status | fix round-trips | report |
|---|---|---|---|---|---|
| B-spine | 1 | opus | done | 1 | reports/wave1-b-spine.md |

## Decisions & arbitrations
- {timestamped-by-phase: what was decided, by whom (user at G0 / orchestrator arbitration), why}

## Gate log
| when (phase) | command | result | failure routed to |
|---|---|---|---|
```

Statuses: `pending | in-progress | done | failed | skipped`. An item enters `in-progress` when its
packet is sent, `done` only when its wave's gates pass.

## work-order.md

```markdown
# Work order: {RUN_SLUG}
## Waves
| wave | item | model | may edit | must not touch | gate |
|---|---|---|---|---|---|

## Corrected anchor map
{merged grounder output — the single source implementers are packeted from}

## Contradictions & G0 resolutions
| plan said | code shows | resolution (user/orchestrator) |

## Interfaces
| publisher item | consumer item(s) | signature (verbatim once published) |

## Plan-specific guardrails
{the hard rules extracted from the plan + repo CLAUDE.md, verbatim — appended to every packet}
```

## Resume rules

1. Re-run pre-flight steps 2–4 fresh (branch, conventions, plan) — the repo may have moved.
   `BASE_REF` **and** `preexisting_dirt` come from state, never recomputed: dirt recorded at the
   original pre-flight stays protected, and any current dirt beyond it is the interrupted run's
   own in-flight work (rule 2), not user changes to preserve.
2. Diff reality against state: if `git status` shows edits to files owned by an `in-progress` item,
   assume its agent partially applied work — respawn it with its packet **plus** its prior report
   (if any) and a note of which of its files already contain changes, instructing it to reconcile
   rather than redo.
3. `done` phases/items are skipped on their state alone — do not re-verify their gates unless a
   later gate fails.
4. A phase marked `failed` resumes at its fix round-trip with the recorded gate log entry, not from
   scratch. Round-trip counts persist — 2 recorded round-trips means the next failure goes to the
   user, even across sessions.
5. G0 decisions are durable: never re-ask a question `state.md` records an answer to.
6. If `work-order.md` is missing but reports exist, the run is corrupt — tell the user and offer
   `--force`.
