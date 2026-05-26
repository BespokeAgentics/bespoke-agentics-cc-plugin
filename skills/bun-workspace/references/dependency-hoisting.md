# Dependency Hoisting

Rules for deciding which deps move to the workspace root and how to resolve conflicts. The goal is one source of truth per dependency without losing per-package flexibility where it matters.

## What hoists by default

A dep should hoist to the root when **all** of the following are true:

- It appears in ≥ 2 workspace packages.
- The semver ranges have a common satisfying version (matching major and ideally matching minor).
- It's not a *peer* dependency that must be installed exactly once at the consumer (e.g., `react`, `react-dom` — those should hoist *and* be added to `peerDependencies` of any package that uses them).

When you hoist, **remove the dep from each child's `package.json`** and add it once to root. Bun's flat `node_modules` makes it visible to every workspace.

## What does NOT hoist

- **Different majors.** If app A has `react@18` and app B has `react@19`, hoisting picks one and silently breaks the other. Either split (each declares its own version, no root entry) or upgrade both. Surface the choice; never decide silently.
- **Build-time-only deps that diverge.** If two packages use different `vite` majors, keep each version local.
- **Deps with native bindings.** Sometimes hoisting native modules works; sometimes the wrong arch gets resolved when invoked from a child's `bin`. If a dep has a `binary`/`postinstall` step and you're unsure, leave it local for the first migration and consolidate later.

## Conflict resolution

When the same dep appears at multiple versions across packages, choose one strategy per conflict:

1. **Pick highest** — usually the right move for libraries that follow semver. Update lower-version packages and add a note to the migration report; let the user verify their code still compiles.
2. **Force via `overrides`** — for transitive deps you don't directly depend on (e.g. `ws` overrides for security advisories), set the version at the root `overrides` field. This is the pattern HOUSEPOWER already uses with `ws`.
3. **Keep local, don't hoist** — when neither pick-highest nor overrides is safe, leave the dep in each child. The cost is a duplicated entry in `bun.lock`; that's acceptable.

## Example: HOUSEPOWER hoist plan

Given the analyze findings:

| Dep                       | Found in                             | Version             | Decision                                |
| ------------------------- | ------------------------------------ | ------------------- | --------------------------------------- |
| `convex`                  | app, cms, listings                   | `^1.13.2` everywhere | **Hoist** at `^1.13.2`                  |
| `typescript`              | all 4                                | `^5.4.5` everywhere | **Hoist** at `^5.4.5` as devDep         |
| `vitest`                  | cms, listings, portal                | `^4.x`              | **Hoist** at `^4.x` as devDep           |
| `zod`                     | cms, listings                        | `^3.23.8`           | **Hoist** at `^3.23.8`                  |
| `@aws-sdk/client-s3`      | cms, listings                        | matching            | **Hoist**                               |
| `ws`                      | (override only) cms, listings, portal | override range      | **Hoist `overrides.ws` to root**        |

If any of the above had mismatched majors, the dep would move to the conflicts table instead of the hoist table.

## DevDeps vs deps

Hoisted **devDependencies** (typescript, vitest, eslint, prettier) are nearly always safe — they're build-time tools. Hoisted **dependencies** (runtime libs like `convex`, `zod`) need slightly more care because they ship to production. The rule is the same — matching majors → hoist — but spend an extra moment confirming the chosen version is correct for *all* consumers.

## Per-package overrides after hoisting

If a single package genuinely needs a different version of a hoisted dep, *don't* re-add it to that package's `dependencies` — Bun's resolver will get confused. Instead either:

- Pin the special version in root `overrides` keyed to that specific package, or
- Un-hoist the dep entirely and keep separate per-package declarations.

In practice this is rare. If it comes up often, the workspace boundary is probably wrong.
