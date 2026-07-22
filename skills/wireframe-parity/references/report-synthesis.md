# Phase 4 — Report synthesis

Read before Phase 4. The job: assemble the validated state into one **read-only** parity report the team can act on. The implementation is never touched — you write a new report. Divergences are *reported*, not fixed.

## Inputs

- `intended-model.md` — the decisions, contract, states, frozen Verification numbers, labels.
- `grounding-map.md` — each decided element honored / drifted / missing, with `file:line`.
- `measured-parity.md` — per-state numeric diffs (or "not measured" reasons); absent under `--no-browser`.
- `interview-answers.md` — each divergence classified regression / intended-evolution / out-of-scope, prioritized. **Overrides** the raw verdicts. If skipped, use the default rule and mark findings `UNVALIDATED`.

## Compute the parity verdict

One line at the top:

- 🔴 **Diverges** — a settled Decision is not honored, or a Contract invariant is broken (confirmed regression). The build does not match what was decided.
- 🟡 **Minor drift** — no broken contract; drifts stay within decided intent, are cosmetic, are accepted intended-evolutions, or only unreachable states are unverified.
- 🟢 **Faithful** — every decision honored, every measured check within tolerance, nothing material unmeasured.

Be proportional. A faithful build reads 🟢 with a short list; don't manufacture yellow. Intended-evolutions do **not** lower the verdict — they are recorded, not counted against the build.

## Assemble from the template

Use `assets/templates/parity-report.md`. Fill every section; say "none" rather than deleting silently where the reader expects one. Hard rules:

- **Lead with strengths** — the decisions and measurements that match faithfully, named specifically. It tells the team what *not* to touch and stops the report reading as nitpicking.
- **The decision parity table is the heart.** One row per spec Decision: `# · Decision · Settled choice · As-built · Verdict · Evidence`. Verdict ✅ honored / ⚠️ drifted / ❌ diverged / ➖ not implemented. Evidence = decision id/spec § **and** `file:line` (+ measurement where relevant).
- **The measured parity table** carries the three-way numbers: `State · Region · Intended (wireframe) · Spec-frozen · As-built · Δ · Verdict`. Include the tolerance you used (±2px, same-AA) in the section intro so a Δ reads correctly.
- **Label & enum fidelity** is its own short section — the app-rendered string vs. the real label.
- **Keep the three classes distinct** in the divergence register: `regression` (a real parity gap to fix), `intended-evolution` (recorded, the wireframe is now stale), `unspecified` (out of scope). They call for different responses.
- **The divergence register** (`assets/templates/divergence-register.md`) is the at-a-glance color-coded (🟢🔵🟡🔴⚪🟣) action list with an owner column.
- **The "not measured" section is not optional** — list every state/check you couldn't reach and why. Honest coverage is the difference between a review and a rubber stamp.
- **The "definition of parity" checklist** closes it: the concrete boxes that, once ticked, flip the verdict to 🟢 — derived from the confirmed regressions.

Write to `{OUT_DIR}/{SLUG}-parity.md`. **Do not modify the implementation, the spec, or the wireframe.**

## Offer the follow-up (don't assume it)

This skill stops at the report. If regressions warrant it, end by offering — not doing — the next step:

> "This review is read-only; the implementation is unchanged. Want me to open the P0 regressions as tasks, or draft the fixes for the owning components?"

If the interview surfaced **intended evolutions**, also offer to refresh the source of truth:

> "Two divergences were intended improvements, so the wireframe is now stale. Want me to update the decisions ledger (`_library/decisions.md`) and the spec so the next parity run measures against the current design?"

Let the user choose.

## Wiki ingestion (if a vault exists)

If `{PROJECT_DIR}/wiki/` exists, honor the wiki-first mandate: ingest the report as a `report`-type page (or run `/wiki:ingest-document`), cross-link it to the spec + the decision/feature pages it touches, and append a row to `wiki/_log.md` (spec, app URL, parity verdict, regression count). Defer the heavy lifting to `/wiki:*`.

## Final step

Print the Final summary block from `SKILL.md` with per-file status and the parity verdict, and confirm in one line that the implementation was not modified.
