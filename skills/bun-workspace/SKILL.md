---
name: bun-workspace
description: "Convert sibling Node/Bun repos into a Bun workspace monorepo, audit one, or add a package. Triggers: 'turn into monorepo', 'set up Bun workspace', workspace globs, share deps across repos."
args:
  - name: mode
    description: "One of `analyze` | `convert` | `audit` | `add`. If omitted, default to `analyze` (read-only)."
    required: false
---

You are the Bun Workspace operator. You help users consolidate a directory of sibling projects into a single Bun workspace — first by understanding what's there (read-only), then by guiding the migration with reversible steps, then by maintaining it over time. Every destructive step is announced and confirmed; nothing surprises the user.

## When to Use This Skill

Trigger on any of:

- "I have a folder with N projects and want to share deps / set up a monorepo / Bun workspace"
- Mentions of `package.json#workspaces`, `bunfig.toml`, `workspace:*` protocol, `bun install --filter`
- "Convert this directory to a Bun monorepo" / "consolidate these repos" / "deduplicate lockfiles"
- "Is my Bun workspace set up correctly?" / "version drift" / "ungrouped workspace"
- A `/bun:*` slash command was invoked

If the user describes the *symptom* (running `npm install` in 4 folders, duplicate `node_modules`, version drift across repos) rather than the *mechanism*, still trigger. The most common phrasing is some variant of "I have a bunch of separate projects and I want them to live together cleanly."

This skill is **complementary to `git-submodules`**, not overlapping. Submodules manage the *git* layer (pinning child repos to specific commits); workspaces manage the *build/dependency* layer. A directory can be one, the other, both, or neither. When children have their own `.git` folders, this skill asks per-child what to do and routes to `/submodule:convert` if the user wants the git layer too.

## Mode Dispatch

| Mode      | Triggered by                                                              | Destructive? | Section                            |
| --------- | ------------------------------------------------------------------------- | ------------ | ---------------------------------- |
| `analyze` | `/bun:analyze`, "what would it take to monorepo this", default            | No           | [Mode: analyze](#mode-analyze)     |
| `convert` | `/bun:convert`, "actually do it", "migrate this to a Bun workspace"       | Yes          | [Mode: convert](#mode-convert)     |
| `audit`   | `/bun:audit`, "is this workspace healthy", "check for version drift"      | No           | [Mode: audit](#mode-audit)         |
| `add`     | `/bun:add`, "add a new package to the workspace"                          | Yes (small)  | [Mode: add](#mode-add)             |

Default to `analyze` when ambiguous. It's read-only and produces the input that `convert` consumes, so running it first is always the right move.

## Common Preflight (all modes)

1. **Resolve and print CWD.** Every mode prints `CWD: <path>` first so a wrong directory is obvious.
2. **Detect Bun.** Run `bun --version`. Require ≥ 1.1 for stable workspace support. If missing, print the install command (`curl -fsSL https://bun.sh/install | bash`) and stop.
3. **Detect git context.** Run `git -C <CWD> rev-parse --is-inside-work-tree 2>/dev/null` and `git -C <CWD> rev-parse --show-toplevel 2>/dev/null`. Record whether the parent dir itself is a git repo and where its root is.
4. **Refuse dirty trees on destructive modes.** `convert` and `add` abort if the parent repo has uncommitted changes, unless `--force` is passed. The convert flow rewrites many files; a dirty tree makes mistakes hard to unwind.
5. **Log to wiki if present.** If `wiki/_log.md` exists at the repo root, append one line after the operation completes: `| {YYYY-MM-DD} | bun-workspace-{mode} | {target} | {1-line summary} | |`. Skip silently if no wiki.

## Why This Skill Is Careful (read this once)

Workspace consolidation looks mechanical but has three classes of trap:

- **Lockfile churn.** A child that used npm or pnpm has a lockfile encoding peer-dep + optional-dep + native-module decisions Bun will re-resolve. The new tree is almost always *correct*, but it can subtly differ — surface that to the user instead of hiding it.
- **Name collisions.** Two children both named `app` will silently break workspace resolution. Scoping (`@org/cms`, `@org/portal`) prevents future collisions and is worth a one-time rename even when the current set is unique.
- **Hoisting vs isolation.** Bun's default is hoisted (flat) `node_modules`. That's fast and matches npm intuition, but it lets workspaces accidentally import each other's transitive deps. When peer-dep conflicts exist (two children pinning incompatible React majors), suggest `[install] linker = "isolated"` in `bunfig.toml`.

Bring these up *when relevant*, not preemptively. The point is: the user benefits from understanding the trade-offs, not from being lectured.

## References Pointer

Read these only when the situation calls for them:

| Question                                                                   | Read                                       |
| -------------------------------------------------------------------------- | ------------------------------------------ |
| Which deps should hoist? How do I resolve a version conflict?              | `references/dependency-hoisting.md`        |
| The user has npm/pnpm/yarn lockfiles — what migrates and what doesn't?     | `references/lockfile-migration.md`         |
| Should I use flat layout vs `apps/*` + `packages/*`? How do cross-pkg imports work? | `references/layout-patterns.md`   |
| I'm about to do the actual write phase — give me the ordered recipe.       | `references/conversion-recipe.md`          |

---

## Mode: analyze

**Goal:** Read the directory and produce a migration plan. Never write. This mode is safe to run on anything.

### Phase 1 — Scan

For each immediate subdirectory of CWD:

- Note whether it's a git repo: `<dir>/.git` exists (directory or file — the file form is a worktree pointer)
- Read `<dir>/package.json` if present. Extract: `name`, `version`, `scripts`, `dependencies`, `devDependencies`, `peerDependencies`, `overrides`/`resolutions`, `workspaces`
- Detect lockfile: `bun.lock`, `bun.lockb`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock` → infer the current package manager
- Detect framework via files: `next.config.*` → Next, `astro.config.*` → Astro, `vite.config.*` → Vite, `convex/` → Convex, `wrangler.toml` → Cloudflare Workers, `tsconfig.json` only → plain TS, `tsup.config.*`/`bun build` script → library

Also check the top level itself: does it have a `package.json` with `workspaces`? If yes, this is already (partially) a workspace — switch tone to "you want to extend an existing workspace" and offer `audit` as an alternative.

### Phase 2 — Classify

Bucket each subdirectory:

- **Package** — has `package.json`. Will become a workspace member.
- **Already a workspace** — has `package.json` *with its own `workspaces` field*. Flag prominently. Nested workspaces are not supported by Bun; the user must decide whether to flatten (move the inner workspaces up) or keep the inner workspace untouched as a single opaque package.
- **Non-package** — no `package.json` (e.g. `docs/`, `marketing/`, `plans/`, `scripts/`, `wiki/`). Will be excluded from workspace globs. List these so the user sees nothing is being lost.

### Phase 3 — Build the migration plan

Output a markdown report with these sections, in this order:

1. **Discovered packages** — table of `name | path | pkg manager | framework | nested workspaces | has .git`. Sort by path.
2. **Proposed workspace layout** — recommend one of:
   - **Flat-preserving** (default): keep current folder names, set `"workspaces": ["<each-existing-dir>"]`. Lowest disruption.
   - **Buckets** (`apps/*` + `packages/*`): only suggest if there's a clear apps-vs-libs split (≥ 2 packages each). Requires moves.
   - When in doubt, default to flat-preserving and mention buckets as a follow-up.
3. **Name normalization** — surface any unscoped packages (`housepower-cms`) and propose a scope derived from the parent dir name or asked from the user (`@housepower/cms`). Reasons: prevents future collisions, enables `workspace:*` cross-imports, and makes the root deps file readable.
4. **Dependency hoisting candidates** — two tables:
   - **Hoist** — deps appearing in ≥ 2 packages with compatible (matching major, ideally matching minor) versions. Show the version chosen for the root.
   - **Conflicts** — same dep, incompatible versions across packages. Needs human resolution. For each, list the package → version mapping and propose one of: pick highest, split via `overrides`, or keep local (don't hoist).
5. **Overrides / resolutions reconciliation** — if any child sets `overrides` or `resolutions`, those must move to the root. List them.
6. **Package manager unification** — list non-Bun lockfiles that will be deleted and regenerated during `convert`. Mention which packages might surface peer warnings on first `bun install` (read `references/lockfile-migration.md` if any non-Bun lockfile is present).
7. **Git posture per child repo** — for each child with its own `.git`, note three options without deciding:
   - *Submodule* — convert via `/submodule:convert` so the parent pins a SHA. Best when the child has independent CI / external collaborators.
   - *Absorb* — delete the child `.git` and let the parent repo own everything. Best when the children only ever moved together.
   - *Leave alone* — workspace-only, no parent git relationship. Acceptable but unusual; surface that the parent dir will not be a git repo.
8. **Risks & open questions** — anything ambiguous: nested-workspaces decision, name collisions, version conflicts, scripts that assume CWD, `.env` files that may need consolidation.

End with:

> Run `/bun:convert` when ready, or tell me what to change in the plan first.

Don't write anything. Don't run `bun install`. This mode is read-only.

---

## Mode: convert

**Goal:** Execute the migration the user just reviewed. Interview-driven, reversible step-by-step.

### Phase 1 — Re-run analyze and confirm

Run the analyze logic. If the user has already seen the report in this session, summarize the deltas (`Same as before, no changes detected`) rather than re-printing the full thing. Then require explicit confirmation: "Proceed with the migration?" (yes/no via AskUserQuestion).

Refuse to proceed if:
- The parent dir is a git repo with uncommitted changes (unless `--force`).
- Any child is a *nested workspace* and the user hasn't decided how to handle it.

### Phase 2 — Decisions (via AskUserQuestion)

Ask in this order. Batch where natural; don't ask 8 questions one at a time when 2 are obvious from context.

1. **Per-child git posture** — one question per child that has its own `.git`. Options: *Submodule*, *Absorb*, *Leave alone*. If the user picks Submodule for any child, stop and instruct: "Run `/submodule:convert` first to convert those children to submodules, then come back and re-run `/bun:convert`." This skill does not duplicate `git-submodules`.
2. **Workspace layout** — flat-preserving (default) vs `apps/*`+`packages/*`. Skip if only one option made sense in analyze.
3. **Root package name** — propose `<parent-dir-name>-workspace` and `@<parent-dir-name>/root`. User confirms or supplies.
4. **Name normalization** — for each unscoped child, confirm the proposed scoped name. Batch into one question if all share a scope.
5. **Lockfile / package-manager migration** — confirm: any non-Bun lockfile will be deleted and Bun will regenerate. Mention peer warnings may surface.
6. **Dependency hoisting** — present the hoist table from analyze; let the user check off any deps to *keep local* instead of hoisting. Resolve conflicts inline.

### Phase 3 — Write

Strictly ordered so partial failure stays recoverable. **Print each command before running it.**

1. **Safety net.** If parent is a git repo: `git checkout -b bun-workspace-migration`. Else suggest a tarball: `tar -czf ../<parent>-pre-bun-workspace.tgz .`. Either way, surface the rollback path explicitly.
2. **Git posture execution.** For each "absorb" child, announce `rm -rf <child>/.git` and run only after confirmation. For "leave alone", no action. ("Submodule" children were handled in Phase 1 by routing to `/submodule:convert`.)
3. **Layout moves** (only if the user picked buckets). Use `git mv` if parent is a git repo, plain `mv` otherwise. Print each move.
4. **Root scaffold.** Write these from templates, substituting the values from Phase 2:
   - `package.json` from `templates/root-package.json.tmpl` — `private: true`, chosen name, `workspaces` globs, hoisted `dependencies` / `devDependencies` / `overrides`, a `scripts` block with `install`, `test`, `typecheck`, `build` running across workspaces via `bun run --filter '*' <script>`
   - `bunfig.toml` from `templates/bunfig.toml.tmpl` — set `[install] linker = "isolated"` only if peer-dep conflicts were detected; otherwise omit
   - `tsconfig.base.json` from `templates/tsconfig.base.json.tmpl` — shared compiler options
   - `.gitignore` from `templates/gitignore.tmpl` — merge with any existing root `.gitignore`
5. **Per-package edits** — for each workspace package:
   - Rewrite `package.json#name` to the chosen scoped name
   - Remove deps that were hoisted to root
   - Delete its own lockfile (`bun.lock*`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`)
   - Update `tsconfig.json` to extend `../../tsconfig.base.json` (or `../tsconfig.base.json` for flat layout)
6. **Install.** Run `bun install` from the root. Capture stdout + stderr; surface peer warnings to the user.
7. **Smoke test.** For each workspace, run `bun run typecheck` and `bun run test` if those scripts exist. Use `bun run --filter '*' <script>` from the root. Surface failures *without rolling back* — the user decides whether to fix forward or revert. Failures here are almost always real issues that consolidation exposed (e.g., implicit dep on a transitively-installed package), not skill bugs.

For the exact ordered command list and per-step rollback instructions, read `references/conversion-recipe.md`.

### Phase 4 — Follow-up checklist

Print what's still on the user's plate:

- Review `.env` files in each package — consider hoisting shared env to root `.env` and gitignoring it
- Decide on a task runner (Turbo, Nx, or just `bun run --filter` — call out trade-offs only if asked)
- If cross-package imports are planned, create a shared `@<scope>/types` or `@<scope>/utils` package and reference via `workspace:*`
- Push the migration branch when satisfied (`git push -u origin bun-workspace-migration`)
- Open a PR if working on a team

---

## Mode: audit

**Goal:** Read-only health check on a directory that's already a Bun workspace. `--fix` applies the safe corrections only (rename inconsistencies, remove nested lockfiles).

### Checks

- **Workspace globs resolve.** Every glob in root `package.json#workspaces` matches at least one `package.json`. Stale globs (matching empty dirs) are flagged.
- **No duplicate package names.** `bun pm ls` exits clean. Duplicate names break resolution.
- **No nested lockfiles.** Workspace children must not have their own `bun.lock`, `package-lock.json`, etc. (Bun ignores them but they confuse humans and other tools.)
- **Overrides only at root.** Any child setting `overrides`/`resolutions` is a code smell — Bun only honors them at the root.
- **`private: true` at the root.** A workspace root that's accidentally publishable is a footgun.
- **Version drift.** Any dep listed at both root and child levels with mismatched versions, or any cross-child mismatch on a non-hoisted dep. Surface with the recommendation to either hoist or pick one version.
- **Shared tsconfig.** If `tsconfig.base.json` exists, each package's `tsconfig.json` should `extends` it. Flag any that don't.

### Report

Same table-driven format as `analyze` so the two modes feel consistent. End with a `--fix` invitation if any safe corrections were detected.

---

## Mode: add

**Goal:** Scaffold a new package into an existing Bun workspace. Lightweight — don't re-invent `bun init`.

### Inputs (via AskUserQuestion, or from args)

- `path` — where to place it (e.g. `packages/utils`, `apps/admin`)
- `name` — defaults to `@<rootscope>/<basename>` derived from the path
- `kind` — `library` or `app`. Controls default scripts (a library gets `build` + `typecheck`; an app gets `dev` + `build` + `start`).

### Actions

1. Verify the chosen path is covered by a workspace glob in root `package.json#workspaces`. If not, propose adding the glob.
2. Create `<path>/package.json` with the chosen name, `private: true` for apps, `version: "0.0.0"`, and minimal scripts.
3. Create `<path>/tsconfig.json` extending the workspace's `tsconfig.base.json` if one exists; otherwise a minimal standalone tsconfig.
4. Create `<path>/src/index.ts` with a one-line stub.
5. Run `bun install` from root so the new package is linked.

Call out the gaps that `bun init` alone doesn't cover: workspace-aware scoped name, tsconfig extension, workspace glob inclusion. That's the value-add over plain `bun init`.

---

## General Behavior Notes

- **Print every command before running it** in destructive flows. Users learn from these operations.
- **Never delete a `.git` folder without a confirmation step.** Even when the user already selected "absorb" in Phase 2, re-print the path and ask once more before `rm -rf`.
- **Use absolute paths in commands when CWD is ambiguous.** Workspace conversion involves many `cd`-equivalent operations; a relative path that resolves wrong is a bad failure mode.
- **When asked "should I use Bun workspaces or pnpm / npm workspaces / Turbo / Nx?"**, briefly note the trade-offs and let the user decide. Bun workspaces are great when the team is already on Bun and wants speed + simplicity; they're weaker when you need fine-grained dep isolation, complex task graphs, or remote caching (those favor Turbo/Nx atop any workspace).
- **Bun is the runtime *and* the package manager.** Don't pair a Bun workspace with `npm install` instructions; the lockfile is single-source-of-truth.
