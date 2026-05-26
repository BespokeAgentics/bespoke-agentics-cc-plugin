---
name: "submodule:status"
description: "Health-check every Git submodule in the current repo. Read-only — reports detached HEAD, drift, dirty state, unreachable remotes, and pinned-vs-HEAD mismatches with copy-paste remediation commands."
argument-hint: "[--path <submodule-path>] [--no-fetch]"
allowed-tools: Skill(git-submodules), Bash, Read, Glob, Grep
---

# Submodule Status

Run a read-only health check on every submodule in the current repository.

## Arguments

Parse from `$ARGUMENTS`:

```
[--path '<submodule-path>'] [--no-fetch]
```

- `--path` — check only one specific submodule (default: all)
- `--no-fetch` — skip remote-reachability checks (faster, useful offline)

## Process

Invoke the `git-submodules` skill with `mode: status` and forward `$ARGUMENTS`.

The skill will:

1. **List submodules** via `git submodule status --recursive`.
2. **Collect facts per submodule** — pinned SHA, actual HEAD SHA, tracked branch (from `.gitmodules`), detached-HEAD state, dirty state, drift (pinned ≠ HEAD), remote reachability, and whether the pinned SHA is on the tracked branch upstream.
3. **Classify each row** — 🟢 Healthy / 🟡 Detached / 🟠 Drifted / 🔴 Dirty / 🔴 Broken.
4. **Print a table** with the exact remediation command per row. Does NOT run any fixes.

If the repo has no submodules, the skill says so and suggests `/submodule:add` or `/submodule:convert`.

## Examples

```bash
# Check every submodule
/submodule:status

# Check only one
/submodule:status --path vendor/auth-sdk

# Offline / fast check (skip remote pings)
/submodule:status --no-fetch
```

## What the statuses mean

- **🟢 Healthy** — on the tracked branch, clean, pinned SHA matches HEAD, remote reachable.
- **🟡 Detached** — detached HEAD but otherwise clean. Normal after `git submodule update`; only matters if you intend to commit inside the submodule.
- **🟠 Drifted** — HEAD ≠ pinned SHA. Someone committed in the submodule without updating the parent's pin. Either bump the pin (`git add <path> && git commit`) or reset (`git submodule update --init -- <path>`).
- **🔴 Dirty** — uncommitted changes inside the submodule. Commit or stash inside the submodule, then re-check status.
- **🔴 Broken** — remote unreachable, or pinned SHA not present locally. Most often caused by force-pushes to the child repo. See `references/troubleshooting.md` inside the skill.

## Notes

- This command never modifies the repo. Safe to run anytime.
- For automation, the skill prints both a human-readable table and, when run with no other interaction needed, a brief stable summary line (`N healthy, M detached, K drifted, ...`).
