# Phase 6 — Report

Two files in `{OUT_DIR}`:

- `{SLUG}-edge-cases.md` — the report, built from `assets/templates/edge-case-report.md`.
- `{SLUG}-cases.json` — a copy of the final `cases.json`, for tooling and for turning cases into tests.

## Before writing

Run the final check. `--final` turns an unverified P0/P1 status at `deep` and `prove` into an error;
`--repo` re-checks every cited location:

```bash
python3 {SKILL_DIR}/scripts/check_cases.py {WORK_DIR}/cases.json --fill --final --repo {PROJECT_DIR}
python3 {SKILL_DIR}/scripts/check_cases.py {WORK_DIR}/cases.json --markdown {WORK_DIR}/matrix.md
python3 {SKILL_DIR}/scripts/check_cases.py {WORK_DIR}/cases.json --summary
```

`--markdown` renders the case matrix: paste it into the report unchanged. `--summary` prints every
tally the verdict line, the tables and the final summary block use (`by_priority`, `by_status`,
`by_origin`, `defects_p0_p1`, `verified_defects_p0_p1`, `confirmed_p0_p1`,
`undecided_unhandled_p0_p1`, `decisions`, `trimmed`, `dropped`). Never count cases by hand.

## Sections, in order

1. **Header** — target kind and spec, level (with `degraded_from` and its reason, if any), date,
   grounded, built.
2. **Verdict** — one line that leads with the most important fact. Use the first rule that is true:
   - code target with `verified_defects_p0_p1` → "{n} P0/P1 defects in the code ({c} confirmed by
     probe, the rest upheld by a skeptic). Start with EC-xx." For changes targets, split the count:
     "{i} introduced by this change, {e} pre-existing."
   - code target with `defects_p0_p1` that are not verified (`quick`/`standard`) → "{n} P0/P1 cases
     look unhandled (as read, not verified). Start with EC-xx."
   - expected behaviors still `needed` → "{n} expected behaviors need a decision before this is
     built (or fixed)." Mention `undecided_unhandled_p0_p1` here: those may be defects once decided.
   - otherwise → "No P0/P1 gaps found; {n} lower-priority cases listed."
3. **Top risks** — the P0/P1 cases, at most five shown in full (Given/When/Then, current status with
   evidence and verification), the rest by id and title. For changes targets, tag each case
   `(introduced)` or `(pre-existing)` and list the introduced ones first: they are what the reviewer of
   this change must act on. Pre-existing P0/P1 defects are still listed in full, never dropped.
4. **Decisions needed** — every case still `needed` or `open`: the question, the proposal, and its
   `alternatives`. Omit the section when it is empty.
5. **Case matrix** — the `--markdown` output.
6. **Cases by lens** — every case in full, grouped by lens in taxonomy order: Given / When / Then,
   expected source with its evidence, current status with evidence and verification, severity ×
   likelihood → priority, origin (changes targets), test idea.
7. **Scenario walkthroughs** — `deep`/`prove`, from `{WORK_DIR}/walkthroughs.md`.
8. **Probe results** — `prove`: per probe, the cases, the verdict, and the relevant output lines. If
   probes were declined, say so.
9. **Coverage and limits** — what the analysis did not do, stated honestly:
   - lenses applied, and lenses skipped with the reason;
   - the `UNKNOWN` count, and what would resolve those cases;
   - cases cut at `quick` (`trimmed`), and cases dropped as filler in consolidation (`dropped`);
   - a degraded level and its reason; `--no-ground`; an interview that was declined;
   - skeptic verdicts of `unknown` (from `skeptics.json`), and inconclusive probes with their errors.
10. **Dismissed** — cases the user marked "can't happen here", with the reason. Omit when empty.
11. **Appendix: test skeletons** — `deep`/`prove`, from `{WORK_DIR}/skeletons.md`. At `prove`, the
    probe sources too.

## Writing rules

- A `proposed` behavior that is still `needed` appears only with **DECISION NEEDED**, in the matrix and
  in the case detail, never in language that reads like a requirement.
- Every `file:line` in the report comes from `cases.json` or `surface.md`. Nothing new is introduced
  while writing.
- For code targets, a verified defect is called a defect in plain words. It is not softened to
  "consider", and it is not filed as future work.
- Keep it scannable: the verdict and the top risks must be enough for someone who reads nothing else.

## Wiki

If `{PROJECT_DIR}/wiki/` exists, follow the wiki-first mandate. Writing there is allowed: pre-flight
excluded `wiki` from the tree snapshot.

1. Run `/wiki:ingest-document '<company>' '{OUT_DIR}/{SLUG}-edge-cases.md' 'other' --summary
   'Edge-case analysis of <target> (<level>)'`. `<company>` is the client or project the target
   belongs to: the wiki's `clients/` folder names them. If more than one fits, ask.
2. Make sure `wiki/_log.md` has an entry `## YYYY-MM-DD — edge-cases — <target>` giving the level,
   case counts by priority, and the defect count. Add it if the ingest did not.

## Last step

1. Prove the run was read-only:

   ```bash
   python3 {SKILL_DIR}/scripts/tree_state.py compare {WORK_DIR}/tree-before.json --repo {PROJECT_DIR} {EXCLUDES}
   ```

   Exit 0 means no file outside `.edge-cases/`, the output directory and `wiki/` changed, including
   files that were already modified before the run. Report any difference to the user verbatim.
2. Print the final summary block from `SKILL.md`, with the read-only line taken from that result.
3. Offer the follow-ups.
