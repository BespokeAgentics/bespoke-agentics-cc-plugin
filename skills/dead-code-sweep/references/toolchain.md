# Toolchain — gates and detectors per ecosystem

Two lookups per ecosystem: the **gates** (how this repo proves nothing regressed) and the
**detectors** (native tools that surface dead-code candidates). Always prefer the repo's own named
scripts/targets — they encode the project's flags and env. Never install dependencies into the
user's project; ephemeral runners (`npx`, `bunx`, `uvx`, `pipx run`) are fine, and skipping a
detector that isn't cheaply runnable is fine — the manual sweep still runs.

## Gate discovery order

1. `package.json` `scripts` — look for `typecheck`, `tsc`, `check`, `lint`, `build`, `test` (and
   `test:*` variants). A `pretest`/CI script often chains the real set.
2. `Makefile` / `justfile` / `Taskfile.yml` targets with those names.
3. `pyproject.toml` — presence of ruff/mypy/pytest config implies `ruff check .`, `mypy`, `pytest`.
4. `Cargo.toml` → `cargo check`, `cargo clippy`, `cargo test`. `go.mod` → `go vet ./...`,
   `go build ./...`, `go test ./...`.
5. CI workflows (`.github/workflows/*.yml`) as corroboration for which commands the project treats
   as the bar.

Record the exact commands chosen and why. If a monorepo, scope gates to the affected packages for
intermediate waves but run the workspace-level gates for baseline and final.

## JavaScript / TypeScript

**Detectors**
- **knip** (`npx knip` / `bunx knip`) — unused files, exports, deps, class members. Best
  all-rounder; respects `package.json` exports. If the repo has a knip config, trust its
  entry-point map; if not, expect entry-point false positives and lean on the liveness checklist.
- **ts-prune** (`npx ts-prune`) — unused exports only; noisy on barrels; fine as a second signal.
- **tsc one-off flags** — `npx tsc --noEmit --noUnusedLocals --noUnusedParameters` surfaces unused
  locals without touching tsconfig.
- **ESLint/Biome/oxlint** — `no-unused-vars`, `no-unreachable` if already configured; run the
  repo's own lint script.
- **depcheck** (`npx depcheck`) — unused dependencies; cross-check against config-file usage
  (postcss/tailwind/vite plugins load by string) before flagging.

**Notes** — resolve `tsconfig.json` `paths` aliases before orphan-file conclusions; JSX usage
(`<Component />`) and decorator metadata count as references; side-effect imports
(`import './x.css'`) are live by definition.

**Snapshots** — Jest: `--ci` fails on obsolete snapshots, `-u` prunes them; Vitest analogous. Run
the repo's test command with its snapshot-check mode to find orphaned snapshots rather than
grepping for them.

## Python

**Detectors**
- **ruff** — `ruff check --select F401,F811,F841 .` (unused imports, redefinitions, unused
  locals); zero-config, safe everywhere; `--fix` only for F401 and only inside scope.
- **vulture** (`uvx vulture <paths>`) — unused functions/classes/attributes with a confidence
  score; treat <90% confidence as medium at best. Dynamic dispatch (`getattr`, Django/Celery
  string references, pytest fixtures injected by name) is its blind spot — the liveness checklist
  covers it.
- **pytest fixtures** — a "dead" function may be a fixture injected by parameter name; check
  `conftest.py` and fixture registries before flagging.

**Gates** — repo's configured runner (`pytest`, `python -m unittest`), `mypy`/`pyright` if
configured, `ruff check` as lint.

## Rust / Go / JVM

- **Rust** — the compiler is the primary detector: `cargo check` warns on unused items
  (`dead_code` lint); `cargo machete` or `cargo +nightly udeps` for unused deps. `pub` items get
  no warning — they need the manual sweep, and published-crate roots are public API.
- **Go** — unused imports/locals are compile errors already, so litter concentrates in unexported
  helpers: `staticcheck` (U1000) if present, else manual sweep. `go mod tidy -diff` shows unused
  module requirements without applying.
- **JVM** — rely on the repo's own static analysis if configured (IntelliJ inspections aren't
  scriptable here); otherwise manual sweep only, with reflection/DI (Spring annotations, Guice)
  treated as pervasive liveness risk — most findings cap at medium.

## Other / unknown stacks

No detector: manual seed-and-trace only, and say so in the report. Confidence caps at medium for
whole-file removals (no compiler to co-sign), except where the language runtime itself would have
failed (a missing import at load time) — those may stay high if gates exercise the load path.
