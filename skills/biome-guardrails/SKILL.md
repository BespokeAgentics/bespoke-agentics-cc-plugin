---
name: biome-guardrails
description: "Install Biome.js + sidecar ESLint as strict AI-code guardrails in a JS/TS project. Triggers: 'add Biome', 'set up linting', 'enforce code quality', 'lint guardrails'."
---

<objective>
Set up Biome.js with strict, enforced code quality rules designed to constrain AI-generated code. Installs Biome with native rules (complexity, correctness, style, suspicious), a sidecar ESLint config for structural rules Biome does not yet cover (line limits, param counts, no-comments), package.json lint scripts, and optional Claude Code hooks for config protection and real-time lint feedback on edits.
</objective>

<quick_start>
Most common invocation — install everything with defaults:

```
/bespokeagentics:biome-guardrails
```

Skip ESLint sidecar (Biome-only):
```
/bespokeagentics:biome-guardrails --no-eslint
```

Skip Claude Code hooks:
```
/bespokeagentics:biome-guardrails --no-hooks
```

Custom source directory:
```
/bespokeagentics:biome-guardrails --src app/
```
</quick_start>

<input>
Parse from `$ARGUMENTS`:

- `--no-eslint` (optional): Skip the sidecar ESLint config and its dependencies
- `--no-hooks` (optional): Skip Claude Code hook setup
- `--src <path>` (optional): Source directory for ESLint to target (default: `src/`)

If `$ARGUMENTS` is empty, install everything with defaults.
</input>

<phase_1 name="Project Discovery">

Before making any changes, scan the project to understand its current state.

**1a. Detect Package Manager**

Check for lock files in priority order:
1. `bun.lockb` or `bun.lock` → bun
2. `pnpm-lock.yaml` → pnpm
3. `yarn.lock` → yarn
4. `package-lock.json` → npm

If no lock file exists, default to `npm`.

Set `PM` to the detected package manager and `PMX` to its exec command:
- npm → npx
- yarn → yarn dlx
- pnpm → pnpm dlx
- bun → bunx

**1b. Check Existing State**

| Check | How |
|-------|-----|
| `package.json` exists | Read root `package.json` |
| Biome already installed | Check `devDependencies` for `@biomejs/biome` |
| `biome.json` or `biome.jsonc` exists | Glob for `biome.json*` at root |
| ESLint already configured | Check for `eslint.config.*`, `.eslintrc*`, or `eslint` in devDependencies |
| Existing lint scripts | Read `scripts` from `package.json` |
| `.claude/` directory exists | Check for `.claude/settings.json` or `.claude/settings.local.json` |
| Source directory | Verify `--src` path exists, or check for `src/`, `app/`, `lib/` |

**1c. Pre-flight Report**

```
=== Biome AI Guardrails — Pre-flight ===
Package manager:    {PM}
package.json:       {exists / will create}
Biome installed:    {yes (v{version}) / no — will install}
biome.json:         {exists — will overwrite / will create}
ESLint sidecar:     {will install / skipped (--no-eslint)}
Claude Code hooks:  {will install / skipped (--no-hooks)}
Source directory:    {path}
=========================================
```

If `package.json` does not exist, abort with:
```
ERROR: No package.json found. Run `{PM} init` first, then re-run this command.
```

</phase_1>

<phase_2 name="Install Dependencies">

**2a. Install Biome**

If `@biomejs/biome` is NOT in devDependencies:

```bash
{PM} add -D @biomejs/biome
```

Use the correct install command for the detected package manager:
- npm: `npm install -D`
- yarn: `yarn add -D`
- pnpm: `pnpm add -D`
- bun: `bun add -d`

**2b. Install ESLint Sidecar Dependencies (unless `--no-eslint`)**

If the `--no-eslint` flag was NOT provided:

```bash
{PM} add -D eslint eslint-plugin-no-comments eslint-plugin-better-max-params
```

</phase_2>

<phase_3 name="Configure Biome">

Read the reference file at `references/biome-config.json` and write it to the project root as `biome.json`.

If a `biome.json` already exists, **overwrite it** — the user explicitly invoked this command to apply guardrails.

The reference config includes:

**Formatter:**
- 2-space indent, 100 char line width
- Double quotes, trailing commas, semicolons always

**Linter — Native Biome rules (all set to `error`):**

| Category | Rules |
|----------|-------|
| complexity | `noExcessiveCognitiveComplexity` (max 10), `noForEach`, `useFlatMap`, `useSimplifiedLogicExpression` |
| correctness | `noUnusedVariables`, `noUnusedImports`, `useExhaustiveDependencies` |
| style | `noVar`, `useConst`, `useTemplate`, `useShorthandAssign`, `useSingleVarDeclarator`, `useNamingConvention` |
| suspicious | `noConsoleLog`, `noExplicitAny`, `noDoubleEquals`, `noImplicitAnyLet` |
| nursery | `noSecrets` (warn), `noMagicNumbers` (warn) |

**Import organization:** enabled

After writing, verify the config is valid:
```bash
{PMX} biome check --max-diagnostics=0 biome.json
```

If the check command fails with an unknown rule error, read the error output and remove the offending rule from `biome.json`. Report the removed rule to the user — this can happen when the installed Biome version does not support a nursery rule.

</phase_3>

<phase_4 name="Configure ESLint Sidecar">

**Skip this phase entirely if `--no-eslint` was provided.**

Read the reference file at `references/eslint-sidecar-config.mjs` and write it to the project root as `eslint.ai-guardrails.mjs`.

This config covers rules Biome cannot enforce natively:

| Rule | ESLint Implementation |
|------|----------------------|
| No comments | `eslint-plugin-no-comments` → `disallowComments: error` |
| Max 2 function params | `eslint-plugin-better-max-params` → `func: 2, constructor: 10` |
| Max 50 lines per function | `max-lines-per-function` → `max: 50, skipBlankLines: true` |
| Max 250 lines per file | `max-lines` → `max: 250, skipBlankLines: true` |
| Max nesting depth 4 | `max-depth` → `4` |
| Max 20 statements | `max-statements` → `20` |
| Max 1 class per file | `max-classes-per-file` → `1` |
| Min identifier length 2 | `id-length` → `min: 2, exceptions: ["_"]` |
| No `process.env` access | `no-restricted-syntax` targeting `process.env` member expressions |
| No magic numbers | `no-magic-numbers` (stricter fallback for Biome nursery rule) |

If `--no-eslint` was provided but the user still wants no-comment enforcement, the skill includes a standalone script at `scripts/check-no-comments.sh` that can be added as a manual package.json script. Mention this in the summary.

</phase_4>

<phase_5 name="Update package.json Scripts">

Read the current `package.json`, then update the `scripts` section. Preserve any existing scripts that do not conflict.

**If ESLint sidecar is installed:**

```json
{
  "scripts": {
    "lint": "biome check . && eslint --config eslint.ai-guardrails.mjs {SRC_DIR}/",
    "lint:fix": "biome check --write . && eslint --fix --config eslint.ai-guardrails.mjs {SRC_DIR}/",
    "format": "biome format --write .",
    "ci": "biome ci . && eslint --config eslint.ai-guardrails.mjs {SRC_DIR}/"
  }
}
```

**If ESLint sidecar is skipped (`--no-eslint`):**

```json
{
  "scripts": {
    "lint": "biome check .",
    "lint:fix": "biome check --write .",
    "format": "biome format --write .",
    "ci": "biome ci ."
  }
}
```

Replace `{SRC_DIR}` with the detected or specified source directory.

If any of these script names already exist, **overwrite them** — the user explicitly invoked this command to set up guardrails.

Write the updated `package.json` back, preserving all other fields.

</phase_5>

<phase_6 name="Set Up Claude Code Hooks">

**Skip this phase entirely if `--no-hooks` was provided.**

Set up two hooks in the project's `.claude/settings.local.json`.

**6a. Config Protection Hook (PreToolUse)**

Read the template at `templates/protect-config-hook.sh`. This hook blocks any Edit or Write tool call targeting `biome.json`, `eslint.ai-guardrails.mjs`, or any ESLint config file.

Write the script to `.claude/scripts/protect-lint-config.sh` and make it executable (`chmod +x`).

**6b. Lint-on-Edit Feedback Hook (PostToolUse)**

Read the template at `templates/lint-on-edit-hook.sh`. This hook runs `biome check` after every Edit or Write to `.ts`/`.tsx`/`.js`/`.jsx` files and feeds lint errors back to the agent. Includes a 3-strike circuit breaker.

Write the script to `.claude/scripts/lint-on-edit.sh` and make it executable (`chmod +x`).

**IMPORTANT:** Before writing the lint-on-edit script, replace the hardcoded `npx` on lines 12 and 21 with the detected `PMX` value from Phase 1. This ensures the hook uses the correct package manager exec command (e.g., `bunx biome check` for bun projects).

**6c. Register Hooks**

Read `.claude/settings.local.json` if it exists. Add or merge the hook entries:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/scripts/protect-lint-config.sh",
            "timeout": 5000
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/scripts/lint-on-edit.sh",
            "timeout": 15000
          }
        ]
      }
    ]
  }
}
```

If `.claude/settings.local.json` already has hooks, merge the new entries into the existing arrays without duplicating. Do NOT overwrite existing hooks.

</phase_6>

<phase_7 name="Verify Installation">

Run a quick verification:

1. Run `{PMX} biome check --max-diagnostics=0 .` to verify Biome is working
2. If ESLint was installed, run `{PMX} eslint --config eslint.ai-guardrails.mjs --max-warnings=0 {SRC_DIR}/` to verify ESLint is working
3. If hooks were installed, verify the script files exist and are executable

Report any errors and suggest fixes.

</phase_7>

<phase_8 name="Summary Report">

Print a final summary:

```
================================================================
  Biome AI Guardrails — Installed Successfully
================================================================

Package manager:    {PM}
Biome version:      {version}

Files created/updated:
  biome.json                    — Biome config with AI guardrails
  {eslint.ai-guardrails.mjs    — ESLint sidecar for gap rules}
  {.claude/scripts/protect-lint-config.sh — Config protection hook}
  {.claude/scripts/lint-on-edit.sh        — Lint feedback hook}
  {.claude/settings.local.json            — Hook registration}
  package.json                  — Updated lint scripts

Biome Native Rules (enforced):
  Cognitive complexity <= 10    No console.log
  No unused vars/imports        Strict equality (===)
  No explicit any               No var (use const/let)
  Naming conventions            Import organization
  No forEach (use for...of)     Template literals

{ESLint Sidecar Rules (enforced):
  No comments                   Max 2 function params
  Max 50 lines/function         Max 250 lines/file
  Max depth 4                   Max 20 statements
  Max 1 class/file              Min identifier length 2
  No process.env access         No magic numbers}

{Claude Code Hooks:
  Config protection — blocks edits to lint config files
  Lint-on-edit      — runs Biome after every file edit}

Scripts:
  {PM} run lint          — Check all rules
  {PM} run lint:fix      — Auto-fix what's possible
  {PM} run format        — Format all files
  {PM} run ci            — CI pipeline check

================================================================
```

Only show sections that were actually installed. Omit ESLint section if `--no-eslint`, omit hooks section if `--no-hooks`.

If `--no-eslint` was provided, mention that a standalone no-comments check script is available at `scripts/check-no-comments.sh` as a lightweight alternative.

</phase_8>

<coverage_matrix>
For the full rule coverage matrix (which rules are Biome native vs ESLint sidecar), read `references/coverage-matrix.md`. Consult it when the user asks about which rules are handled where.
</coverage_matrix>

<error_handling>

- **No `package.json`**: Abort with clear message to run `{PM} init` first
- **Biome install fails**: Report the error; suggest checking Node.js version (requires >= 16)
- **ESLint plugin not found**: Report; suggest running install command manually
- **biome.json has unknown rules**: Auto-remove the offending rule and warn the user (Biome version may be older)
- **Hooks directory doesn't exist**: Create `.claude/` and `.claude/scripts/` as needed
- **Existing hooks in settings.local.json**: Merge without overwriting

</error_handling>

<key_behaviors>

- **ALWAYS detect the package manager** — never assume npm
- **ALWAYS verify after install** — run the lint tools to confirm they work
- **Overwrite configs when invoked** — this command represents an intentional setup
- **Merge hooks, NEVER overwrite** — respect existing hook configurations
- **Report everything** — the user should know exactly what was created and changed

</key_behaviors>

<success_criteria>

The skill is complete when ALL of the following are true:

1. `biome.json` exists at project root with all guardrail rules and `biome check` exits cleanly on it
2. `package.json` has `lint`, `lint:fix`, `format`, and `ci` scripts
3. If ESLint sidecar was installed: `eslint.ai-guardrails.mjs` exists at project root and `eslint --config eslint.ai-guardrails.mjs` runs without config errors
4. If hooks were installed: `.claude/scripts/protect-lint-config.sh` and `.claude/scripts/lint-on-edit.sh` are present and executable, and `.claude/settings.local.json` has the hook registrations
5. Summary report was printed showing all created files and available scripts

</success_criteria>
