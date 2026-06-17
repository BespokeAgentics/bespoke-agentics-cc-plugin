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

## Persist the answers

Write `{ANALYSIS_DIR}/interview-answers.md` capturing, per confirmed ask: the validated outcome /
acceptance criteria, the confirmed source location(s), `kind`, priority, and any constraints; plus the
list of dropped asks. This file is the contract Phase 4 builds the plan from — Phase 4 must not
introduce requirements that aren't in it.

Report: `Phase 3 complete. {N} asks confirmed, {N} dropped, {N} constraints recorded`.
