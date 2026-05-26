# Lockfile Migration

How to move a package from npm / pnpm / yarn to Bun without losing important resolutions. Read this when at least one child has a non-Bun lockfile.

## The general flow

Bun *will* generate its own lockfile from `package.json` and resolve fresh. You don't need to translate the old lockfile; you need to surface what the old lockfile encoded that `package.json` alone doesn't capture.

Order of operations for each non-Bun package:

1. Read the existing lockfile to spot anything surprising (pinned transitive versions, security overrides, peer-dep workarounds).
2. Ensure those decisions are preserved either by promoting them to the root `overrides`/`resolutions`, by tightening the dep range in `package.json`, or by accepting Bun's resolution (which is usually fine).
3. Delete the old lockfile.
4. Run `bun install` from the workspace root after all packages are converted. **Do not** run `bun install` inside the child — that creates a nested lockfile.

## From npm (`package-lock.json`)

Common issues:

- **`npm`-specific fields.** `package-lock.json` may include `engines`, `cpu`, `os` constraints in some entries. Bun resolves these from `package.json`; nothing to do.
- **Peer-dep auto-installs.** Recent npm versions auto-install peer deps; Bun does too (with `--linker hoisted`, the default) but with slightly different semantics. Watch for peer warnings on first install.
- **Overrides.** If `package-lock.json` shows pinned transitive versions because of `package.json#overrides`, hoist those `overrides` to the workspace root.

Delete: `package-lock.json`, `npm-shrinkwrap.json` (if present).

## From pnpm (`pnpm-lock.yaml`, `pnpm-workspace.yaml`)

pnpm has the strictest dep isolation; Bun is more permissive by default. Two things to check:

- **`pnpm-workspace.yaml`** — if the child was itself a pnpm workspace, its `packages:` globs need to be translated into Bun workspace globs at the new root. Or you may decide to flatten the inner workspace entirely.
- **`pnpm` `overrides` / `pnpm.peerDependencyRules`** — pnpm-specific. Translate `overrides` to Bun root `overrides`. `peerDependencyRules.ignoreMissing` has no direct Bun equivalent; missing peers will show as warnings, which is usually fine.

Consider setting Bun's `[install] linker = "isolated"` in `bunfig.toml` to keep pnpm-like strictness if the user relied on that isolation.

Delete: `pnpm-lock.yaml`, `pnpm-workspace.yaml` (if absorbed into root), `.npmrc` with pnpm-specific config.

## From yarn (`yarn.lock`)

- **Yarn Classic vs Berry.** Berry uses PnP by default — code that assumed PnP resolution may break under Bun's hoisted layout. Watch for "Cannot find module" errors that worked under Berry.
- **`resolutions`** — Yarn's equivalent of `overrides`. Translate to root `overrides`.

Delete: `yarn.lock`, `.yarnrc.yml`, `.pnp.cjs`, `.pnp.loader.mjs`, `.yarn/` (unless used for something else).

## Surfacing peer warnings

After the first root `bun install`, the output may include lines like:

```
warn: <pkg> has peer dependency <X> but none was installed
```

These warnings are diagnostic, not always fatal:

- If `<X>` is something the workspace *should* have (e.g. `react`), add it to the right package's `dependencies` and re-install.
- If `<X>` is an optional/legacy peer the package would have auto-installed under npm, it's safe to ignore.

Don't suppress them globally — they're useful signal.

## Native modules

Some deps (sharp, node-sass, @swc/core, sqlite3, canvas) compile native binaries on install. After consolidating, run an end-to-end smoke test (`bun run typecheck` + the package's own tests) for any package that uses these to confirm the right arch was resolved. Bun is generally good at this but it's worth verifying.
