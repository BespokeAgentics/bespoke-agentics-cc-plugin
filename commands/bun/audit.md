---
name: "bun:audit"
description: "Health-check an existing Bun workspace. Verifies workspace globs resolve, no duplicate package names, no nested lockfiles, overrides only at root, `private: true` on root, no version drift, and that each package extends the shared tsconfig. Read-only by default; pass `--fix` to apply the safe corrections."
argument-hint: "[<target-dir>] [--fix]"
allowed-tools: Skill(bun-workspace), Bash, Read, Edit, Glob, Grep
---

# Bun Workspace — Audit

Validate that an existing Bun workspace is healthy. Surfaces drift, configuration smells, and obsolete files.

## Arguments

Parse from `$ARGUMENTS`:

```
[<target-dir>] [--fix]
```

- `<target-dir>` (optional) — workspace root to audit; defaults to CWD.
- `--fix` — apply the safe corrections (delete nested lockfiles, add missing `tsconfig.json#extends`, set `private: true` on root). Anything ambiguous (e.g. version drift resolution) still requires user input.

## Process

Invoke the `bun-workspace` skill with `mode: audit` and forward `$ARGUMENTS`.

The skill will check:

1. **Workspace globs resolve.** Every glob in `package.json#workspaces` matches a directory containing `package.json`. Stale globs are flagged.
2. **No duplicate package names.** Confirms `bun pm ls` runs clean.
3. **No nested lockfiles.** Workspace children must not have their own `bun.lock`, `package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock`.
4. **Overrides only at root.** Any child setting `overrides`/`resolutions` is flagged — Bun only honors them at the root.
5. **`private: true` at the root.** A workspace root that's accidentally publishable is a footgun.
6. **No version drift.** Same dep at multiple versions across packages, or root vs child mismatch on a hoisted dep.
7. **Shared tsconfig extension.** If `tsconfig.base.json` exists at the root, each package's `tsconfig.json` should `extends` it.

The report mirrors the `analyze` table format. With `--fix`, the safe corrections are applied and re-checked.

## Examples

```bash
# Read-only audit
/bun:audit

# Audit + apply safe corrections
/bun:audit --fix

# Audit a specific workspace root
/bun:audit /Users/me/Projects/my-monorepo
```

## Safety Notes

- Without `--fix`, the command writes nothing.
- `--fix` only touches the safe corrections (delete obvious junk, set obvious defaults). Version-drift resolution is never automatic.
