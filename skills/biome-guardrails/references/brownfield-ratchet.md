# Brownfield Audit + Ratchet Mode

Follow this procedure when the target codebase already exists and already has
debt. The greenfield phases in SKILL.md overwrite configs and expect a clean
start. This mode does the opposite: it never overwrites an existing config,
it never edits source files, and it is green on day one.

## Why this mode exists

Real incident, condensed: a production data layer published 536 handlers
behind one type — `(args: AnyArgs) => Promise<any>`. Its schema file grew to
4,776 lines. No gate fired, because three holes lined up:

1. The linter was disabled for that directory by a config override.
2. The TypeScript lint plugin was loaded, but 0 of its rules were enabled.
3. No tool anywhere capped file size.

The cleanup took a multi-week workstream. A ratchet installed on day one
would have blocked the second `any` and the 1,501st line. That is the job
here: find the holes, measure the debt, and install gates that block new
debt without punishing anyone for the old debt.

## Phase B1 — Audit (read-only)

Change nothing in this phase. Produce numbers.

### B1a. Map the enforcement that exists

| Check | How | Hole signal |
|---|---|---|
| Lint engines present | `biome.json*`, `eslint.config.*`, `.eslintrc*` | none found |
| Per-directory disables | read `overrides` in `biome.json`; `ignores` in ESLint configs | a directory with `"linter": { "enabled": false }` |
| Rules loaded but unused | `eslint --print-config <a-real-source-file>`; count rules per plugin prefix | a plugin registered with 0 rules enabled |
| `any` rule active anywhere | search resolved configs for `no-explicit-any` / `noExplicitAny` | absent everywhere |
| File-size cap | search configs and scripts for `max-lines`, `maxLines` | absent everywhere |
| Suppression census | grep counts of `eslint-disable`, `biome-ignore`, `@ts-ignore`, `@ts-expect-error` | large or growing counts |
| Hook manager | `lefthook.yml`, `.husky/`, `simple-git-hooks`, `core.hooksPath` | none — nothing runs locally |
| CI lint steps | read the CI config; note `continueOnError` / `\|\| true` markers | lint runs but cannot fail |

A directory-level linter disable is the highest-value finding. It is how a
whole subsystem goes invisible. Record every one, with the reason if stated.

### B1b. Measure the debt

Run the bundled ratchet script with a throwaway baseline path. This measures
without touching the project:

```bash
node <skill>/scripts/type-ratchet.mjs --init --baseline /tmp/audit/type-baseline.json
node <skill>/scripts/max-file-lines.mjs --init --baseline /tmp/audit/size-baseline.json
```

Read both JSON files. They contain the counts, the per-rule split, and the
per-file offender list.

Also measure the file-size distribution:

```bash
git ls-files '*.ts' '*.tsx' | grep -vE '_generated|\.next/|node_modules' | \
  while read -r f; do wc -l < "$f"; done | \
  awk '{if($1>1500)a++; if($1>1000)b++; if($1>500)c++; n++} END{print "files:",n," >1500:",a," >1000:",b," >500:",c}'
```

### B1c. Measure compiler-flag costs, one flag at a time

Run `tsc --noEmit` once per candidate flag. Never run them together — an
aggregate count hides which flag costs what.

| Flag | Typical cost | Action if cheap |
|---|---|---|
| `noImplicitOverride` | near zero | adopt, fix the errors in the same change |
| `noFallthroughCasesInSwitch` | near zero | adopt |
| `noImplicitReturns` | low | adopt if under ~10 errors |
| `exactOptionalPropertyTypes` | high (often 1,000+) | defer; record the number |
| `noUncheckedIndexedAccess` | high | defer; record the number |
| `noPropertyAccessFromIndexSignature` | very high | usually reject; record the number |

```bash
npx tsc --noEmit -p tsconfig.json --noImplicitOverride 2>&1 | grep -c "error TS"
```

Adopt a flag only when its measured cost is small enough to fix in the same
change. Record every deferred flag with its number — a future session should
not re-measure.

### B1d. Report

Present one table before proposing anything:

```
| Signal                          | Value |
| Weak-typing count (production)  | NNN   |
| Weak-typing count (with tests)  | NNN   |
| Files over the cap              | NN (largest: N,NNN lines) |
| Directories with linting off    | list  |
| Plugins loaded with 0 rules     | list  |
| Suppression count               | NNN   |
| Free compiler flags             | list with per-flag cost |
```

If the user asked for `--audit` only, stop here.

## Phase B2 — Decisions

Ask the user (AskUserQuestion) before installing anything. Three questions
matter; make the measured numbers visible in the option descriptions:

1. **Sequencing.** Warn-only now, blocking now, or defer? Check `git status`
   first — if a large refactor is in flight, warn-only or defer avoids
   red-walling it. A ratchet with a correct baseline is green on day one, so
   immediate blocking is safe for most repos.
2. **Scope of the `any` gate.** Production only (default) or tests included.
   Test mocks legitimately need `any`; holding fixtures to the production
   bar mostly generates noise. File-size always includes tests — a
   6,000-line test file is exactly the reviewability problem this exists to
   stop.
3. **File cap.** Default 1,500. Accept the user's number if they have one.

## Phase B3 — Cheap wins (rules that already exist)

Before adding anything new, turn on what is already installed:

- Enable the engine's `any` rule at **warn** severity in the project's own
  config — Biome `suspicious/noExplicitAny`, or ESLint
  `@typescript-eslint/no-explicit-any`. Warn gives editor feedback on every
  keystroke; the ratchet is the actual gate. Respect engine ownership: if a
  directory is linted by ESLint, add the ESLint rule there, not Biome's.
- Adopt the compiler flags measured near-free in B1c. Fix their errors in
  the same change.
- Every per-directory linter disable found in B1a gets a comment naming the
  reason and the compensating control ("counted by the type ratchet").
  An undocumented exemption invites the next one.

Do not remove or rewrite existing configs in this mode.

## Phase B4 — Install the ratchets

1. Copy `scripts/type-ratchet.mjs` and `scripts/max-file-lines.mjs` from
   this skill into the project — `scripts/guards/` by default, or wherever
   the repo keeps guard scripts. Copy, do not reference: the project's CI
   and hooks cannot reach the plugin directory.
2. Initialize both baselines and commit them:
   ```bash
   node scripts/guards/type-ratchet.mjs --init            # add --include-tests if B2 chose it
   node scripts/guards/max-file-lines.mjs --init --max <cap>
   ```
   Default baseline paths are `config/type-strength-baseline.json` and
   `config/file-size-baseline.json`. If the repo already keeps ratchet
   baselines elsewhere (a coverage baseline is the usual precedent), match
   that location with `--baseline`.
3. Add package scripts:
   ```json
   "lint:types": "node scripts/guards/type-ratchet.mjs",
   "lint:filesize": "node scripts/guards/max-file-lines.mjs"
   ```
   If the repo has an aggregate `verify`/`ci` script, append both.

## Phase B5 — Wire the rings

Read `references/ring-wiring.md` and wire both guards into the hook manager
and CI that B1a detected. Land warn-first if B2 chose it; the graduation
procedure is in that file.

## Phase B6 — Verify with mutation tests

Never report a guard green until you have watched it fail. Run every row:

| # | Mutation | Expect |
|---|---|---|
| 1 | none | both guards exit 0 |
| 2 | add `const x: any = 1;` to a production file | type-ratchet exits 1 and names the file; revert |
| 3 | run `--update` while that regression exists | refused, exit 1 |
| 4 | run `--update` without `RATCHET_ALLOW_UPDATE=1` | refused, exit 64 |
| 5 | create a file one line over the cap | max-file-lines exits 1; delete it |
| 6 | append one line to a baselined offender | max-file-lines exits 1; revert |
| 7 | run both guards bare, no arguments | repo mode scans tracked files — CI calls them this way |

If the hook manager was wired, also stage a violating file and confirm the
hook reports it.

## Phase B7 — Report

Print what was measured, what was installed, what was deferred (with its
measured cost), and the one-line policy: **counts only go down; caps only
apply to growth; baselines record pre-existing debt only.** State explicitly
that no existing config was overwritten and no source file was edited.

If the project keeps engineering-process docs (CONTRIBUTING, a wiki), record
the guards and the graduation state there — an unrecorded gate is the first
thing a future cleanup deletes.
