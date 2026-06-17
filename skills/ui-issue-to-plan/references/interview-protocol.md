# Phase 3 — Interview (the elicitation gate)

The user recorded a video instead of writing a ticket because the intent is easier to *show* than to
*spell out*. Your analysis has turned the showing into structured guesses; this phase turns the
guesses into a confirmed spec. Ask grounded questions, not open-ended ones — you already know what's
on screen and where it lives in the code, so questions should sound like "you're pointing at the
date picker in `Header.tsx:42` — fix its alignment, or change its reset behavior?".

Use the **AskUserQuestion** tool. Max 4 questions per call; multiple calls are fine. Phrase options
from what the analysis actually found, and offer your best inference first (mark it "(Recommended)"
only when confidence justifies it). Always allow the user to add their own answer (the tool's "Other"
option is automatic) — they know the intent better than the pixels do.

## Step 0 — Print the digest first (text, not a question)

Before any question, print a tight digest so the user sees you understood the video:

```
Here's what I saw in the recording:
  • Screens: <list>
  • The issue, as I understood it: <1–2 sentences from issue-summary.md>
  • Candidate asks:
      1. <title> — <kind> — likely lives in <file:line>
      2. ...
  • Couldn't ground: <component(s) needing confirmation>
```

If narration was missing (no transcript), say so and note you'll lean on these questions to capture intent.

## Round 0 — Frame the intent (the altitude beat)

People record a walkthrough because the experience is easier to *show* than to spell out — so before
narrowing in on the defect, find out how far they want to go. **Skip this round only if `--mode` was
passed explicitly** (it already sets the altitude). Otherwise, one question:

> **"Is this strictly a fix, or do you also want to improve the experience here?"**
> Options: *Just fix what's broken* · *Fix it AND improve the flow (Recommended when the video shows
> aspiration)* · *Mostly about improving — the bug is secondary*.

If they choose anything but "just fix," ask one aspirational follow-up to anchor the vision:

> **"What's the ideal end-state for this flow?"** — seed the options from the `Vision & aspirational
> statements` in `issue-summary.md` (e.g. "AI status is visible app-wide, with progress + the ability
> to cancel"), always leaving room for their own words.

Record the chosen altitude as the **effective mode**. "Just fix" → behave as `MODE == fix` for the
rest of the interview (no opportunities round; opportunities, if any were synthesized, are listed as
*deferred* in the plan, not dropped). Otherwise the opportunities round (Round E) runs.

## Round A — Confirm the asks

One multiSelect question: **"Which of these did you want to address?"** Options are the candidate
asks from `issue-summary.md`, each with a one-line description naming the component and kind.
Unselected asks are out of scope — record them as dropped. If there's only one ask, still confirm it
(single-select yes / not-quite / something-else) so you don't build the wrong thing.

## Round B — Clarify each confirmed ask

For each confirmed ask, ask the load-bearing questions (batch up to 4 across asks where sensible):

1. **Nature of the change** — when `kind` is uncertain: "Is this a bug fix, a behavior change, or a
   new feature?" Options framed from the evidence.
2. **Desired outcome / acceptance** — "What should happen instead?" Offer the inferred readings from
   `issue-summary.md` as concrete options (e.g. "Reset should clear all four filters AND refetch" vs
   "Reset should clear filters but keep the current page"). This is the single most important
   question — it defines "done".
3. **Scope edges** — only when relevant: should the change apply everywhere this component is used, or
   just the screen in the video?

## Round C — Confirm grounding

For every component flagged unresolved or low-confidence in `component-source-map.md`, ask one
confirmation question: "I think the X lives in `<file>` — is that right?" with the secondary
candidates as options plus "it's somewhere else (tell me)" and "it doesn't exist yet (new code)".
Skip this round entirely if everything grounded with high confidence.

## Round D — Priority, sequencing & constraints

1. If more than one ask is confirmed: "Which is P0 (do first)?" — multiSelect; the rest default P1.
2. "Any constraints I should respect?" — offer common ones as options: must match an existing design /
   don't touch shared component X (other screens depend on it) / keep the current API contract / no
   new dependencies / accessibility must hold. Leave room for free-text.

## Round E — Opportunities (enhancements)

Run this **only** when the effective mode allows improving (Round 0 wasn't "just fix", and `MODE`
isn't `fix`) and `opportunities.md` exists with at least one item. This is where the skill earns its
keep — surfacing the improvements the user couldn't easily articulate.

Present the curated proposals from `opportunities.md` (each already grounded to a `file:line`), then:

1. **Pick the enhancements** — one multiSelect: "Beyond the fixes, here's what I'd consider improving
   — which do you want in scope?" Options = the proposals, each with its one-line value + landing spot.
   Unselected ones are recorded as *deferred* (kept in the plan's deferred list, not deleted).
2. **Prioritize the chosen ones** — enhancements get their own P0/P1/P2, **separate from the fixes**
   (an enhancement is opt-in; never let it outrank a defect unless the user explicitly says so).
3. Clarify depth only where a selected enhancement has a meaningful fork (e.g. "ETA: rough elapsed
   timer vs. real estimate?") — keep this light.

Keep fixes and enhancements visibly distinct throughout — the user is choosing to *expand* scope here,
and they should always be able to see what's a must-fix vs. a nice-to-have.

## Persist the answers

Write `{ANALYSIS_DIR}/interview-answers.md` as the contract Phase 4 builds from, in **two clearly
separated buckets**:

- `## Confirmed fixes` — per confirmed defect ask: validated outcome / acceptance criteria, confirmed
  source location(s), `kind`, priority, constraints.
- `## Confirmed enhancements (opt-in)` — per selected opportunity: the improvement, its grounded
  landing spot, acceptance, priority. Empty when fix-only — say so explicitly.
- `## Deferred` — dropped asks and un-selected opportunities (so they're visible, not lost).

Phase 4 must not introduce requirements that aren't in the first two buckets.

Report: `Phase 3 complete. {N} fixes + {N} enhancements confirmed, {N} deferred, {N} constraints`.
