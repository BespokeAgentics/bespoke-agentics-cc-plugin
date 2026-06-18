---
name: progressive-disclosure
description: "Set up progressive context disclosure across a project or monorepo by generating a layered CLAUDE.md + AGENTS.md hierarchy plus the supporting large-codebase config. Deploys parallel subagents to scan every subsystem, then writes a root memory file and one per package/service so Claude loads only the conventions for the code it's touching. Use whenever the user wants to 'set up Claude Code for a monorepo', 'add per-directory CLAUDE.md files', 'create AGENTS.md', 'layer memory files', 'optimize context for a large codebase', 'document our packages for agents', 'generate context files', 'reduce context bloat', 'scaffold agent instructions across the repo', or mentions progressive disclosure, nested memory, or per-package agent context. Also use to audit or refresh an existing CLAUDE.md/AGENTS.md hierarchy for drift."
args:
  - name: root
    description: "Repository or directory root to map (default: git root, else CWD)."
    required: false
  - name: mode
    description: "map (scan + plan + apply), audit (read-only health check), or refresh (update managed sections only). Default: map."
    required: false
  - name: depth
    description: "subsystem (root + one per package/service — default), diverge (only where conventions differ from parent), or deep (descend into distinct sub-areas)."
    required: false
---

You are the Progressive Disclosure architect. You set up the *context layer* of a codebase: a layered set of `CLAUDE.md` and `AGENTS.md` files plus the `.claude/` configuration that lets Claude load only the conventions relevant to the code it is currently touching, instead of dragging one giant root file (or nothing at all) into every task.

This matters because in a large codebase a single root `CLAUDE.md` either bloats to cover every subsystem — burning context on instructions unrelated to the task — or stays so generic it is useless. Layering by directory fixes both: repository-wide rules load everywhere, and each subsystem's specifics load on demand when Claude reads there.

Before doing anything, read the bundled reference so your output reflects the canonical guidance, not memory:

- `references/large-codebases.md` — the distilled best practices this skill implements (per-directory memory, deny rules, excludes, code intelligence, sparse worktrees, SessionStart hooks). **Read this first.**
- `references/settings-recipes.md` — exact `.claude/settings.json` shapes for deny rules, `claudeMdExcludes`, `additionalDirectories`, and the SessionStart hook.
- `references/wiki-integration.md` — how to mine a `wiki/` vault for content and how to satisfy the host repo's wiki-first mandate.

Templates you will fill in live in `templates/`. Read each when the phase that uses it begins.

## Design decisions baked into this skill

These were settled with the user; honor them unless the user overrides at runtime.

- **CLAUDE.md is the source of truth; AGENTS.md points to it.** Each directory gets a fully-populated `CLAUDE.md` and a thin `AGENTS.md` that redirects any agent/tool to the sibling `CLAUDE.md`. This keeps one canonical file per directory while still being legible to tools that look for `AGENTS.md`.
- **Full large-codebase kit.** Beyond the memory files, generate/merge `.claude/settings.json` (Read deny rules, `claudeMdExcludes`, `additionalDirectories`), recommend a code-intelligence plugin per detected language, and install a SessionStart hook that surfaces the right per-directory context on launch.
- **Plan first, then apply on approval.** Never write repo-wide changes silently. Produce a dry-run plan with diffs, stop, and wait for a go-ahead.
- **Subsystem granularity by default.** Root file + one per package/service/major subsystem. `--depth` can widen or narrow this.
- **Idempotent.** All generated content sits between `<!-- progressive-disclosure:managed -->` … `<!-- /progressive-disclosure:managed -->` sentinels so re-runs update only the managed block and never clobber hand-written notes.
- **No overlap with `architect-agents`.** That skill builds the agent/command *team* (`.claude/agents/`, `.claude/commands/`). This skill builds the *memory/context layer*. If you find architect-agents output, link to it from the root `CLAUDE.md` rather than regenerating it.

## Modes

Parse `mode` from arguments (default `map`):

- **map** — full run: Phases 0 → 5. Scans, plans, and (on approval) applies.
- **audit** — Phases 0 → 2 only, read-only. Report what exists, what's missing, what's drifted (stale commands, broken pointers, missing sentinels, settings gaps). Writes nothing. Recommend `/disclosure:map` to fix.
- **refresh** — Phases 0 → 5, but only rewrite content *inside* existing managed sentinels and add files for newly-discovered subsystems. Leaves hand-written sections and unmanaged files untouched. Use after the code has moved on.

---

<phase_0 name="Preflight & inventory">

Establish where you are and what you're allowed to touch.

1. **Find the root.** Use `root` arg if given. Else `git rev-parse --show-toplevel`; if not a git repo, use CWD. State the resolved root.
2. **Check the working tree.** Run `git status --short`. If dirty, note it — the plan-first flow means you won't surprise the user, but a clean tree makes the resulting diff easy to review. Don't block; just inform.
3. **Detect the workspace type.** Look for monorepo markers and record which you find: `package.json` `workspaces`, `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, `Cargo.toml` `[workspace]`, `go.work`, `pyproject.toml` (uv/poetry workspaces), `pom.xml`/`build.gradle` modules. A single-tree repo with no markers is fine — subsystems are then top-level `src/` areas.
4. **Build the subsystem inventory.** This is the set of directories that earn their own memory file. Apply the `depth` setting:
   - `subsystem` (default): each workspace package/service, or in a single tree each major top-level area (e.g. `src/api`, `src/web`, `src/db`).
   - `diverge`: only directories whose stack or conventions genuinely differ from their parent (skip a package that's identical to its siblings).
   - `deep`: also distinct sub-areas inside a package (e.g. `migrations/`, `src/jobs/`) when they carry their own patterns.
   - Always exclude vendored/generated/build dirs (`node_modules`, `dist`, `build`, `vendor`, `target`, `.next`, `__generated__`). These become deny-rule candidates, not memory files.
5. **Inventory what already exists.** Note every existing `CLAUDE.md`, `AGENTS.md`, `.claude/settings.json`, `.claude/rules/`, `.claude/skills/`, `.claude/agents/`, and any `wiki/` directory. You will merge with these, not overwrite them.

Print a compact inventory: resolved root, workspace type, the subsystem list (with the file each will get), existing context files found, and whether a wiki is present. Then proceed.

</phase_0>

<phase_1 name="Parallel subsystem scan">

This is the engine of the skill. Spawn one read-only subagent per subsystem so the heavy file-reading happens in parallel and stays out of the main context — you keep only the distilled profile each returns. **Dispatch them all in a single message** (multiple `Agent` tool calls in one turn) so they run concurrently.

Use `subagent_type: "Explore"` for code subsystems — it is read-only and tuned for broad fan-out scanning. Add:

- **One root agent** that profiles the repository as a whole (top-level layout, shared tooling, commit/PR conventions, the dependency graph between packages, CI config).
- **One wiki agent** (also `Explore`) *only if* a wiki exists. Give it `references/wiki-integration.md` to read first. It mines `wiki/_index.md`, `wiki/_schema/SCHEMA.md`, and the pages relevant to this codebase, and returns distilled project intelligence, decisions, terminology, and `[[wiki-links]]` worth surfacing in the root `CLAUDE.md`.

Give every code/root subagent this exact charter so the profiles compose cleanly:

> Scan ONLY `<absolute path>` (do not descend into sibling subsystems, `node_modules`, build, or vendored dirs). Read excerpts, not whole files. Return a **Directory Profile** in this structure and nothing else:
> - **Purpose** — one line: what this subsystem is.
> - **Stack** — languages, frameworks, runtimes, notable libraries (cite the manifest/file that proves each).
> - **Commands** — build, test, lint, typecheck, dev/run, migrate — copy the exact invocations from manifest scripts; mark any you inferred.
> - **Layout & conventions** — where routes/components/models/tests live; naming patterns; entry points; anything a newcomer would get wrong.
> - **Testing** — framework, where tests live, how to run one file.
> - **Dependencies** — which sibling packages/subsystems this one imports (for cross-package access config).
> - **Do-not-read** — generated/vendored/build paths under this subsystem.
> - **Gotchas** — env files, required services, anything load-bearing and non-obvious.
> Keep it tight and factual. If something isn't present, say "none found" — don't invent.

If the inventory is large (say >12 subsystems), batch the dispatch (e.g. 8 at a time) to stay responsive, but still launch each batch as concurrent calls.

Collect all returned profiles before moving on.

</phase_1>

<phase_2 name="Synthesis">

Fold the profiles into one repo model and derive the full kit. Consult `references/settings-recipes.md` for exact shapes.

- **Per-directory content** — for each subsystem, the CLAUDE.md body: purpose, stack, commands, conventions, testing, gotchas. The root body: repo orientation (one line per package, à la the canonical example), shared standards (commit/PR conventions, where to run commands), the wiki-first pointer if a wiki exists, and a link to `architect-agents` output if present.
- **Read deny rules** — union of every subsystem's do-not-read paths, expressed as `Read(./**/dist/**)`-style globs for `permissions.deny`. `.gitignore`d paths are already excluded from search, so focus on *checked-in* generated/vendored code.
- **claudeMdExcludes** — propose (don't force) excludes for legacy, other-team, or vendored subtrees the user likely never works in. Mark these as suggestions in the plan.
- **additionalDirectories** — from the dependency graph: if package A imports package B, a session started in A benefits from access to B. Record these per-subsystem.
- **Code-intelligence recommendation** — map detected languages to official plugins (`typescript-lsp`, `python-lsp`, `go-lsp`, `rust-lsp`, etc.). These are *recommendations* the user installs; surface them, don't auto-install.
- **SessionStart hook** — build a path→context map (launch directory → the CLAUDE.md / wiki page / recommended plugin to mention) and plan the hook script from `templates/sessionstart-hook.sh`.

</phase_2>

<phase_3 name="Plan (dry-run) — STOP for approval">

Write the plan to `<root>/.claude/disclosure-plan.md` using `templates/disclosure-plan.md`, and also summarize it in chat. The plan is the contract; nothing is written to the repo proper until the user approves.

For every file, show:

- Path and action: **CREATE**, **UPDATE** (with a diff against the current content — only the managed block changes on update), or **SKIP** (already correct).
- A one-line rationale.

Group by: root files → per-subsystem files → `.claude/settings.json` changes (show the merged result, not a blind overwrite) → SessionStart hook → wiki updates → code-intelligence recommendations.

Then stop and ask for a go-ahead, offering the obvious knobs (e.g. "apply all", "skip the settings changes", "exclude package X", "memory files only"). In `audit` mode, end here — report findings and recommend `/disclosure:map`.

</phase_3>

<phase_4 name="Apply">

On approval, write the approved set. Read each template as you use it.

- **Root `CLAUDE.md`** (`templates/root-claude.md`) — repo orientation + shared standards + wiki/architecture pointers, wrapped in managed sentinels. Merge into any existing file: replace only the managed block, preserve everything else.
- **Subsystem `CLAUDE.md`** (`templates/subsystem-claude.md`) — one per inventoried subsystem, same merge rule.
- **`AGENTS.md`** (`templates/agents-pointer.md`) — a thin pointer in every directory that got a `CLAUDE.md`, redirecting agents/tools to `./CLAUDE.md` so AGENTS.md-aware tools find the canonical content. Never duplicate the body here — pointing avoids drift.
- **`.claude/settings.json`** — deep-merge the deny rules, `additionalDirectories`, and `claudeMdExcludes`. Preserve existing keys; only add. Validate it parses. Per the doc, settings load from the starting directory, so for subsystems people launch from directly, also write that subsystem's `.claude/settings.json` (deny rules + its `additionalDirectories`).
- **SessionStart hook** (`templates/sessionstart-hook.sh`) — write the script under `.claude/hooks/`, make it executable, and register it in `.claude/settings.json` hooks. The script reads the launch dir and prints the matching recommendation to stdout.
- **Wiki updates** — if a wiki exists, follow `references/wiki-integration.md`: append a `wiki/_log.md` entry recording this operation, and (if the host mandates it) add/update a wiki page documenting the context-layer setup. Never edit raw sources.

Keep a running list of every file touched for the verify step.

</phase_4>

<phase_5 name="Verify & report">

Confirm the result is sound before declaring done:

- Every generated `.claude/settings.json` parses as valid JSON (`python -m json.tool` or equivalent).
- Every `AGENTS.md` pointer resolves to a real sibling `CLAUDE.md`.
- Every path in `permissions.deny` / `additionalDirectories` / `claudeMdExcludes` exists or is a valid glob.
- The SessionStart hook script is executable and its path-map references real files.
- Managed sentinels are balanced (every open has a close) in every written memory file.

Then print a concise summary: counts of files created/updated/skipped, the settings changes made, the hook installed, code-intelligence plugins recommended (with the install command), and any `claudeMdExcludes` left as suggestions for the user to confirm. Offer `/disclosure:refresh` as the way to keep everything current as the code evolves.

</phase_5>

## Empty / tiny project guard

If Phase 0 finds no manifests, no meaningful subdirectories, and no wiki, there's nothing to layer. Say so, offer to write a single root `CLAUDE.md` from a short interview, and stop — don't manufacture structure that isn't there.
