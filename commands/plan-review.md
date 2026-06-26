---
name: "bespokeagentics:plan-review"
description: "Pressure-test a written implementation plan, spec, or issue/bug report BEFORE any code is written. Reads the local artifact, decomposes it into claims/tasks/assumptions/acceptance-criteria, grounds every referenced (and implied) component in THIS repo's real source (file:line) to surface the gaps the document hides, reviews it across completeness/feasibility/risk/clarity/scope lenses, runs an AskUserQuestion interview to validate and prioritize the findings, then writes a READ-ONLY review report + color-coded gap register to ./reviews/ — never modifying the original. For local plan/spec/ticket/design-doc markdown. Distinct from repo-audit (audits the codebase) and ux-audit (audits a UI): this audits a DOCUMENT against the code."
argument-hint: "'<artifact-path>' [--type plan|issue|spec|auto] [--depth quick|standard|deep] [--out <dir>] [--no-ground] [--force]"
allowed-tools: Skill(plan-review), Agent, AskUserQuestion, Bash, Read, Write, Glob, Grep
---

# Plan Review

Run the `plan-review` skill: read a written plan, spec, or issue report, ground it in this repo's
source, interview the user to validate the findings, and write a read-only review report. **The
original artifact is never modified.**

## Arguments

Parse from `$ARGUMENTS`:

```
'<artifact-path>' [--type plan|issue|spec|auto] [--depth quick|standard|deep] [--out <dir>] [--no-ground] [--force]
```

- `<artifact-path>` (required) — local text artifact (`.md`, `.markdown`, `.txt`) holding a plan,
  spec, design doc, or issue/bug report.
- `--type plan|issue|spec|auto` (default `auto`) — what kind of artifact; tunes the review lenses.
- `--depth quick|standard|deep` (default `standard`) — `quick` = high-confidence findings only, no
  adversarial pass; `standard` = full grounding + all lenses; `deep` = wider grounding + each finding
  adversarially verified before it survives.
- `--out <dir>` (default `./reviews`) — where the review report is written.
- `--no-ground` — review the document in isolation (use when the code isn't present). Grounding is the
  default because it produces the best findings.
- `--force` — re-run all phases even if outputs exist.

## Process

Invoke the `plan-review` skill and forward `$ARGUMENTS`. The skill will:

1. **Parse & decompose** — read the artifact, resolve its type, and break it into tasks, claims about
   the code, assumptions, acceptance criteria, and referenced components → `artifact-map.md`.
2. **Ground** — parallel `Explore` agents map each referenced/implied component to real `file:line`
   and verify each checkable claim (verified / contradicted / partial / unresolved), plus surface what
   the plan likely *missed* (other callers, duplicates, implied migrations/states) → `grounding-map.md`.
   Skipped under `--no-ground`.
3. **Review** — parallel `general-purpose` reviewers, one per lens (completeness, feasibility, risk,
   clarity, scope), produce de-duplicated, severity-rated findings → `findings.md`. On `--depth deep`,
   each blocker/major is adversarially refuted before it survives.
4. **Interview** — AskUserQuestion batches validate which gaps are real and in-scope, resolve blocking
   ambiguities, and set priority — so the report reflects your intent, not raw model suspicion.
5. **Report** — write `./reviews/<slug>-review.md`: readiness verdict (🟢/🟡/🔴), strengths,
   severity-grouped findings (gaps / improvements / errors with artifact quote + `file:line`),
   prioritized recommendations, a color-coded gap & ambiguity register, open questions, and a
   "definition of ready" checklist. Wiki-ingested if a vault exists.

## Output

`{OUT_DIR}/<artifact-slug>-review.md` (the read-only review), plus intermediate artifacts under
`plan-review-analysis/` (artifact-map, grounding-map, findings, interview-answers). Ends with a summary
and a readiness verdict, then **offers** to apply the P0 fixes into a revised copy or open the first
blocker as a task — but does not modify the original artifact or any code unless you say so.
