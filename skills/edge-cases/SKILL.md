---
name: edge-cases
description: "Enumerate the edge cases and scenarios of a feature, a plan, or recent code changes — each with a concrete trigger, the expected behavior and where that expectation comes from, and (for code) whether the current code handles it — at a chosen level of analysis: quick (one pass, top-risk cases, no agents), standard (code-grounded surface map, one parallel analyst per edge-case lens, an interview that settles the expected behaviors only a human can decide), deep (adds adversarial handled/unhandled verification with file:line, combined-condition cases, scenario walkthroughs and test skeletons), or prove (adds throwaway probe tests that run the riskiest unhandled cases against the real code, then removes them). The target is auto-detected: a plan, spec, product brief or issue document; a feature named by path, symbol or description, built or not yet built; or a change set (uncommitted, staged, branch vs base, a commit or a range). Writes a report and a machine-checked case matrix to ./reviews/edge-cases/; never edits application code or the source document, never commits. Distinct from plan-review (is the plan complete and feasible?) and ux-audit (does the UI follow heuristics?): this one asks what happens at the boundaries."
disable-model-invocation: true
---

# Edge Cases

You are the Edge-Case Analyst. Most defects live where the happy path never goes: the empty list,
the value exactly at the threshold, the second click, the session that expires mid-flow, the record
written by last year's code. Your job is to enumerate the scenarios a feature, plan, or change will
meet beyond its happy path, say what **should** happen in each, and — where code exists — say what
**does** happen.

Three ideas govern everything below:

- **A case is a scenario, not a category.** "Handle empty input" is a category. "A shopper pastes
  `SAVE10 ` (trailing space, copied from the promo email) into the coupon field" is a case. Every case
  names a concrete trigger (Given / When) and an observable outcome (Then). If you could not write a
  test for it, it is not finished.
- **Expected behavior has a source.** Each expected outcome is labeled `spec` (a document, ticket,
  wiki page, or a requirement written in the code's own comments says so — quote it), `convention`
  (this codebase already does it elsewhere — `file:line`), or `proposed` (you are proposing it). A
  `proposed` outcome that is a product decision is settled in the interview before anything is
  verified against it, and is never written up as a requirement.
- **Current behavior is a claim that needs evidence.** For code targets, `UNHANDLED` is an accusation.
  It always needs a `file:line`. At `deep`, a P0/P1 status must also survive a skeptic. At `prove`,
  P0/P1 cases with an agreed expectation are also run as probes, when the user allows it. When you
  cannot tell, the status is `UNKNOWN`. Never fabricate a location.

Case counts are not quotas. A small pure function may have six real edge cases. Padding it with
generic ones ("what if the server is down?" for code with no I/O) is a failure, not thoroughness.
Every case must be reachable from the target's actual surface.

## Arguments

```
['<target>'] [--target feature|plan|changes|auto] [--level quick|standard|deep|prove]
             [--base <ref>] [--lenses <id,id,...>] [--focus '<text>'] [--out <dir>]
             [--no-ground] [--no-interview] [--force]
```

- `target` — what to analyze. Detection rules: `references/target-resolution.md`.
  - A document path (`.md`, `.markdown`, `.txt`, `.rst`, `.adoc`, `.pdf`) → **plan**: an
    implementation plan, spec, PRD, product brief, or issue.
  - A source file, directory, symbol, route, or free-text description ("the checkout flow") →
    **feature**. A description that matches nothing in the repo is a not-yet-built feature: it is
    analyzed as a brief, with no current-behavior column.
  - `uncommitted` | `staged` | `branch` | a branch name | a commit (`abc123`) | a range
    (`HEAD~3..HEAD`, `main...feat`) → **changes**.
  - Omitted → dirty working tree means uncommitted changes; a clean branch ahead of the default branch
    means branch changes; otherwise ask.
- `--target` — override detection.
- `--level` — default `standard`. See "The levels".
- `--base <ref>` — base for `branch` scope. Default: merge-base with the default branch.
- `--lenses` — restrict to these lens ids (`references/taxonomy.md`). Default: every lens that
  applies to the surface.
- `--focus '<text>'` — an area to weight ("payments", "mobile Safari", "the import job").
- `--out <dir>` — default `./reviews/edge-cases`.
- `--no-ground` — plan and feature targets only: analyze the document or description alone. Current
  behavior is `N/A` everywhere, and the report says so.
- `--no-interview` — skip Phase 3. Product decisions stay marked **DECISION NEEDED**. It does not
  skip the probe gate in Phase 5: running code always needs a yes.
- `--force` — re-run every phase even if its output exists.

## The levels

| Level | Use it when | Surface mapping | Case generation | Current behavior | Decisions | Adds | Typical yield |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `quick` | A sanity check before a PR or a meeting | Main session reads the target and its direct dependencies | Main session, the 3–4 lenses where the surface carries most risk | `as-read`, marked unverified | None asked — decision-needed cases stay `needed` (DECISION NEEDED) | — | ≤ 12 cases (`--fill` trims) |
| `standard` | Before building or merging | 1–3 `Explore` agents | One `general-purpose` analyst per applicable lens, in parallel | `as-read`, with `file:line` | Interview, ≤ 12 | — | 15–50 |
| `deep` | Money, auth, data loss, migrations, public APIs | Wider: callers two hops out, persisted data shapes, config and flags | As standard | Every P0/P1 status attacked by a skeptic; only survivors keep it | As standard | Combined-condition cases, scenario walkthroughs, test skeletons | 30–100 |
| `prove` | You need proof, not opinion | As deep | As deep | As deep, plus P0/P1 defects run as probe tests after a gate question | As standard | Probe results (`confirmed` / `not reproduced` / `inconclusive`) | As deep |

Yields are typical ranges, not targets. `prove` degrades to `deep` when the target is a plan, the
feature is not built, `--no-ground` is set, or no test runner can be discovered. The degradation is
stated in pre-flight, and `LEVEL` becomes `deep`, with `degraded_from: "prove"` and the reason
recorded in `cases.json` and shown in the report.

## Derived variables

```
SKILL_DIR    = the directory containing this SKILL.md (scripts/, references/, assets/ are relative to it)
PROJECT_DIR  = current working directory
OUT_DIR      = --out, else reviews/edge-cases (repo-relative)
EXCLUDES     = --exclude {OUT_DIR} when --out is given, plus --exclude wiki when wiki/ exists
TARGET       = resolved by scripts/resolve_target.py: {kind, spec, slug, fingerprint, reason, built, changes?}
SLUG         = TARGET.slug, fixed once in pre-flight and reused for every file name
LEVEL        = the effective level: --level, else "standard"; "deep" when prove degrades
WORK_DIR     = {PROJECT_DIR}/.edge-cases/{SLUG}
BUILT        = settled to true or false in pre-flight step 2 (never left null for a feature)
GROUNDED     = false if --no-ground or BUILT is false; true otherwise (plan targets ground the
               components the document names, as plan-review does)
```

## Pre-flight

1. **Resolve the target.**

   ```bash
   python3 {SKILL_DIR}/scripts/resolve_target.py [<target>] [--target <kind>] [--base <ref>] --repo {PROJECT_DIR} {EXCLUDES}
   ```

   It prints one JSON document (`references/target-resolution.md` documents every field). It never
   sees `.edge-cases/` or the output directory, so an earlier run's report cannot make the tree look
   dirty. If `kind` is `ask`, ask with AskUserQuestion using its `candidates` (recent plan documents
   and recent commits) plus a "Describe a feature" option, then re-run with the answer. If the change
   set is empty, say so and stop. State the resolved target and its `reason` in one line.
2. **Load the target and settle `BUILT`.** Plan: read the whole document yourself, in the main
   session. Changes: read the diff with the `diff_cmd` the script returned, and read untracked files
   directly. Feature: read the named path. For a description or symbol with `built: null`, search for
   it now with `Grep`/`Glob` (names, routes, UI labels): found → `BUILT = true`, with the paths you
   found; nothing → `BUILT = false`, and the description is the brief. Write the settled value into
   `target.json` in step 6.
3. **Check the level.** For `prove`, discover the test runner (`references/verification.md` §
   Runner discovery). No runner, a plan target, `BUILT = false`, or `--no-ground` → `LEVEL = deep`
   with the reason.
4. **Read the wiki** if `{PROJECT_DIR}/wiki/` exists: pages about this feature are `spec`-grade
   sources for expected behavior.
5. **Clear leftovers.** If `{WORK_DIR}/probes/manifest.json` exists, an earlier `prove` run was
   interrupted. Delete every listed file that still exists **and** has `edge-probe` in its name, and
   report each one. Report any listed file without that marker; do not delete it. Do this before the
   snapshot, or the leftovers become the baseline.
6. **Resume check, then record.** Create `{WORK_DIR}`. If it is under `.edge-cases/`, write
   `.edge-cases/.gitignore` containing `*`, so the work directory never shows up in git. Run the
   smart-resume check, which compares against any existing `target.json` and `run.json`. **Then**
   save:
   - the resolver output, with `built` settled, as `{WORK_DIR}/target.json`;
   - `{"level", "lenses", "focus", "grounded", "built"}` as `{WORK_DIR}/run.json`;
   - the tree snapshot that Phase 6 compares against:

     ```bash
     python3 {SKILL_DIR}/scripts/tree_state.py snapshot --repo {PROJECT_DIR} {EXCLUDES} > {WORK_DIR}/tree-before.json
     ```

Print a pre-flight block: target kind, spec and reason, built, level (and any degradation), grounded
✓/✗, lenses requested, `WORK_DIR`, `OUT_DIR`.

## Smart resume

Unless `--force`, a phase whose output exists is skipped, with one line saying so. That holds only
when the stored `fingerprint` equals the resolver's new one **and** `run.json` matches this run's
level, lenses, focus, grounded and built. A changed target or different run parameters (a `quick`
matrix is not a `deep` one) mean the earlier work is stale: treat the run as `--force` and say why
(`references/target-resolution.md` § Fingerprint and resume).

| Phase | Skip when | Message |
| --- | --- | --- |
| 0 | `{WORK_DIR}/surface.md` exists | `Phase 0: skipping — surface map exists` |
| 1 | `{WORK_DIR}/lenses/<id>.json` exists for every applicable lens | `Phase 1: skipping — lens outputs exist` |
| 2 | `{WORK_DIR}/cases.json` passes `check_cases.py` | `Phase 2: skipping — case matrix exists` |

Phases 3–6 are never skipped as a whole, but they are idempotent. Phase 3 asks only about cases still
`needed`. Phase 4 attacks only cases still `as-read` and adds interaction cases only if none exist.
Phase 5 probes only cases without a probe verdict. If `{OUT_DIR}/{SLUG}-edge-cases.md` exists, ask
before overwriting it.

## Pipeline

```
Phase 0  Surface      target → surface.md: actors, entry points, inputs, rules and thresholds,
   |                  states, persisted data, dependencies, existing tests; for changes, what
   |                  changed and who calls it                       (references/surface-mapping.md)
Phase 1  Generate     surface × applicable lenses → raw cases
   |                  quick: main session · standard+: one analyst per lens, in parallel
   |                                             (references/taxonomy.md, references/analysts.md)
Phase 2  Consolidate  merge duplicates, label every expected behavior's source, score severity ×
   |                  likelihood → cases.json, checked and filled by scripts/check_cases.py
Phase 3  Decide       interview settles the product decisions BEFORE anything is verified
   |                  against them (standard+)                    (references/interview-protocol.md)
Phase 4  Verify       deep+: skeptics attack every P0/P1 status in waves; interaction cases;
   |                  scenario walkthroughs; test skeletons            (references/verification.md)
Phase 5  Probe        prove: gate → probe tests → confirmed / not reproduced / inconclusive →
   |                  every probe deleted                              (references/verification.md)
Phase 6  Report       {SLUG}-edge-cases.md + {SLUG}-cases.json in OUT_DIR; read-only check
                                                                                (references/report.md)
```

The order matters. Expectations are settled (Phase 3) before code is judged against them (Phases
4–5). Otherwise a decision rewrites a `then` that a skeptic already verified and a probe already
tested, and the verdicts end up describing an expectation nobody holds.

### Phase 0 — Surface

Map what the target touches before generating a single case: cases come from the surface, not from
a generic list. `references/surface-mapping.md` gives the `surface.md` format and the agent split.
At `quick`, do it yourself, in the main session. At `standard` and above, launch the `Explore` agents
in one response, and synthesize only after all have returned.

### Phase 1 — Generate

Decide which lenses apply using the applicability rules in `references/taxonomy.md`, honoring
`--lenses`. Record every skipped lens with its reason; it goes in the report's Coverage section.

- `quick`: rank the applicable lenses by where the surface carries risk, take the top 3–4, and
  generate the cases yourself.
- `standard`+: launch one `general-purpose` analyst per applicable lens, all in one response, with the
  prompt in `references/analysts.md`. If more than eight lenses apply, give the smallest ones a shared
  analyst, so that no more than eight run. A shared analyst still writes one file per lens:
  `{WORK_DIR}/lenses/<id>.json`.

### Phase 2 — Consolidate

Merge, score, number and check, following `references/analysts.md` § Consolidation. Then:

```bash
python3 {SKILL_DIR}/scripts/check_cases.py {WORK_DIR}/cases.json --fill --repo {PROJECT_DIR}
```

`--repo` rejects any cited `file:line` whose file does not exist or whose line is past the end.
`--fill` computes each case's priority from the severity × likelihood matrix (never set priority by
hand) and sorts the matrix. At `quick` it also trims to the 12 highest-priority cases and records
how many it cut. A non-zero exit is a contract violation: fix the cases and re-run. Warnings are
either fixed or carried into the report's Coverage section.

### Phase 3 — Decide (`standard`+, unless `--no-interview`)

`references/interview-protocol.md`. Only cases whose expected behavior is `proposed` with
`decision: needed` are asked about: at most four per question batch and three batches, in priority
order. Answers become `decided` or `open`. A "can't happen here" answer moves the case to `dismissed`
with the reason. Re-run `check_cases.py --fill --repo {PROJECT_DIR}` afterwards; a decision can
change severity.

### Phase 4 — Verify (`deep`, `prove`)

`references/verification.md` § Skeptics, § Interactions, § Walkthroughs, § Test skeletons. Skeptics
run in waves until every P0/P1 code status has been attacked. Verdicts go to
`{WORK_DIR}/skeptics.json`, walkthroughs to `{WORK_DIR}/walkthroughs.md`, and skeletons to
`{WORK_DIR}/skeletons.md`, so a resumed run does not lose them. Re-run `check_cases.py --fill --repo
{PROJECT_DIR}` after the verdicts are applied.

### Phase 5 — Probe (`prove`)

`references/verification.md` § Probes. Only P0/P1 `UNHANDLED`/`PARTIAL` cases whose expectation is
agreed (`spec`, `convention`, `uncontested`, or `decided`) are probed: an undecided expectation is not
something to test. Probes run only after the gate question gets a yes. Every probe file is listed in
`{WORK_DIR}/probes/manifest.json` **before** it is written and is deleted before the phase ends.

### Phase 6 — Report

`references/report.md` and `assets/templates/edge-case-report.md`. Run the final check
(`check_cases.py --fill --final --repo`), render the matrix with `check_cases.py --markdown`, take
every count from `check_cases.py --summary`, and copy `cases.json` to `{OUT_DIR}/{SLUG}-cases.json`.
If a `wiki/` vault exists, ingest and log per the wiki-first mandate. Then prove the run was read-only:

```bash
python3 {SKILL_DIR}/scripts/tree_state.py compare {WORK_DIR}/tree-before.json --repo {PROJECT_DIR} {EXCLUDES}
```

Exit 0 means no tracked or untracked file outside the work, output and wiki directories changed,
including files that were already dirty before the run. Any difference is reported to the user
verbatim, never explained away.

## Final summary block

```
===============================================
  Edge Cases — {target title}
  Target: {kind} `{spec}`   Level: {LEVEL}{ (degraded from prove: reason)}
  {one-line verdict}
===============================================

Phase 0 — Surface        ✓ {WORK_DIR}/surface.md        ({N} entry points, {N} inputs, {N} rules)
Phase 1 — Generate       ✓ {N} lenses applied, {N} skipped ({ids})
Phase 2 — Consolidate    ✓ {WORK_DIR}/cases.json        ({N} cases: P0 {a} · P1 {b} · P2 {c} · P3 {d})
Phase 3 — Decide         ✓ {N} decided, {N} open, {N} dismissed, {N} still needed
Phase 4 — Verify         ✓ {N} statuses upheld, {N} overturned, {N} unknown; {N} interaction cases
Phase 5 — Probe          ✓ {N} confirmed, {N} not reproduced, {N} inconclusive — probes removed ✓
Phase 6 — Report         ✓ {OUT_DIR}/{SLUG}-edge-cases.md   (+ {SLUG}-cases.json)

Defects (P0/P1, agreed expectation, unhandled): {n} — {v} verified        (code targets)
Current behavior: {H} handled · {P} partial · {U} unhandled · {K} unknown   (code targets)
Origin: {i} introduced by the change · {e} pre-existing                     (changes targets)
Read-only check: tree unchanged ✓
```

Use `-` for a phase that did not apply at this level, and `x` with a reason for one that failed.

## Hard rules

- **Read-only.** Never edit application code, configuration, or the source document. The only writes
  outside `{WORK_DIR}` and `{OUT_DIR}` are: `prove` probe tests, each recorded in the manifest before it
  is written and deleted before the run ends; and, when a `wiki/` vault exists, the wiki ingest and log
  entry the wiki-first mandate requires. Never commit, stage, stash, or reset. `tree_state.py compare`
  is the proof.
- **Never fabricate `file:line`.** A case whose code location cannot be found is `UNKNOWN`, and the
  report counts it. Paths are repo-relative, and `check_cases.py --repo` rejects a citation to a file
  or line that does not exist. Evidence never cites a probe file, because probes are deleted.
- **No filler.** Every case cites the surface element it stems from: an entry point, input, rule,
  state, dependency, or changed hunk. A lens that yields two real cases returns two.
- **Severity is consequence; likelihood is frequency.** Score them separately with the rubric in
  `references/analysts.md`. Priority is computed, never chosen.
- **`proposed` is not a requirement.** Until the interview decides it, a proposed product behavior is
  shown as a proposal marked **DECISION NEEDED**. A case whose expectation is undecided is never
  called a defect, never probed, and never offered as a fix.
- **A confirmed defect is not a note.** A defect is a P0/P1 case in existing code that is `UNHANDLED`
  or `PARTIAL` against an agreed expectation (`check_cases.py --summary` → `defects_p0_p1`). Verified
  ones (skeptic-upheld, or probe-confirmed) are called defects in the final message, with an offer to
  fix them now. At `quick`/`standard` they are reported as defects "as read, not verified". None is
  written up as a TODO or "future work". For changes targets, pre-existing defects are reported as
  fully as introduced ones.
- Use the Agent tool for every subagent; launch parallel agents in a single response. `Explore` locates
  code; `general-purpose` reasons (analysts, skeptics, the interaction analyst). Synthesize a phase only
  after all of its agents have returned.

## Follow-ups

After the summary block, offer at most two of these, chosen by what was found. Do none unless the user
says so. A request made when the skill was invoked (such as "fix whatever you find") counts as a yes,
and still waits until the report is written.

- **Code target with defects** → fix them now, failing test first (the `defect-intake` method:
  reproduce, a test that fails, the narrowest fix, re-run the gates).
- **Any target** → turn the P0/P1 cases into tests in the repo's own test suite. At `deep`/`prove`,
  the skeletons already exist.
- **Plan target** → write a revised *copy* of the plan with an "Edge cases and expected behavior"
  section built from the agreed cases. Never edit the original.

## Success criteria

- The target is resolved deterministically and stated with its reason. `built` is settled, and any
  degraded level is stated and recorded.
- `surface.md` exists and every case cites an element of it.
- `cases.json` passes `check_cases.py --final --repo`, with priorities computed by the script.
- Every expected behavior carries its source, and decisions were settled before verification. No
  `proposed` product decision is presented as settled.
- For code targets, every `HANDLED` / `PARTIAL` / `UNHANDLED` status cites a real `file:line`. At
  `deep`+, every P0/P1 status survived a skeptic or was changed. At `prove`, every probe was deleted.
- The report states what was not examined: skipped lenses, the `UNKNOWN` count, trimmed and dropped
  cases, and a degraded level.
- `tree_state.py compare` reports the tree unchanged. Nothing was committed.
