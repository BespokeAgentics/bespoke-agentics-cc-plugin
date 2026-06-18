# Large-codebase context: distilled best practices

Self-contained summary of the canonical guidance (Claude Code docs, *Set up Claude Code in a monorepo or large codebase*) that this skill implements. Read this before generating anything so output reflects the guidance rather than memory.

## The core problem

Claude Code loads every `CLAUDE.md` from the working directory up through every parent at launch, then loads each subdirectory's `CLAUDE.md` on demand when it first reads a file there. In a small project a single root file is fine. As a codebase grows, that one file either swells to cover every subsystem — spending context on instructions irrelevant to the current task and degrading performance — or stays too generic to help. The fix is to **layer instructions by directory** so repository-wide rules load everywhere and subsystem specifics load only when relevant.

## The settings, and what each accomplishes

Each is independent and they layer rather than replace each other. This skill produces the ones marked ✅.

| Goal | Mechanism | This skill |
| --- | --- | --- |
| Load only the conventions for the code you touch | Per-directory `CLAUDE.md` files | ✅ generates |
| Exclude `CLAUDE.md` for packages you never work in | `claudeMdExcludes` setting | ✅ proposes |
| Block reads of generated/vendored checked-in code | `Read` deny rules in `permissions.deny` | ✅ generates |
| Jump to a symbol instead of scanning files | Code-intelligence plugin (language server) | ✅ recommends |
| Check out only the dirs a task needs in a worktree | `worktree.sparsePaths` | ➖ documents (opt-in) |
| Read/edit a sibling package from one session | `additionalDirectories` / `--add-dir` | ✅ generates |
| Area-specific procedures that load only when relevant | Per-directory skills | ➖ defers to `architect-agents` |
| Recommend the right plugin at session start | `SessionStart` hook | ✅ installs |

## Layering CLAUDE.md by directory

The recommended split is two levels:

- **Root `CLAUDE.md`** — rules that apply everywhere: coding standards, commit/PR conventions, repository layout, where to run commands. Orient Claude to the structure, e.g.:

  ```
  This is a monorepo with three packages under packages/:
  - packages/api: Node.js REST API (Express, TypeScript, PostgreSQL)
  - packages/web: React frontend (Vite, TypeScript, Tailwind)
  - packages/shared: shared TypeScript utilities used by both
  Run commands from the package directory, not the monorepo root.
  ```

- **Per-subdirectory `CLAUDE.md`** — conventions specific to that area's stack. One per package in a monorepo; one per subsystem (`src/db/`, `src/api/`) in a single tree. Include the local commands and the patterns a newcomer would otherwise get wrong, e.g.:

  ```
  This package is the REST API server.
  - Run tests: npm test (Vitest)   - Dev server: npm run dev (port 3001)
  - Migrations: npm run migrate     - Env: copy .env.example to .env
  API routes are in src/routes/ (each exports an Express router).
  DB queries use Knex in src/db/. Never write raw SQL in route handlers.
  ```

Starting Claude from `packages/api/` then loads both that file and the root — with nothing from `packages/web/` in context.

**Where to start Claude** determines what loads: from the repo root, the root file loads and subdirectory files load on demand as Claude reads them; from a subdirectory, that file plus every ancestor loads at launch and file access is scoped to that subtree until granted more. Commit these files so teammates inherit them; each directory's owner maintains its own.

**Keeping them current:** review `CLAUDE.md` edits in PRs like any doc change; revisit after major model releases (a rule that worked around an old limitation can become pure overhead); and consider a `Stop` hook that proposes updates from the session transcript. This skill's `refresh` mode and managed sentinels exist to make recurring updates safe.

### Per-directory CLAUDE.md vs path-scoped rules

`.claude/rules/` files with a `paths:` glob are an alternative that keeps all conventions centralized at the root and loads them when Claude touches matching files. Use per-directory `CLAUDE.md` when directory owners maintain their own conventions versioned with the code; use path-scoped rules when you want one central location or the same rule applies to many scattered paths. This skill defaults to per-directory files (matching the "subsystem owns its context" model) but can note rules as an alternative.

## AGENTS.md

`AGENTS.md` is the cross-tool convention several AI coding tools read for project instructions. Claude Code's native memory file is `CLAUDE.md`. To serve both without maintaining two copies that drift, this skill makes **`CLAUDE.md` the source of truth and `AGENTS.md` a thin pointer** to it in each directory. (Claude's `@path` import works inside `CLAUDE.md`; the `AGENTS.md` pointer is plain prose so non-Claude tools still get directed to the canonical file.)

## Reducing what Claude reads

- **Deny rules.** Content searches already respect `.gitignore`, so `node_modules/`, `dist/`, `build/` stay out of results without config. For *checked-in* generated or vendored code (a committed SDK, generated clients), add `Read` deny rules so Claude won't open them even when a search lists them. Deny rules cover the built-in file tools and recognized Bash file commands (`cat`, `head`, `grep`, `find`); they don't filter a recursive search's own output and don't cover arbitrary subprocesses.
- **Code intelligence.** Finding a definition or callers by scanning costs many reads. A code-intelligence plugin connects Claude to a language server to jump to definitions, find references, and surface type errors directly. Official plugins exist for TypeScript, Python, Go, Rust, and others; they require the language's server binary on each machine. Pairs well with deny rules and excludes.

## Scoping worktrees and file access

- **`worktree.sparsePaths`** writes only the listed directories (plus root-level files) to disk when Claude creates a worktree — faster, smaller, and especially useful for subagent worktree isolation. List directories, not files; include `.claude` if you want root settings/skills inside the worktree. Pair with `symlinkDirectories: ["node_modules"]` to avoid duplicating large dirs.
- **`additionalDirectories`** (in `permissions`) grants read/write to dirs outside the working directory — e.g. a sibling package whose shared type you're updating. Relative paths resolve against the start directory. `--add-dir`/`/add-dir` does the same at runtime. Note the loading difference: the `additionalDirectories` *setting* grants file access only (no CLAUDE.md, rules, or skills load from it); `--add-dir` loads skills, and loads CLAUDE.md/rules only with `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`.

## Keeping skills discoverable

When skills spread across many directories, Claude chooses among them by name + description, and descriptions get shortened when there are many — which can strip the keywords Claude matches on. Keep descriptions short and lead with words a request would contain. Put broadly-shared skills (PR conventions, deploy checklist) in the root `.claude/skills/`; package cross-repo ones as a plugin (namespaced `plugin:skill`, so no collisions).

## When layering stops scaling

Per-directory files can drift and go unowned. At that point move reference content out of always-loaded `CLAUDE.md` into on-demand mechanisms: skills (load when relevant), plugins (versioned bundles a platform team owns), and MCP servers (expose an existing code-search/RAG index as a tool). A `SessionStart` hook can read the launch directory, look it up in a committed path→plugin map, and print the recommendation so a teammate in an unfamiliar area learns which plugin that area's owners maintain.

## Planning cross-package changes

Configuration controls what Claude sees; sequencing controls the result. For a change spanning several packages (update a shared type plus every call site): hand Claude the whole change in one session so decisions stay consistent, and save the plan to a markdown file before editing — a long session compacts its context along the way, and the saved plan survives where conversation history may not.

## Put-it-together layout

```
monorepo/
  CLAUDE.md
  .claude/settings.json            # deny rules (also for worktree sessions)
  packages/
    api/
      CLAUDE.md
      AGENTS.md                    # pointer → ./CLAUDE.md
      .claude/settings.json        # worktree, additionalDirectories, deny rules
      .claude/skills/...
    web/
      CLAUDE.md
      AGENTS.md
    shared/
      CLAUDE.md
      AGENTS.md
```

Project settings load only from the directory you start Claude in (they are *not* inherited from parents the way `CLAUDE.md` is), so each subsystem's `.claude/settings.json` must be self-contained rather than layered on the root file.
