# Phase 4 — Plan Synthesis

Assemble the validated state into a single implementation plan a developer (or another Claude
session) can execute. Every claim should trace to either a frame (what was shown) or a `file:line`
(where it lives) — this is what separates a grounded plan from a vague to-do list.

## Inputs

- `{ANALYSIS_DIR}/interview-answers.md` — the contract. Build ONLY the confirmed asks; honor every
  recorded constraint and priority. Do not add requirements that aren't here.
- `{ANALYSIS_DIR}/issue-summary.md` and `observed-ui-map.md` — for evidence (quotes, frame timestamps).
- `{ANALYSIS_DIR}/component-source-map.md` — for the affected source files.

## Derive the slug (if not provided)

If `ISSUE_SLUG` is empty, derive it from the primary (P0) confirmed ask's title — kebab-case, short,
e.g. `filter-dropdown-reset`. Reuse this exact slug for the filename.

## Write `{OUT_DIR}/{ISSUE_SLUG}.md`

Use the template at `assets/templates/implementation-plan.md`. Fill it from the validated state:

- **Context** — the problem in plain language (from the narration + validated intent), why it matters,
  and the intended outcome. Cite the source video.
- **Observed UI & evidence** — per ask, the component(s) involved, the frame timestamp(s) where the
  issue is visible, and the narrator's verbatim quote. This lets a reader re-watch the exact moment.
- **Affected source files** — the grounded `file:line` list from `component-source-map.md`, including
  handler/state locations (where the fix usually lands). Mark any unconfirmed location as such.
- **Proposed changes** — per confirmed ask, in priority order: what changes, in which file, and how
  (the approach — not necessarily the final diff). State acceptance criteria from the interview.
- **Task checklist** — ordered, actionable `- [ ]` items a developer can work through. Each task names
  its file(s). Keep tasks small enough to verify individually.
- **Open questions & assumptions** — anything deferred in the interview, any low-confidence grounding,
  and assumptions made when narration was missing.
- **Verification** — how to confirm the fix end-to-end: how to run the app, what to click, and what
  the correct behavior looks like (the acceptance criteria, made concrete). Reference the original
  frame so "before" is unambiguous.

Keep it scannable: a developer should grasp the change in 60 seconds and have the file pointers to
start immediately.

## Wiki integration (only if a `wiki/` vault exists)

Per the project's wiki-first mandate:
1. Ingest the plan: `/wiki:ingest-document '<plan-path>' spec` (or read `wiki/_schema/SCHEMA.md` and
   create a spec/task page that links to the plan and the source video).
2. Add cross-references to any related feature/gap pages.
3. Append an entry to `wiki/_log.md` recording the ingest.

Skip silently if there is no wiki.

## Done

Print the final summary block (defined in SKILL.md) with the plan path marked as the primary output.
Offer the obvious next step: "Want me to start implementing the P0 task?" — but do not begin editing
code unless the user says yes; this skill's job ends at a validated plan.
