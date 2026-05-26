---
name: "submodule:convert"
description: "Convert a directory containing multiple nested git repos into a clean submodule layout. Surveys nested repos, publishes any that lack remotes (via gh CLI), and re-adds each as a proper submodule of the parent."
argument-hint: "[<target-dir>] [--include <name,name>] [--exclude <name,name>] [--visibility public|private] [--force]"
allowed-tools: Skill(git-submodules), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Submodule Convert

Take a directory whose subfolders each contain their own `.git` and convert them into proper Git submodules of a parent repo.

## Arguments

Parse from `$ARGUMENTS`:

```
[<target-dir>] [--include 'name1,name2'] [--exclude 'name1,name2']
[--visibility public|private] [--force]
```

- `<target-dir>` (optional) — directory to scan; defaults to CWD
- `--include` — comma-separated list of child folder names to convert (overrides interactive selection)
- `--exclude` — comma-separated list of child folder names to skip
- `--visibility` — default visibility when publishing missing remotes via `gh repo create`
- `--force` — proceed even if the parent working tree is dirty

If `$ARGUMENTS` is empty, the skill runs the full interactive flow.

## Process

Invoke the `git-submodules` skill with `mode: convert` and forward `$ARGUMENTS`.

The skill will:

1. **Survey** — find every `.git` one level deep under the target directory; record each child's remote, branch, cleanliness, and HEAD SHA.
2. **Confirm** — show a table of findings and let the user accept/reject each row. Refuse dirty children.
3. **Publish missing remotes** — for children without `origin`, use `gh repo create --source=. --push` if `gh` is authenticated; otherwise prompt for an existing URL (see `references/remote-creation.md` inside the skill).
4. **Convert each child** — for each approved child:
   - Capture URL + SHA + branch
   - Ensure the SHA is pushed (`git branch -r --contains <SHA>`)
   - Rename to `<child>.pre-submodule` as a backup
   - Run `git submodule add -b <branch> <URL> <child>`
   - Check out the original SHA inside the new submodule
   - Diff the backup vs the new working tree; abort cleanup if there's drift
   - Remove the backup only after explicit confirmation
5. **Commit** — stage `.gitmodules` and all new submodule paths; commit.
6. **Report** — print converted, skipped, and any leftover backups.

If the target directory is not itself a git repo, the skill will ask whether to `git init` it now or whether the user wants `/submodule:init` instead — it does not silently initialize.

If a `wiki/` directory exists at the repo root, append a single-line entry to `wiki/_log.md`.

## Examples

```bash
# Convert everything one level under CWD, interactively
/submodule:convert

# Convert only specific children
/submodule:convert ./monorepo --include 'auth,billing,frontend'

# Pre-set visibility for any repos that need publishing
/submodule:convert ./projects --visibility private
```

## Safety Notes

- **Working trees must be clean.** Dirty submodules are skipped — the skill will not lose your work.
- **Unpushed commits are detected.** If a child has commits the remote doesn't have, the skill pushes first (or asks). Submodule pins must reference reachable commits.
- **Backups are kept until you confirm.** Each converted child is renamed to `<name>.pre-submodule` and only deleted after you approve the diff.
- **The parent repo is not pushed.** Run `git push` yourself when you're ready.
