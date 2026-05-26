---
name: "bun:add"
description: "Scaffold a new package into an existing Bun workspace: writes `package.json` with the workspace's scope, `tsconfig.json` extending the shared base, and a `src/index.ts` stub. Verifies the chosen path is covered by a workspace glob (prompts to add one if not). Runs `bun install` from the root."
argument-hint: "<package-path> [--name <name>] [--kind library|app]"
allowed-tools: Skill(bun-workspace), AskUserQuestion, Bash, Read, Write, Edit, Glob
---

# Bun Workspace — Add Package

Add a new package to an existing Bun workspace. Lightweight wrapper around `bun init` that handles the workspace-aware bits: scoped name, tsconfig extension, glob coverage.

## Arguments

Parse from `$ARGUMENTS`:

```
<package-path> [--name <name>] [--kind library|app]
```

- `<package-path>` (required) — where to place the new package, relative to the workspace root. Examples: `packages/utils`, `apps/admin`.
- `--name` — explicit package name. Defaults to `@<rootscope>/<basename>` derived from `<package-path>`.
- `--kind` — `library` (default) or `app`. Controls the default scripts.

If `<package-path>` is missing, the skill asks via `AskUserQuestion`.

## Process

Invoke the `bun-workspace` skill with `mode: add` and forward `$ARGUMENTS`.

The skill will:

1. **Verify workspace root.** Confirm CWD (or the resolved root from the path) is a Bun workspace.
2. **Check glob coverage.** Confirm the chosen path is covered by a glob in `package.json#workspaces`. If not, propose adding one and confirm.
3. **Scaffold files**:
   - `<path>/package.json` — chosen name, `version: "0.0.0"`, `private: true` for apps, minimal scripts based on `--kind`.
   - `<path>/tsconfig.json` — extends the workspace's `tsconfig.base.json` if it exists.
   - `<path>/src/index.ts` — one-line stub.
4. **Install.** Run `bun install` from the workspace root so the new package is linked.

## Examples

```bash
# Add a library at packages/utils
/bun:add packages/utils

# Add an app at apps/admin with explicit name
/bun:add apps/admin --name @myorg/admin-dashboard --kind app
```

## Safety Notes

- Only writes inside `<package-path>`. The only root-level write is to `package.json#workspaces` if the glob needs adding (confirmed first).
- Does not overwrite an existing `package.json` at the target path — aborts with a clear message instead.
