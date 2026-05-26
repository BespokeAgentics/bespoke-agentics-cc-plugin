---
name: "bun:convert"
description: "Execute the Bun workspace migration: per-child git posture decisions, optional layout moves, root scaffolding (package.json with workspaces, bunfig.toml, tsconfig.base.json, .gitignore), per-package edits (scope rename, hoisted-deps strip, nested lockfile removal), root `bun install`, and a smoke test. Interactive — every destructive step is announced and confirmed."
argument-hint: "[<target-dir>] [--layout flat|buckets] [--scope @org] [--force]"
allowed-tools: Skill(bun-workspace), Skill(git-submodules), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Bun Workspace — Convert

Convert a directory of sibling projects into a Bun workspace monorepo. Interview-driven; every destructive step is announced first and reversible via the safety branch.

## Arguments

Parse from `$ARGUMENTS`:

```
[<target-dir>] [--layout flat|buckets] [--scope @org] [--force]
```

- `<target-dir>` (optional) — directory to convert; defaults to CWD.
- `--layout` — skip the layout question with this preset.
- `--scope` — skip the scope question with this preset (e.g. `--scope @housepower`).
- `--force` — proceed even if the parent working tree is dirty (rare; the safety net works better with a clean tree).

If `$ARGUMENTS` is empty, the skill runs the full interactive flow.

## Process

Invoke the `bun-workspace` skill with `mode: convert` and forward `$ARGUMENTS`.

The skill will:

1. **Re-run analyze** — re-derive the plan and confirm with the user. Refuse to proceed on a dirty git tree (without `--force`) or with un-decided nested workspaces.
2. **Decisions** — interview via `AskUserQuestion`:
   - Per-child git posture (submodule / absorb / leave alone)
   - Workspace layout (flat-preserving / buckets)
   - Root package name
   - Per-child name normalization (apply chosen scope)
   - Lockfile / package-manager migration confirmation
   - Dependency hoisting choices (override which hoist candidates stay local)
3. **Safety net** — create branch `bun-workspace-migration` (or a tarball backup if the parent isn't a git repo).
4. **Git posture** — for "submodule" children, stop and route to `/submodule:convert`. For "absorb" children, `rm -rf <child>/.git` after one more confirmation. For "leave alone", no action.
5. **Layout moves** — only if buckets chosen.
6. **Root scaffold** — write `package.json`, `bunfig.toml` (only when peer-dep conflicts warrant `linker = "isolated"`), `tsconfig.base.json`, `.gitignore` from templates.
7. **Per-package edits** — rename to scoped name, strip hoisted deps, delete nested lockfile, extend shared tsconfig.
8. **Install + smoke test** — `bun install` from root, then `bun run --filter '*' typecheck` and `bun run --filter '*' test` where those scripts exist.
9. **Report + follow-up checklist** — no auto-commit; the user reviews and commits.

For the exact ordered command list and per-step rollback notes, the skill consults `references/conversion-recipe.md` internally.

## Examples

```bash
# Full interactive flow on CWD
/bun:convert

# Convert a specific dir, preset layout and scope
/bun:convert /Users/me/Projects/HOUSEPOWER --layout flat --scope @housepower
```

## Safety Notes

- **Working tree must be clean** (or pass `--force`). The safety branch only matters with a clean baseline.
- **Per-child `.git` removal is confirmed twice.** Once during the decision phase, once before `rm -rf`.
- **No auto-commit.** The skill leaves the staged migration on a `bun-workspace-migration` branch (or in your working tree) for you to review and commit.
- **Submodule children are deferred to `/submodule:convert`.** This skill never touches submodule mechanics directly.
- **Smoke test failures don't auto-rollback.** They're real signal you should investigate, not skill bugs.
