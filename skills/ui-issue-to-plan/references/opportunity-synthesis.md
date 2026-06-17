# Phase 2.5 — Opportunity Synthesis

A person records a walkthrough instead of writing a ticket because they're *thinking out loud about
the experience* — not just reporting a defect. The defect is the entry point; the real intent is
often "I want this to feel better." This phase turns what was observed into a **curated, grounded
set of improvement opportunities** the user can opt into, so the plan elevates the experience instead
of only patching the bug.

Skip this phase entirely if `--mode fix`. Otherwise run it after grounding and before the interview
(its output seeds the interview's opportunities round).

## Inputs

- `{ANALYSIS_DIR}/observed-ui-map.md` — the screens/components and their states.
- `{ANALYSIS_DIR}/issue-summary.md` — the defect asks **plus** the `Vision & aspirational statements`
  and `Opportunity signals` sections (the narrator's "we should be able to…" and the on-screen friction).
- `{ANALYSIS_DIR}/component-source-map.md` — real `file:line` for the surfaces involved.

## What to produce — `{ANALYSIS_DIR}/opportunities.md`

A **curated 3–5** improvement proposals. Curation is the point: this is not a brainstorm dump. Each
proposal must clear two bars or it's cut:

1. **Grounded** — it lands at a real `file:line` (or a clearly named new file beside real ones), not
   "somewhere in the app."
2. **High-relevance** — it serves the flow the user actually demonstrated or the vision they voiced.
   No generic filler ("add dark mode", "use a design system") unless the video genuinely points there.

For each proposal record:

- `id` — slug (e.g. `opp-1-progress-eta`).
- `title` — one line.
- `class` — **Restore** (bring back something that regressed — usually already a fix ask, cross-ref it)
  vs **Enhance** (net-new improvement beyond the reported issue). Keep these visibly separate.
- `trigger` — what prompted it: an observed component + frame/quote, or an on-screen friction signal,
  or a verbatim aspirational statement from the narration.
- `proposal` — the enhancement, stated concretely as a change to the experience.
- `lands at` — grounded `file:line` (from `component-source-map.md`) where it would be implemented.
- `effort` — rough S / M / L.
- `value` — why it matters to *this* flow (tie to the user's vision when they stated one).

End with a one-line **coverage note**: how many Enhance proposals, and an honest "nothing beyond the
fixes rose to high-value" when that's the truth (don't pad to hit 3 — a terse bug video may yield zero).

## Calibrate — don't nag

- The bar is *relevance to the demonstrated flow*. A 20-second "this button is the wrong color" clip
  should surface 0–1 opportunities, not 5. A 3-minute walkthrough where the narrator describes a
  desired system (like an app-wide AI activity indicator) should surface the full 3–5.
- Prefer proposals that share the fix's blast radius (same files/components) — they're cheap to land
  alongside the fix and read as "while we're in here, we could also…".

## Borrow archetype heuristics (lightweight)

Match the demonstrated UI to a known archetype and pull from its proven moves — you may consult the
sibling `ux-audit` / `ai-waiting-ux` skills' thinking for the relevant archetype:

- **AI / long-running in-progress** → live progress %, ETA / elapsed, cancel + retry, optimistic UI,
  a persistent/global activity center, completion + failure surfacing, graceful degradation on timeout.
- **Forms / multi-step** → inline validation, autosave + restore, progress stepper, keyboard flow.
- **Tables / lists** → empty/loading/error states, bulk actions, sort/filter persistence, density.
- **Navigation / shell** → state retention across routes, deep-linkability, breadcrumb/return affordances.

Use these as a checklist to *notice* opportunities, then keep only the grounded, high-relevance few.

Report: `Phase 2.5 complete. {N} opportunities ({R} restore, {E} enhance) grounded` (or `0 — nothing high-value beyond the fixes`).
