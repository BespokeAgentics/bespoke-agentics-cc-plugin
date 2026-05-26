---
name: "submodule:add"
description: "Add a remote repository as a Git submodule of the current repo. Wires .gitmodules, pins the commit, and commits the result."
argument-hint: "<url> [<path>] [--branch <branch>] [--name <name>] [--force]"
allowed-tools: Skill(git-submodules), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Submodule Add

Add a remote git repository as a submodule of the current repository.

## Arguments

Parse from `$ARGUMENTS`:

```
<url> [<path>] [--branch '<branch>'] [--name '<name>'] [--force]
```

- `<url>` (required if not asked interactively) — git URL (`https://…` or `git@…`)
- `<path>` (optional) — mount path inside the parent repo; defaults to the URL's basename without `.git`
- `--branch` (optional) — branch to track via `git submodule add -b <branch>`
- `--name` (optional) — logical name in `.gitmodules` (defaults to `<path>`)
- `--force` (optional) — proceed even if the parent working tree is dirty

If `$ARGUMENTS` is empty, the skill collects the URL and path interactively.

## Process

Invoke the `git-submodules` skill with `mode: add` and forward `$ARGUMENTS`.

The skill will:

1. **Preflight** — confirm CWD is inside a git repo, check `gh` availability, refuse a dirty parent tree unless `--force`.
2. **Validate inputs** — verify URL is reachable via `git ls-remote` (warn but allow if private/deferred-auth), refuse if mount path already exists.
3. **Execute** — run `git submodule add` with the branch flag if provided, then `git submodule update --init --recursive` for the new path.
4. **Commit** — stage `.gitmodules` + the submodule path, commit with `Add submodule: <path>`.
5. **Report** — print the pinned SHA, tracked branch, and the collaborator-side update command.

If a `wiki/` directory exists at the repo root, append a single-line entry to `wiki/_log.md`.

## Examples

```bash
/submodule:add https://github.com/anthropics/anthropic-sdk-python.git
/submodule:add git@github.com:me/utils.git vendor/utils --branch main
/submodule:add https://github.com/foo/bar.git libs/bar --name bar-lib
```

## Notes

- Collaborators must run `git submodule update --init --recursive` after they pull the parent commit.
- To later pull updates from the tracked branch: `git submodule update --remote -- <path>`.
- For diagnosing submodule issues afterward, use `/submodule:status`.
