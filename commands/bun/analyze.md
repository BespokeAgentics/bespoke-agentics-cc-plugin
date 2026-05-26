---
name: "bun:analyze"
description: "Read-only scan of a directory containing multiple sibling projects and produce a Bun workspace migration plan. Lists packages, proposes layout and scoped names, identifies hoist candidates and version conflicts, and surfaces git-posture options per child repo. No files are written."
argument-hint: "[<target-dir>]"
allowed-tools: Skill(bun-workspace), Bash, Read, Glob, Grep
---

# Bun Workspace — Analyze

Inspect a top-level directory that contains multiple sibling Node/Bun projects and produce a migration plan for turning it into a Bun workspace monorepo. **Read-only** — nothing is modified.

## Arguments

Parse from `$ARGUMENTS`:

```
[<target-dir>]
```

- `<target-dir>` (optional) — directory to scan; defaults to CWD.

## Process

Invoke the `bun-workspace` skill with `mode: analyze` and forward `$ARGUMENTS`.

The skill will:

1. **Scan** — list immediate subdirectories of the target. For each, record git status, `package.json` contents (name, scripts, deps), lockfile, and framework heuristic.
2. **Classify** — bucket each subdirectory as a workspace package, a non-package (excluded from the workspace), or an already-nested workspace (requires a decision before convert).
3. **Build the plan** — produce a markdown report covering:
   - Discovered packages table
   - Proposed workspace layout (flat vs `apps/*`+`packages/*`)
   - Name normalization (proposed scope + scoped names)
   - Dependency hoisting candidates and version conflicts
   - Overrides/resolutions reconciliation
   - Package manager unification (non-Bun lockfiles to be regenerated)
   - Git-posture options per child repo (submodule / absorb / leave alone)
   - Risks and open questions
4. **Stop** — print the report and instruct the user to run `/bun:convert` when ready.

## Examples

```bash
# Analyze the current directory
/bun:analyze

# Analyze a specific directory
/bun:analyze /Users/me/Projects/HOUSEPOWER
```

## Safety Notes

- This command **writes nothing**. It's always safe to run.
- If the target dir is itself a Bun workspace already, the skill switches tone and suggests `/bun:audit` instead.
