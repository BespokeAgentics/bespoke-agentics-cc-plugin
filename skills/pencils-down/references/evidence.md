# Evidence — what each source tells you, and the trap it sets

The collector (`scripts/collect_state.py`) emits pointers, not conclusions. This table is what to
do with each section of its output when building the feature ledger.

| Section | What it uniquely tells you | Trap |
|---|---|---|
| `plans` | What was *intended* — the feature list the project promised itself | A plan is intent. A feature that appears only here is `planned`, however confident the wording. Read the newest plan first; older plans record abandoned directions as readily as live ones. |
| `commits` | What actually landed, when, and in what order | Subjects describe the change, not whether the feature works. `feat: add export` may be a scaffold. Read the diff for anything you report as `done`. |
| `commits[].wip_marker` | Subjects containing WIP / stub / placeholder / draft | A strong `in-progress` or `stubbed` signal — but check whether a later commit finished it before labelling. |
| `branches` | Parallel work and how long it has sat | A branch stale > 30 days with a feature name is an `abandoned` candidate, and a go-live hygiene item either way. Never assume a branch's content from its name. |
| `uncommitted` | Work on one machine that is not on any branch | Label it. It is neither `done` nor safe to count. Ask the user whether it is live work or debris. |
| `wiki` | Decisions and context recorded alongside the code | The vault is the project's source of truth where it exists (Wiki-First Mandate) — but a decision page is a decision, not an implementation. Cross-check against commits. |
| `markers` | `TODO` / `FIXME` / `HACK` / `not implemented`, with `file:line` | Each `not implemented` inside a user-reachable path is a `stubbed` feature. Dense `TODO` clusters mark where distance-to-done is larger than the commit history suggests. Markers in tests or scripts are hygiene, not features. |
| `flags` | Feature-flag-shaped identifiers | Tells you a **Disable mechanism exists** — the single most useful fact for Step 4. Absence means every Disable needs its mechanism added (S) or falls back to route/nav removal. The regex is broad; `experimental` in a comment is not a flag system. |
| `tests` | Whether "tests green" can be a gate, and what command runs them | Count is not coverage. Zero tests is a go-live fact to state; a hundred tests on one module is not a safety net for the rest. |
| `ci` | Whether a default-branch gate exists | A workflow file is not a passing workflow. Check the last run if the tooling allows (`gh run list`), otherwise mark 🟡. |
| `go_live.inventory` | Which public-repo files exist | Existence ≠ adequacy. A 40-byte README is 🟡, not 🟢. Open each file before grading it. |
| `go_live.readme` | Headings and whether install / quickstart / license are mentioned | A README that mentions install is not one a stranger can follow. Step 6 says to actually follow it. |
| `go_live.env` | Env vars the code reads vs the ones `.env.example` declares | `used_but_undeclared` is a list of first-run failures for every new user. It is the most common 🔴 and the cheapest to fix. |
| `totals` | Headline counts | **Do not report them as findings.** "312 TODOs" is an anecdote; the ledger is the finding. |
| `notes` | What the collector could not read | These survive into the plan's Assumptions section verbatim. A gap smoothed over here is an assumption nobody labelled. |

## Reading order

1. `notes` — know the blind spots before forming a picture.
2. The newest two `plans` in full.
3. `commits` subjects in order, oldest to newest, to see the story; then diffs for the ones that
   decide a ledger row.
4. `markers` filtered to paths a user reaches (routes, handlers, UI components).
5. `flags`, to know whether Disable is cheap.
6. Everything else as the go-live checklist needs it.

## Fan-out

When the repository has more than roughly five distinct areas (apps, packages, services), send one
`Explore` agent per area with this ask, verbatim:

> List every user-recognisable feature or capability in `<area>`. For each: its state (`done`,
> `in-progress`, `stubbed`, `planned`) with `file:line` evidence; whether a flag, route, or nav
> entry controls its visibility; and the most recent commit that touched it. Report stubs
> (`not implemented`, empty handlers, placeholder UI) explicitly. Do not infer business purpose.

Merge the returns into the ledger. Where two agents report the same feature from different areas,
keep one row and both evidence sets.
