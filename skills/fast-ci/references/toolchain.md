# TC* — Toolchain Swap Catalog

Facts verified July 2026. Versions move weekly — treat exact patch numbers as "current as of
writing" and re-verify anything that gates a decision. Fidelity legend: 🟢 drop-in ·
🔵 config migration · 🟡 partial · 🔴 blocked (conditions listed per entry).

## TC1 — TypeScript ≤6 → TypeScript 7 (native compiler) — usually the biggest single win

**Status:** GA July 8, 2026. The native Go compiler ships as plain `typescript` on npm with the
standard `tsc` binary — `npm i -D typescript@^7` and `npx tsc --noEmit` *is* the native compiler.
The `@typescript/native-preview` package (`tsgo` binary) is retired.

**Win:** 8–12x full typechecks (vscode 125.7s→10.6s; playwright 12.8s→1.47s). Slack: CI typecheck
7.5min→1.25min. Memory −6% to −26%.

```yaml
- run: npx tsc --noEmit            # or: npx tsc --build --noEmit for project references
```

CI-relevant flags: `--checkers N` (parallel check workers, default 4 — pin the value so output
ordering is identical across environments; lower to 1–2 on small runners), `--builders N`
(parallel project-reference builds), `--singleThreaded`.

**Caveats (this is where 🟡/🔴 comes from):**
- TS 6.0 deprecations are **hard errors** in 7: `baseUrl` removed, `strict` defaults true,
  `module: esnext` default, `rootDir` defaults `./`, `types` defaults `[]`. Budget a tsconfig
  migration pass.
- **No programmatic API in 7.0** (lands in 7.1). Anything Volar-based — Vue, Svelte, Astro, MDX
  — must stay on 6.x → 🔴 blocked, unblock condition "TS 7.1 API".
- Tools needing the old API (some typescript-eslint setups) use the side-by-side alias:

```json
{
  "devDependencies": {
    "@typescript/native": "npm:typescript@^7.0.2",
    "typescript": "npm:@typescript/typescript6@^6.0.2"
  }
}
```

## TC2 — Prettier → oxfmt (oxc)

**Status:** beta (v0.58.x). Passes **100% of Prettier's JS/TS conformance tests**; >30x faster
than Prettier, ~3x faster than Biome's formatter. Formats JS/TS/JSX/JSON/YAML/TOML/HTML/Vue/CSS/
Markdown/GraphQL; built-in Tailwind class sorting and import sorting. Config: `.oxfmtrc.json`.
Adopters: vuejs/core, vercel/turborepo, sentry-javascript.

```sh
pnpm add -D oxfmt
pnpm oxfmt --migrate prettier    # converts .prettierrc; also: --migrate biome
pnpm oxfmt                       # write; CI check: oxfmt --check
```

**Fidelity:** 🔵 for JS/TS. 🟡 if the repo formats file types oxfmt doesn't cover or leans on
Prettier plugins beyond Tailwind sorting. Beta status is an interview item, not a unilateral call.

## TC3 — ESLint → oxlint (oxc)

**Status:** stable since June 2025 (v1.7x line). 50–100x faster than ESLint; ~2x faster than
Biome. Type-aware linting: alpha. JS plugins: alpha. Config: `.oxlintrc.json`.

```sh
npx oxlint --init            # fresh config
npx @oxlint/migrate          # convert existing ESLint config
```

**Fidelity:** 🔵 for the common rule surface. 🟡 when niche ESLint plugins matter — use the
hybrid: oxlint first for the 99% path, keep a slimmed ESLint for the residual rules with
`eslint-plugin-oxlint` disabling everything oxlint already covers. The hybrid still removes
ESLint from the agent's hot loop (run residual ESLint in the merge queue or post-merge).

## TC4 — Or: Biome 2.x (one tool for lint + format)

**Status:** stable (2.3.x). Type-aware rules without tsc; Vue/Svelte/Astro SFC support since 2.3.
`npx biome init` → `biome.json`; CI: `npx biome ci .` (lint + format-check in one step).

**Choosing TC2/TC3 vs TC4:** oxlint+oxfmt = maximum speed and best ESLint/Prettier drop-in
fidelity → default for *existing* codebases. Biome = one stable tool, one config → fine default
for greenfield or teams that value simplicity over the last 2–3x. Do not install both stacks.

## TC5 — pip/poetry/venv → uv (Astral)

**Status:** stable de-facto standard (0.11.x). 10–100x faster than pip. `pyproject.toml` +
`uv.lock`; `uv sync --locked` fails if the lockfile is stale — exactly what CI wants.

```yaml
- uses: astral-sh/setup-uv@v8
  with:
    enable-cache: true
    cache-dependency-glob: "uv.lock"
    python-version: "3.13"
- run: uv sync --locked --all-extras --dev
- run: uv run pytest
```

Migration from poetry/pip-tools: `uvx migrate-to-uv` handles most layouts; verify `[tool.uv]`
extras/groups by diffing the resolved environment (`uv pip list` vs old freeze).

## TC6 — flake8/black/isort/pyupgrade → ruff

**Status:** stable-in-practice (0.15.x). One binary replaces the lot.

```yaml
- run: uv run ruff check --output-format=github .
- run: uv run ruff format --check .
```

Config in `pyproject.toml [tool.ruff]`. 🔵 — rule mapping is documented and the migration is
mechanical.

## TC7 — mypy → ty (Astral) — sidecar only

**Status:** **beta** (0.0.x, diagnostics still churn between releases; 1.0 targeted 2026, not
shipped). 10–60x faster than mypy/Pyright. The honest pattern until 1.0:

```yaml
- run: uvx ty check            # fast, informational, non-blocking
- run: uv run mypy .           # remains the required gate
```

Agents get the fast signal locally (`uvx ty check` in the verify script); the blocking gate stays
trustworthy. 🟡 by construction — promoting ty to the gate before 1.0 is a 🔴 unless the user
explicitly accepts diagnostic churn.

## TC8 — Jest → bun test / npm → pnpm or bun install

**bun test** (stable, 1.3.x): Jest-compatible runner, runs many suites unmodified, dramatically
faster startup. 🟡 — verify the suite actually passes under bun (mocks, node-specific APIs,
custom transforms are the usual gaps) before switching the CI step; keep the runtime you deploy
on for integration tests.

**Installs:** `oven-sh/setup-bun@v2` + `bun install --frozen-lockfile`, or pnpm's
content-addressed store + `--frozen-lockfile`. Framing that holds up: bun is fastest, pnpm is
strictest about dependency isolation. Either beats npm in CI; pick one, cache the store.

## TC9 — Supporting cast (one-liners)

- **Turborepo remote cache** — free on Vercel-linked repos; external CI via `TURBO_TOKEN` +
  `TURBO_TEAM`; self-host against S3/R2 via `@turborepo/remote-cache`. Unchanged packages cost ~0.
- **Nx** — `nx affected -t build test lint`; note self-hosted/third-party remote cache requires
  Powerpack licensing since 19.7.
- **mise** — Rust polyglot version manager (replaces asdf/nvm/pyenv) + task runner;
  `jdx/mise-action@v2`. One `mise.toml` pins every tool the agent needs.
- **lefthook** — Go git-hooks manager (replaces husky+lint-staged), parallel execution; pairs
  naturally with oxlint/oxfmt so the pre-commit hook costs milliseconds.
- **zizmor** — Rust static analyzer for GitHub Actions workflows; `uvx zizmor .github/workflows/`
  — run it on every workflow this skill writes or edits.
- **Bundlers** — Vite 8 ships Rolldown (Rust) by default; Rspack for webpack-API repos; swc
  inside Next.js. Only touch the bundler if builds gate the agent loop — usually typecheck/lint
  dominate.
