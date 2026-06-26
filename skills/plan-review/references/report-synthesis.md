# Phase 4 — Report Synthesis

Goal: assemble the validated state into one **read-only** review the author can act on. The original
artifact is never touched — you write a new report next to it. Improvements are *recommended*, not
applied.

## Inputs

- `artifact-map.md` — the decomposition (tasks, claims, acceptance criteria).
- `grounding-map.md` — what's real vs. contradicted vs. unresolved.
- `findings.md` — the severity-rated findings (post-adversarial on `deep`).
- `interview-answers.md` — the validated, prioritized, source-of-truth decisions.

When `interview-answers.md` exists, it **overrides** raw findings: dismissed findings move to
"considered & dismissed", confirmed ones take the user's priority, resolved ambiguities become
decisions. If the interview was skipped, use the model ranking and mark findings `UNVALIDATED`.

## Compute the readiness verdict

One line at the top, from the validated findings:

- 🔴 **Not ready** — one or more confirmed **blockers**. Building now risks broken/unsafe/wrong work.
- 🟡 **Needs revisions** — no blockers, but confirmed **major** gaps that should be closed first.
- 🟢 **Ready** — only minor items, or none. Safe to build; note the polish.

Be honest and proportional. A solid plan should read 🟢 with a short list — don't manufacture yellow.

## Assemble from the template

Use `assets/templates/review-report.md`. Fill every section; drop a section only if it's genuinely
empty (e.g. no third-party items), and say "none" rather than deleting silently where the reader would
expect it. Hard rules:

- **Every finding cites its evidence** — the artifact quote *and*, where grounded, the `file:line`.
  This is what lets the author judge the call. A finding without evidence shouldn't be in the report.
- **Lead with strengths.** Name what the plan gets right, specifically. It's not flattery — it tells
  the author what *not* to touch, and a review that only lists problems gets dismissed as nitpicking.
- **Keep gaps / improvements / errors visibly distinct** (the three kinds). The author responds to
  each differently: fix an error, fill a gap, consider an improvement.
- **The gap register** (`assets/templates/gap-register.md`) is the at-a-glance, color-coded
  (🟢🔵🟡🔴⚪🟣) table of every open item with an owner column — the artifact author's action list.
- **The "definition of ready" checklist** is the close: the concrete boxes that, once ticked, flip the
  verdict to 🟢. Make them checkable and specific, derived from the confirmed P0/P1 findings.

Write to `{OUT_DIR}/{ARTIFACT_SLUG}-review.md`. **Do not modify `{ARTIFACT_PATH}`.**

## Offer the follow-up (don't assume it)

This skill stops at the review. If the findings clearly warrant it, end by offering — not doing — the
next step:

> "This review is read-only; your plan is unchanged. Want me to apply the P0 fixes into a revised
> copy (`{slug}-v2.md`, original kept), or open the first blocker as a task?"

Let the user choose. Silently rewriting their plan is exactly the surprise this skill is designed to
avoid.

## Wiki ingestion (if a vault exists)

If `{PROJECT_DIR}/wiki/` exists, honor the wiki-first mandate:

1. Ingest the review as a `report`-type page (or run `/wiki:ingest-document` on the written file).
2. Cross-link it to the source artifact and any feature/decision pages the findings touch.
3. Append a row to `wiki/_log.md` describing the review (artifact, readiness, finding counts).

Defer the heavy lifting to the `/wiki:*` commands; don't reimplement them here.

## Final step

Print the Final summary block from `SKILL.md` with per-file status and the readiness verdict, and
confirm in one line that the original artifact was not modified.
