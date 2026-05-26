# Conversion Recipe

The ordered command list for the convert mode write phase, with rollback notes per step. Use this as the script the skill is running — print each command to the user before executing.

Variables used below (substitute in actual values from the decisions in convert Phase 2):

- `$ROOT` — absolute path of the parent directory
- `$WORKSPACES` — JSON array of workspace globs (e.g. `["housepower-app", "housepower-cms", ...]`)
- `$ROOT_NAME` — chosen root package name
- `$SCOPE` — chosen org scope (`@housepower` etc.)

## Step 0 — Preflight (already done in Common Preflight)

- CWD printed
- Bun version checked
- Git context recorded
- Tree confirmed clean (or `--force`)

## Step 1 — Safety net

If `$ROOT` is a git repo:

```bash
cd "$ROOT"
git checkout -b bun-workspace-migration
```

If not a git repo:

```bash
tar -czf "$(dirname $ROOT)/$(basename $ROOT)-pre-bun-workspace.tgz" -C "$(dirname $ROOT)" "$(basename $ROOT)"
echo "Backup written to $(dirname $ROOT)/$(basename $ROOT)-pre-bun-workspace.tgz"
```

**Rollback.** `git checkout main && git branch -D bun-workspace-migration` (git case) or `tar -xzf <backup> -C ..` (tarball case).

## Step 2 — Per-child git posture

For each child the user marked "absorb":

```bash
ls -la "$ROOT/<child>/.git"   # show what will be removed
# Confirm with the user one more time
rm -rf "$ROOT/<child>/.git"
```

For each child marked "submodule": this should have been handled by `/submodule:convert` in Phase 1; do nothing here.

For "leave alone": nothing.

**Rollback.** None for absorb — the child .git is gone. This is why Step 1's safety net matters. Document in the report which children were absorbed.

## Step 3 — Layout moves (only if buckets chosen)

```bash
mkdir -p "$ROOT/apps" "$ROOT/packages"
git -C "$ROOT" mv "<child>" "apps/<child>"   # or packages/<child>
```

If not a git repo, use plain `mv`. Repeat per child.

**Rollback.** `git checkout .` (git case) or reverse the `mv` (non-git case).

## Step 4 — Root scaffold

Write four files from templates, substituting `$ROOT_NAME`, `$WORKSPACES`, the hoisted-deps tables from analyze, etc.

```bash
# Write root package.json
# (Use the Write tool with templates/root-package.json.tmpl as source, substituted)

# Write bunfig.toml (only if peer-dep conflicts were detected; otherwise skip)
# Write tsconfig.base.json
# Merge or create .gitignore
```

**Rollback.** Delete the four written files. Step 1's safety net catches this.

## Step 5 — Per-package edits

For each workspace package:

```bash
# Rewrite name in package.json
# (Use Edit tool: replace "name": "<old>" with "name": "@$SCOPE/<base>")

# Remove hoisted deps (one Edit per dep block)
# Delete local lockfile
rm -f "<pkg>/package-lock.json" "<pkg>/pnpm-lock.yaml" "<pkg>/yarn.lock" "<pkg>/bun.lock" "<pkg>/bun.lockb"

# Update tsconfig.json to extend ../../tsconfig.base.json
# (Use Edit tool)
```

**Rollback.** Step 1.

## Step 6 — Install

```bash
cd "$ROOT"
bun install
```

Capture stderr separately to surface peer warnings to the user. A nonzero exit means resolution failed — surface immediately, do not proceed to Step 7.

**Rollback.** Step 1.

## Step 7 — Smoke test

For each workspace, if the script exists, run it from the root:

```bash
cd "$ROOT"
bun run --filter '*' typecheck 2>&1 || true
bun run --filter '*' test 2>&1 || true
```

Use `|| true` because individual workspace failures shouldn't kill the report. Tabulate which packages passed which scripts.

**Don't roll back on test failures.** The migration is mechanically complete; failures here are real issues for the user to address (often missing deps that were transitively present before, or scripts that assumed a different CWD). Surface them clearly with the recovery branch name so the user can decide.

## Step 8 — Report and commit (do not auto-commit)

Print a summary:

```
Bun workspace migration complete.
Branch:       bun-workspace-migration
Packages:     N
Hoisted deps: M
Smoke tests:  X/Y passed

Next: review the diff (git diff main), commit when satisfied, push.
```

Do **not** run `git commit` automatically. The user reviews and commits.

## Rollback as a whole

If anything went wrong before Step 6 (the install), the safety net from Step 1 fully restores. After Step 6, the lockfile is regenerated — rolling back via git is still complete (the safety branch is intact) but the user should think before discarding a successful resolution.

If the user wants to abandon after Step 7 failures:

```bash
cd "$ROOT"
git checkout main
git branch -D bun-workspace-migration
# or, for the tarball case:
cd ..
rm -rf "$ROOT"
tar -xzf "$(basename $ROOT)-pre-bun-workspace.tgz"
```
