---
name: "submodule:init"
description: "Initialize a brand-new parent repository wrapping existing project folders as Git submodules. Combines `git init` + remote creation + multi-child submodule conversion in one guided flow."
argument-hint: "[<target-dir>] [--name <repo-name>] [--visibility public|private] [--no-parent-remote]"
allowed-tools: Skill(git-submodules), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Submodule Init

Create a brand-new parent (super) repository from a folder of existing projects, wrapping each project as a submodule.

Use this when:

- You have a folder of loose project directories — some git repos, some not — and you want a single umbrella repo tracking them all.
- You want to combine `git init` + `gh repo create` (for the parent) + submodule wiring (for each child) in one guided flow.

## Arguments

Parse from `$ARGUMENTS`:

```
[<target-dir>] [--name '<repo-name>'] [--visibility public|private] [--no-parent-remote]
```

- `<target-dir>` (optional) — directory to initialize; defaults to CWD
- `--name` — name to use when creating the parent's remote (default: basename of target-dir)
- `--visibility` — visibility for the parent (and any children that need publishing); default `private`
- `--no-parent-remote` — skip creating a remote for the parent (keep it local-only)

If `$ARGUMENTS` is empty, the skill runs the full interactive flow.

## Process

Invoke the `git-submodules` skill with `mode: init` and forward `$ARGUMENTS`.

The skill will:

1. **Survey & classify** each subfolder of the target directory:
   - Git repo with remote → ready to submodule
   - Git repo, no remote → needs publishing first
   - Not a git repo → ask whether to (a) init + publish as a new repo, (b) leave as a regular folder, or (c) skip
2. **Confirm the plan** — show the classification table and collect per-row decisions.
3. **Initialize the parent** — `git init` in the target directory, create an initial commit with a `README.md`, and (unless `--no-parent-remote`) create the remote via `gh repo create`.
4. **Publish missing remotes** for children — using `gh repo create --source=. --push` where `gh` is authed; manual URL prompt otherwise (see `references/remote-creation.md` inside the skill).
5. **Convert each git child** — same safe pattern as `/submodule:convert` (rename → re-add → checkout pinned SHA → diff → cleanup on confirm).
6. **Commit & report** — stage `.gitmodules` + all submodule paths in the parent; commit; print the summary.

If a `wiki/` directory exists at the repo root, append a single-line entry to `wiki/_log.md`.

## Examples

```bash
# Initialize a parent in the current directory, interactively
/submodule:init

# Initialize a parent for a specific folder with a chosen remote name
/submodule:init ./client-work --name acme-platform --visibility private

# Keep the parent local-only (no remote created)
/submodule:init ./scratch --no-parent-remote
```

## Notes

- This is the strict superset of `/submodule:convert` — it handles the case where the parent doesn't exist yet AND the children might be plain folders.
- Existing git repos with remotes are converted in place (their commit history is preserved).
- Plain folders that the user opts to "init + publish" get a fresh `git init` and an initial commit before publishing.
- The parent remote, when created, gets the contents of `.gitmodules` and the initial `README.md` — push history is one commit deep.
