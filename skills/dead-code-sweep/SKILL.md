---
name: dead-code-sweep
description: >
  Post-session dead-code cleanup with regression proof. Use this immediately after a coding
  session — or whenever the user says "clean up dead code", "remove unused code", "did I leave
  anything behind", "sweep for leftovers", "delete orphaned files/imports/exports", "remove stale
  tests", "clean up after this refactor/migration", "prune what's no longer used", or finishes a
  change and wants the litter gone — even if they never say the words "dead code". It resolves a
  scope (uncommitted work by default, a branch's changes vs its base, or the entire project),
  discovers the repo's own verification gates (typecheck/lint/build/test) and runs them FIRST to
  record a baseline, then finds candidates by tracing the diff (what did this change orphan?) plus
  the ecosystem's native detectors, cross-checks every candidate against dynamic references and
  framework conventions, and removes in gated waves: high-confidence items auto-removed with gates
  re-run after every wave (a new failure restores the code — the test proved it alive),
  medium-confidence items batch-confirmed in one interview, low-confidence items reported only.
  Stale tests, mocks, fixtures, and snapshots of removed code are swept with it; a failing test is
  never deleted to make gates green. Every removal is evidence-cited, backed up under
  .dead-code-sweep/ with one-command restore, and reported honestly. Never commits.
---

# Dead-Code Sweep

You are running a post-session dead-code sweep. A coding session just ended (or the user wants a
broader cleanup), and changes leave litter behind: the old implementation that got replaced but not
deleted, the helper whose last caller vanished, the import left dangling, the test still exercising
a function that no longer exists, the dependency added during an experiment. Your job is to find
that litter, prove it is dead, remove it, and prove the removal broke nothing.

Two ideas govern everything below:

- **The diff is the seed.** Dead code "left behind by changes" is findable by asking what the
  changes stopped referencing — not by archaeology over the whole repo. Diff-seeded analysis is
  faster, has far fewer false positives, and matches what the user actually wants right after a
  session. Whole-project mode exists, but it is the explicit choice, never the accident.
- **"Dead" is an empirical claim, and so is "no regressions."** Neither is establishable by
  reading code alone. Deadness is proven by exhaustive reference searching (including dynamic and
  framework-convention references); safety is proven by the repo's own gates run before and after.
  If you cannot run gates, you do not get to delete autonomously — evidence standards drop, so
  autonomy drops with them.

Deleting live code is the one unforgivable failure mode. Missing some dead code is fine — say so
in the report. When in doubt, downgrade confidence, never up.

## Arguments

Arguments arrive with the invocation and are parsed as:

```
[scope] [--base <ref>] [--report-only] [--out <dir>]
```

- `scope` — `uncommitted` | `branch` | `project`. If omitted, auto-detect: dirty working tree →
  `uncommitted`; clean tree on a branch ahead of the default branch → `branch`; otherwise
  `project`. State the resolved scope and why before proceeding.
- `--base <ref>` — base for `branch` scope. Default: merge-base with the default branch
  (`origin/HEAD`, falling back to `main`/`master`).
- `--report-only` — full analysis, zero edits. Findings + evidence + what _would_ be removed.
- `--out <dir>` — working directory for backup + report. Default `.dead-code-sweep/<UTC-timestamp>/`.

## Phase 0 — Scope and baseline

**Resolve the change set.**

| Scope         | Change set                                                                          |
| ------------- | ----------------------------------------------------------------------------------- |
| `uncommitted` | `git diff HEAD` (staged + unstaged) plus untracked files (`git status --porcelain`) |
| `branch`      | `git diff <merge-base>..HEAD`, plus the working tree if dirty                       |
| `project`     | every tracked source file; the "change set" is the whole repo                       |

**Discover the gates from the repo's own conventions** — never invent commands. Look, in order, at:
`package.json` scripts (typecheck/tsc, lint, build, test), `Makefile`/`justfile` targets,
`pyproject.toml` tooling (ruff, mypy, pytest), `Cargo.toml` (`cargo check/clippy/test`), `go.mod`
(`go vet/build/test`), CI workflow files as corroboration. `references/toolchain.md` has the
per-ecosystem table. Prefer the repo's named scripts over raw tool invocations — the script encodes
the project's flags.

**Run the full gates once, now, before touching anything.** Record every failure verbatim. This
baseline is what makes "no regressions" an honest claim later: a regression is a _new_ failure
relative to this run, and a pre-existing failure is reported as pre-existing, never silently
absorbed or silently fixed.

Two baseline outcomes change the plan:

- **No gates exist at all** (no test/typecheck/build commands discoverable): autonomous deletion
  loses its safety net, so it is off. Downgrade every would-be high-confidence removal to the
  confirmation batch, and say prominently in the report that the sweep ran without a regression net.
- **The baseline is broken in a way that masks regressions** (build or typecheck fails): you cannot
  distinguish "my removal broke it" from "it was broken." Switch to `--report-only` behavior
  automatically, tell the user why, and include the baseline failures in the report.

## Phase 1 — Candidate discovery

Read `references/detection.md` before this phase — it holds the candidate classes, the seed-and-
trace method, and the liveness checklist that Phase 2 depends on.

**Diff-seeded (uncommitted and branch scope).** Walk the change set and ask, for each hunk:

1. What references did this change _remove_? Each removed call/import/JSX-usage points at a symbol
   or file that may now be orphaned. Trace each: does anything else still reference it?
2. What did this change _replace_? New code that supersedes an older sibling (renamed function,
   rewritten component, v2 next to v1) often leaves the old one live-looking. Compare added symbols
   against similarly-named or similarly-shaped existing ones.
3. What did this change leave _inside touched files_? Unused imports, unused locals, private
   functions with no remaining callers, newly commented-out blocks.
4. What tests, mocks, fixtures, and snapshots exercised the code this session removed or renamed?
5. What dependencies did the session's changes stop using (or add and abandon)? In diff scopes,
   only audit dependencies whose import sites the change set touched — full dependency audits
   belong to `project` scope.

**Tool-assisted, always.** If the ecosystem has native detectors (knip, ts-prune, ESLint
`no-unused-vars`, `ruff --select F401,F811,F841`, vulture, `cargo machete`, compiler warnings —
see `references/toolchain.md`), run them and intersect their output with your scope. Tool output is
a _candidate list_, never a verdict — every hit still passes Phase 2. Never add dependencies to the
user's project to run a detector; ephemeral runners (`npx`, `bunx`, `uvx`) are fine, and skipping a
tool that isn't cheaply runnable is fine too.

**Project scope.** No diff to seed from, so the detectors and an export/file-reference inventory
carry discovery. Expect more candidates and more false-positive risk; the Phase 2 evidence bar does
not move.

**Fan out when the candidate list is large.** Cross-checking references is read-only and
embarrassingly parallel: for more than ~8 candidates, launch parallel Explore agents, each handed a
batch of candidates and the liveness checklist, each returning per-candidate evidence (searches run,
hits found). You make the classification calls yourself — agents gather evidence, they don't vote
on deletion.

## Phase 2 — Evidence and confidence

For every candidate, run the **liveness checklist** (full version in `references/detection.md`):
references from non-test source; references from tests; dynamic references (the name inside string
literals, template strings, config files, route tables, DI registrations, reflection like
`getattr`/`import_module`/`require(variable)`); framework conventions that make files live without
imports (Next.js/SvelteKit/Remix routes, Convex functions, serverless handler configs, Django
dotted-path strings, migrations); public-API surface (`package.json` `exports`/`main`/`bin`,
published-package roots, `.d.ts`); explicit keep-markers (`@keep`, `@public`, `@api` annotations).

Then classify:

- **High confidence — auto-remove.** All of: zero non-test references found by at least two
  independent search strategies (e.g., a detector hit _and_ your own grep sweep); no liveness
  checklist match; deadness attributable to this scope's changes (diff scopes) or clearly
  established (project scope); gates exist and run. Its dedicated tests/mocks/snapshots join it in
  the same wave — they are one logical unit. Test-only-referenced code qualifies as high **when
  the change set itself removed its last production reference** — the diff is the author's
  expressed intent to migrate away, and the stale tests join the removal unit.
- **Medium confidence — batch-confirm.** Dead by primary analysis but carrying one risk marker:
  production code referenced _only_ by its own tests where the diff shows no such intent (project
  scope, or the code was already test-only before this session — it may be intended public API,
  or half-built work); exported from a package barrel or root; a generic
  name with near-miss string matches; a commented-out block (deleting comments is a judgment call);
  an unused dependency; found by only one detection method.
- **Low confidence — report only, never touch.** Any liveness checklist match, anything
  unverifiable, anything whose removal you cannot gate.

**Scope discipline.** In `uncommitted` and `branch` scope, dead code you stumble on that predates
the change set goes to an "Out-of-scope observations" section of the report, untouched. The
post-session sweep stays fast and predictable; archaeology is what `project` scope is for, and the
report should suggest it when observations pile up.

## Phase 3 — Removal in gated waves

Skip this phase entirely under `--report-only` (including auto-downgrade from a broken baseline).

**Back up before the first edit.** Create `<out>/backup/` and, before modifying or deleting any
file, copy its pre-sweep version there under its relative path. Write a `.gitignore` containing `*`
into `<out>/` so the sweep's own artifacts never pollute the user's status. This backup is what
makes restore trivial for tracked _and_ untracked files, without touching git state.

**Git state is the user's.** Never commit, stage, stash, or switch branches. In `uncommitted`
scope the user's session work is sitting in the working tree — the sweep's only legitimate edits
are the removals themselves, and the user's intended changes are never reverted or "improved."

**Wave loop:**

1. Remove the high-confidence set. Group logically (a symbol + its tests + its snapshot = one
   removal unit) so failures implicate specific units.
2. Re-run the gates. Compare against the baseline. Any **new** failure → restore the implicated
   unit(s) from backup (bisect by unit if attribution is unclear), re-run to confirm green, and
   reclassify the finding as **"not dead — restored"** with the failure output as evidence. A test
   that fails when code is removed has just proven the code alive; the response is always to
   restore the code, never to delete or skip the test. Deleting a failing test to get to green is
   the one thing this skill must never do.
3. Cascade: removals orphan other code (the file whose only importer just went, the export whose
   only caller just went). Re-scan within scope rules; new high-confidence findings form the next
   wave. Convergence is typically 2–3 waves.
4. If the full test suite is slow (>~5 min), it is acceptable to gate intermediate waves on the
   fastest meaningful check (typecheck + targeted tests for touched areas) — but the **full** gate
   set runs at baseline and again after the final wave, no exceptions.

**Then the confirmation batch.** Present all medium-confidence findings in a single
AskUserQuestion round (multiSelect, grouped by class if numerous, each option naming the item, the
evidence, and the risk marker that made it medium). Remove what the user accepts, in one more gated
wave. Declined items are recorded as "kept by user choice." If there are no medium findings, skip
the interview — don't manufacture questions.

## Phase 4 — Report

Write `<out>/report.md` and give the user a compact inline summary. The report contains:

1. **Header** — scope (and how it was resolved), change-set size, gates discovered, baseline
   result with pre-existing failures listed verbatim.
2. **Removed** — per unit: what, where (`file:line` or whole file), why dead (the searches run and
   what they found — evidence, not assertion), which wave, gate result after.
3. **Restored** — anything removed then restored by a gate failure, with the failure output. These
   are the sweep's most honest lines; never omit them.
4. **Confirmed / declined** — the interview outcomes.
5. **Report-only findings** — low-confidence items with their liveness evidence, and out-of-scope
   observations (suggest `project` scope if warranted).
6. **Verification** — final gate run vs. baseline, stated as: no new failures / these new failures
   (should be none by construction).
7. **Restore instructions** — the backup location and the literal copy command per unit, plus
   "restore everything": `cp -R <out>/backup/. <repo-root>/`.

A clean session is a valid outcome: "nothing to sweep" plus the evidence you looked is a _good_
report. Don't pad it, and don't manufacture findings to seem thorough.

If the project has a wiki vault, log the sweep per the project's conventions (`wiki/_log.md`).
Leave the working tree uncommitted — committing is the user's call.

## Success criteria

- Baseline gates ran before any edit; every later claim of safety is relative to that baseline.
- Every removal cites evidence (searches performed, detectors agreeing); every restoration is
  reported with the failure that caused it.
- No liveness-checklist match was auto-removed; no failing test was deleted or skipped to reach
  green; nothing outside the resolved scope was touched.
- Final gates show zero new failures relative to baseline.
- Backup + restore instructions exist for every edit; git state (index, stash, branches) untouched;
  nothing committed.
