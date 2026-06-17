# Phase 2 — Codebase Grounding

This is the differentiator. The video is of *this* repo, so connect every observed component to the
real source behind it. Skip this phase entirely if `--no-ground` was passed.

## Step 1 — Extract grounding anchors

Read `{ANALYSIS_DIR}/observed-ui-map.md` and `{ANALYSIS_DIR}/issue-summary.md`. Build a worklist of
**grounding targets** — one per distinct UI surface that a candidate ask touches. For each target,
collect the anchors that a code search can match:

- Exact on-screen text (button labels, headings, menu items, placeholder text) — the highest-signal
  anchor; UI strings usually appear verbatim in source or i18n files.
- Error / empty-state messages shown on screen.
- Route paths seen in the URL bar (`/settings/billing`).
- Likely component names implied by the UI (a "Date range" picker → `DateRange*`, `*Picker`).
- Data/field names visible in tables or forms.

Group targets by candidate ask so grounding results line up with what the user will confirm in Phase 3.

## Step 2 — Launch parallel grounding agents

Launch one `Explore` agent per grounding target, all in a single response (parallel). Each agent is
read-only and returns `file:line` evidence. Give each a focused prompt:

```
Agent type: Explore
Prompt: |
  In this repository, locate the source behind a UI element observed in a screen recording.

  Observed element: <type + on-screen label, e.g. "a 'Reset filters' button in the dashboard header">
  Anchors to search for (exact, case-sensitive first, then loosened):
    - "<exact on-screen string 1>"
    - "<exact on-screen string 2>"
    - route: <path if any>
    - likely component name pattern: <e.g. *FilterBar*, *Reset*>

  Do this:
    1. Grep for each exact string (and its i18n key form). Strings shown in the UI usually appear
       verbatim in a component, a constants/i18n file, or a test.
    2. From the match, trace to the component that renders this element; note the file and the line
       where the element + its handler/state live.
    3. Glob for component files whose names match the likely pattern.
    4. If the element has an event handler or bound state, locate that too (the bug usually lives there).

  Return, as a compact list:
    - Best-match source: <file:line> — what it is — confidence (high/med/low) — the anchor that matched.
    - Secondary candidates: <file:line> each, with why.
    - Handler/state location if separate: <file:line>.
    - If nothing matched: say so plainly and list what you searched.
  Do not edit anything. Citations must be real file:line from this repo.
```

Wait for ALL grounding agents to finish before Step 3.

## Step 3 — Synthesize `{ANALYSIS_DIR}/component-source-map.md`

Merge the grounding results into one table-driven document, organized by candidate ask:

For each ask, list its components and for each component:

| Observed component | Anchor that matched | Source (`file:line`) | Handler / state (`file:line`) | Confidence | Notes |
|--------------------|---------------------|----------------------|-------------------------------|------------|-------|

Then a **Resolution summary**:
- `{N}` components grounded with high/medium confidence.
- `{N}` unresolved or low-confidence — list each; these become confirmation questions in Phase 3
  ("I couldn't find the X component — is it in `<dir>`, or is this a new screen?").
- Any signal that the video may not match the current repo (nothing resolves, routes don't exist) —
  flag it loudly; the plan should not pretend to know where code lives.

Report: `Phase 2 complete. {N}/{M} components grounded; {K} need confirmation`.
