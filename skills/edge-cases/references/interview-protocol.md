# Phase 3 — Deciding expected behavior

The interview exists for one thing: **expected behaviors that are product decisions**. Code can tell
you what the system does. Only the user can say what it should do where reasonable products differ.
Do not ask about anything the evidence already answers.

It runs right after consolidation and **before** any verification (Phases 4–5). A decision can
rewrite `then`. Skeptics and probes must judge the code against the expectation the user chose, not
against one they later replaced.

## Who gets asked

Only cases with `expected_source: "proposed"` and `decision: "needed"`. Not asked:

- `spec` and `convention` cases: the source already answered.
- `uncontested` proposals: any reasonable product would do it.
- Current-behavior questions: those are answered by reading code, skeptics and probes, never by
  asking.

If no case needs a decision, skip the phase and say so in one line.

## Before the first question

Print a digest so the questions have context:

```
{N} cases · P0 {a} · P1 {b} · P2 {c} · P3 {d}
{U} look unhandled in code (as read)                         (code targets)
{D} expected behaviors need a product decision — asking about the top {min(D,12)}
```

## Batching

- At most **4 questions per AskUserQuestion call** and **3 calls**: 12 decisions at most.
- Order by priority, then id. When more than 12 need deciding, the rest stay `needed`, and the report
  lists them under "Decisions needed".
- Header: the case id (`EC-07`).

## Question shape

Each question quotes the case, so it can be answered without opening the report:

```
EC-07 · Given SAVE10 was added to the cart before it expired, when the shopper checks out after
expiry — what should happen?
```

Options (2–4):

1. Your proposed behavior, labeled **(Recommended)**, with its one-line reason as the description.
2. One or two real alternatives a competent product team might choose, each with its trade-off. Store
   them on the case as `alternatives`; the report's "Decisions needed" table uses them for cases
   left undecided.
3. **Can't happen here**, for a condition the user knows is unreachable. The description asks them to
   say why in the notes.

The automatic "Other" option covers everything else, including "not sure yet".

## Applying answers

| Answer | Case update |
| --- | --- |
| The recommendation, or an alternative | `decision: "decided"`, `decision_note: "<the chosen behavior>"`; rewrite `then` to match the choice |
| Other, stating a behavior | `decision: "decided"`, `then` rewritten from their words, `decision_note` quotes them |
| Other, deferring ("not sure", "later", "ask X"), or no answer | `decision: "open"`, `decision_note: "<what remains open, and who decides>"` |
| Can't happen here | move the case to `dismissed` as `{id, title, reason}` |

A changed `then` can change severity (a decided "reject" may make a case low). Re-score it if so, then
re-run `check_cases.py --fill --repo {PROJECT_DIR}`.

If the interview is declined or `--no-interview` was passed, leave `needed` as it is. The report shows
each of those cases as **DECISION NEEDED**, never as a requirement. They are not probed and not
called defects.
