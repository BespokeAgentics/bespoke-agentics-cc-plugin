# Phase 2 — Codebase Grounding

Skip entirely if `--no-ground`.

This is what separates a real highlight reel from a guessed-at voiceover. The demo is of *this*
repo, so connect every demonstrated feature to the real source behind it. Grounded narration can
say **what the feature actually does** ("this pulls all four panels in a single GraphQL query")
instead of vibes ("the dashboard loads fast"). It also catches the case where the video doesn't
match the current code — so you don't narrate a lie.

## Step 1 — Build grounding targets

Read the **Distinct features** list and the `onscreen_text` anchors from `moment-catalog.md`. Make
one grounding target per distinct feature. For each, collect anchors a code search can match:

- Exact on-screen strings (button labels, headings, empty/error messages) — highest signal; UI text
  usually appears verbatim in a component or i18n file.
- Route paths seen in the URL bar.
- Likely component/function names implied by the feature ("bulk export" → `*Export*`, `useExport`).
- Field or entity names visible in tables/forms.

## Step 2 — Launch parallel grounding agents

One `Explore` agent per feature, all in a single response. Read-only; each returns `file:line`.

```
Agent type: Explore
Prompt: |
  In this repository, find the source that implements a feature shown in an app-demo recording.

  Feature: <feature name, e.g. "dashboard metrics load in one call">
  On-screen anchors (search exact first, then loosen):
    - "<exact string 1>"
    - "<exact string 2>"
    - route: <path if any>
    - likely name pattern: <e.g. *Dashboard*, useMetrics, /api/metrics>

  Do this:
    1. Grep each exact string (and its i18n-key form). Trace the match to the component/handler.
    2. Identify the entry point that implements the feature's behavior (the data fetch, the mutation,
       the computation) — that's what the narration will describe.
    3. Note anything narration-worthy and TRUE: single vs N+1 queries, caching, optimistic update,
       permission check, debounce, batch size, etc.

  Return, compact:
    - Feature entry point: <file:line> — what it does — confidence (high/med/low) — anchor matched.
    - Supporting source: <file:line> each (the fetch/mutation/util the feature relies on).
    - One or two TRUE, specific facts a voiceover could state about how it works.
    - If nothing matched: say so plainly and list what you searched.
  Do not edit anything. Every citation must be a real file:line from this repo.
```

Wait for ALL grounding agents before Step 3.

## Step 3 — Synthesize `{ANALYSIS_DIR}/feature-source-map.md`

One row per feature, organized to line up with the moment catalog:

| Feature (moment #) | Anchor matched | Entry point (`file:line`) | Supporting (`file:line`) | Narration-worthy facts (verified) | Confidence |
|--------------------|----------------|---------------------------|--------------------------|-----------------------------------|------------|

Then a **Resolution summary**:
- `{N}` features grounded high/medium — narration for these may state the verified facts.
- `{N}` unresolved / low-confidence — narration for these stays descriptive (no invented internals);
  flag them so Phase 4 doesn't over-claim.
- **Repo-mismatch signal**: if little or nothing resolves (routes absent, strings not found), say so
  loudly. The reel can still be made, but narration must be surface-level and the summary must warn
  that it is not code-verified.

Rule for Phase 4: a narration beat may state a technical fact **only** if it traces to a
high/medium-confidence row here. Everything else is described from what's visibly on screen.

Report: `Phase 2 complete. {N}/{F} features grounded; {K} unresolved`.
