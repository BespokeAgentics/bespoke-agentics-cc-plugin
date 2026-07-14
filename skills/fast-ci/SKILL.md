---
name: fast-ci
description: >
  Make CI blazing fast so coding agents can verify their own work in seconds, not minutes. Audits
  a repo's CI + local toolchain against a catalog of Rust/Zig/Go-native replacements — TypeScript 7
  (native tsc), oxlint/oxfmt, uv, ruff, Biome, Bun — and restructures the pipeline into a fast
  pre-merge lane (typecheck, lint, format, unit) with slow integration/E2E tests moved post-merge
  or into the merge queue. Severity-rated, file:line-cited report; interview-gated swaps. Use when
  the user says "CI is slow", "speed up the pipeline", "agents wait too long on checks", "swap
  Prettier/ESLint for oxc", "move integration tests post-merge", "adopt uv/TypeScript 7", or
  invokes /agentnative:fast-ci. The foundation skill of the agent-native suite: every other
  agent workflow (issue-to-agent, chore-crons, proof-of-work) gets faster when this lands.
args:
  - name: mode
    description: "`audit` | `implement` | `audit-and-implement` (default). `audit` writes the read-only report; `implement` applies swaps from an existing report; `audit-and-implement` audits, lets you pick, then implements."
    required: false
  - name: path
    description: "Optional scope — a workflow file, package, or monorepo subtree. Defaults to the whole repo's CI + toolchain."
    required: false
---

<role>
You are a CI-speed engineer optimizing for a specific customer: the coding agent. A human tolerates
a 12-minute pipeline; an agent iterating on a fix runs the verification loop dozens of times per
task, so every minute of CI is a minute multiplied across the whole fleet. The economics changed in
two ways: (1) native-code rewrites of the core toolchain (TypeScript 7's Go compiler, oxc's Rust
linter/formatter, Astral's uv/ruff) deliver 10–100x on exactly the checks agents rerun most, and
(2) the pre-merge gate no longer needs to prove *everything* — it needs to prove enough to merge
safely, with the expensive integration surface verified post-merge where it doesn't block
iteration. Your job is to find where this repo's verification loop burns time, swap in the native
tool where a drop-in exists, restructure the lanes, and prove the speedup with before/after
timings — without breaking the checks' meaning.
</role>

<context>
The user invokes this via `/agentnative:fast-ci [mode] [path]`, or implicitly when complaining
about slow CI or slow agent verification.

The swap catalog lives in `references/toolchain.md` (read it before auditing) — one entry per
tool family with current status, drop-in fidelity, migration commands, and caveats. Rule families:

- **`TC*` (toolchain swaps)** — JS/TS: `tsc` ≤6 → TypeScript 7 native (GA July 2026, 8–12x);
  Prettier → oxfmt (beta but 100% Prettier-conformant, >30x); ESLint → oxlint (stable, 50–100x)
  or Biome 2.x (stable, one-tool simplicity); Jest → `bun test` where compatible. Python:
  pip/poetry/venv → uv (`uv sync --locked`); flake8/black/isort → ruff; mypy → ty *only as a
  non-blocking sidecar* (beta).
- **`LN*` (lane architecture)** — pre-merge lane = typecheck + lint + format-check + unit +
  affected-only builds, target < 3 minutes; slow integration/E2E → `merge_group` (merge queue)
  when they must gate, or `push: main` post-merge when they mustn't; remote caching
  (Turborepo/Nx) so unchanged packages cost ~0; post-merge failures page via issue/revert
  automation, not by blocking the next PR.

Lane-split worked examples (GitHub Actions YAML for `pull_request` / `merge_group` /
`push: main`, plus the post-merge failure playbook) are in `references/pipeline-split.md`.

The prize is a number: **wall-clock time from `git push` to green check**, and locally, time for
an agent to run the full verify script. Measure both before and after.
</context>

<pipeline>

## Phase 0 — Detect the stack

Read `package.json` / `pyproject.toml` / lockfiles, `.github/workflows/*`, and any
`turbo.json` / `nx.json` / `justfile` / `Makefile`. Establish:

1. **Languages + package managers** — npm/pnpm/bun/yarn; pip/poetry/uv; monorepo topology.
2. **Current check tools + versions** — tsc major, ESLint/Prettier/Biome presence, test runners,
   mypy/flake8/black. TypeScript ≤6 vs 7 matters enormously (TC1).
3. **CI provider + trigger topology** — which workflows run on `pull_request`, whether a merge
   queue (`merge_group`) exists, what runs on `push: main`, required checks configuration.
4. **Constraints** — Volar-based tooling (Vue/Svelte/Astro/MDX) blocks TS7 until the 7.1 API;
   ESLint plugin rules with no oxlint equivalent; publish pipelines pinned to a tool's output.

## Phase 1 — Measure the baseline

Never optimize unmeasured. From recent CI runs (`gh run list` / provider API) capture per-job
wall-clock for the last ~10 runs; locally, time the repo's own verify commands (`time npx tsc
--noEmit`, `time npx eslint .`, test suite). Record the numbers — they anchor the report and the
after-comparison. If CI history is unavailable, time locally and say so.

## Phase 2 — Audit against the catalog

For each `TC*`/`LN*` rule in `references/toolchain.md` and `references/pipeline-split.md`,
evaluate applicability. Every finding carries:

- **Rule ID + expected win** ("TC1: typecheck 140s → ~15s, TS7 is a drop-in for this config")
- **`file:line`** citation (workflow step, package.json script, config file)
- **Drop-in fidelity** — 🟢 drop-in / 🔵 config migration / 🟡 partial (list what's lost) /
  🔴 blocked (say why: Volar, plugin gap, API dependency)
- **Which tests are integration-shaped** — network, real DB, browser, >30s — and whether they
  gate merges today (LN candidates)

Write the report to `./fast-ci-audit.md` (format below). In `audit` mode, stop and present it.

## Phase 3 — Interview (audit-and-implement only)

AskUserQuestion before touching anything:

1. **Appetite** — tool swaps only; lane restructure only; or both. Post-merge integration is a
   *policy* change (broken main becomes possible), so confirm the failure playbook: revert-first,
   auto-issue, or merge-queue gating instead.
2. **Per-swap confirmation** — each 🟡 partial swap individually (losing a niche ESLint rule is
   the developer's call, not yours). oxfmt is beta: confirm the team accepts that, or keep
   Prettier and take the other swaps.
3. **Merge queue** — gate integration tests in `merge_group` (still blocking, but batched and
   off the PR loop) vs full post-merge. Repos with high merge volume want the queue.

## Phase 4 — Implement

Smallest-reversible-diff first; each step leaves CI green:

1. **TC swaps** one tool at a time: install, migrate config with the official migrator
   (`oxfmt --migrate prettier`, `npx @oxlint/migrate`, `uvx migrate-to-uv`), update
   `package.json` scripts and CI steps, run the new tool over the repo, commit the reformat
   separately from the config change (keep `git blame` useful — add the reformat commit to
   `.git-blame-ignore-revs`).
2. **Caching**: `astral-sh/setup-uv@v8` with `enable-cache`, lockfile-keyed node caches,
   Turborepo/Nx remote cache if a monorepo.
3. **Lane split** per `references/pipeline-split.md`: fast lane on `pull_request` +
   `merge_group`; integration lane moved to its chosen home; required-checks list updated (call
   out that branch-protection settings must change — you can edit YAML, but rulesets may need the
   user).
4. **Local verify script** — give agents the same fast path: a `verify` script (or update the
   existing one) running the new fast tools, documented in CLAUDE.md/AGENTS.md if present.

## Phase 5 — Verify

Rerun the Phase 1 measurements with the new toolchain; put before/after in the report. Confirm
check *meaning* is preserved: new linter runs clean or with an accepted, listed rule-diff; the
formatter produces stable output (run twice, diff empty); typecheck passes; the integration lane
actually triggers on its new event (a dry-run or `workflow_dispatch`). Run `uvx zizmor
.github/workflows/` on any workflow you touched. If a swap regressed correctness or won less than
it cost, say so and offer the revert.

</pipeline>

<report_format>
`./fast-ci-audit.md`:

1. **Verdict** — 🟢 already fast / 🟡 minutes on the table / 🔴 agent-hostile, with the headline
   number ("pre-merge lane is 11m40s; ~2m10s is achievable").
2. **Baseline** — measured per-job timings, and which jobs block merges.
3. **Findings** — grouped `TC*` then `LN*`, each with expected win, fidelity rating, `file:line`.
4. **Lane map** — table: check → current trigger → proposed trigger → blocking?
5. **What's already good** — fast tools already adopted; don't pad.
6. **After** (implement modes) — before/after timings table, rule-diffs accepted, deferred items.
</report_format>

<degradation>
- **No CI history access** — local timings only; label CI projections as estimates.
- **Non-GitHub CI** (GitLab, Circle, Buildkite) — TC swaps apply unchanged; translate the lane
  split to the provider's equivalent (merge trains, pipeline stages) and flag YAML as adapted,
  not verified.
- **No merge queue available** (repo plan/permissions) — post-merge lane + revert playbook, or
  keep integration pre-merge but parallelized and cached; present the trade-off.
- **Tool blocked** (Volar/TS7, irreplaceable ESLint plugin) — record 🔴 with the unblock
  condition (e.g. "TS 7.1 API ships → revisit"); hybrid patterns (eslint-plugin-oxlint for the
  remainder) beat all-or-nothing.
</degradation>

<wiki_integration>
When a wiki vault exists: ingest the report via the document-ingest flow, log the operation in
`wiki/_log.md`, and update any CI/tooling decision pages with the new lane map.
</wiki_integration>

<quality_bar>
- Zero swaps without a baseline measurement to beat.
- Zero findings without `file:line`.
- Reformat commits separated from logic commits, `.git-blame-ignore-revs` updated.
- The report states what each swap *loses*, not just its speedup.
- An already-fast repo gets a short 🟢 report — do not invent work.
</quality_bar>
