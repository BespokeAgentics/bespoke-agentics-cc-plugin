---
name: "disclosure:map"
description: "Scan a project or monorepo with parallel subagents and set up its progressive-disclosure context layer: a layered CLAUDE.md + AGENTS.md hierarchy (root + one per package/subsystem) plus the supporting .claude/ config (Read deny rules, additionalDirectories, claudeMdExcludes, a SessionStart hook, and code-intelligence recommendations). Plans first with diffs, then applies on approval. Reviews any wiki for context."
argument-hint: "[<root>] [--depth subsystem|diverge|deep] [--no-wiki] [--scope <path>]"
allowed-tools: Skill(progressive-disclosure), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Progressive Disclosure — Map

Set up the full context layer for a codebase so Claude loads only the conventions relevant
to the code it's touching. Deploys parallel read-only subagents to profile every subsystem,
synthesizes the findings, presents a **dry-run plan with diffs**, and writes nothing until
you approve.

## Arguments

Parse from `$ARGUMENTS`:

```
[<root>] [--depth subsystem|diverge|deep] [--no-wiki] [--scope <path>]
```

- `<root>` (optional) — repo/dir to map; defaults to git root, else CWD.
- `--depth` (optional, default `subsystem`) — how aggressively to place per-directory files.
  `subsystem` = root + one per package/service; `diverge` = only where conventions differ
  from the parent; `deep` = also distinct sub-areas inside a package.
- `--no-wiki` — skip wiki discovery and mining.
- `--scope <path>` — limit the scan to one subtree.

## Process

Invoke the `progressive-disclosure` skill with `mode: map` and forward `$ARGUMENTS`. The skill:

1. **Preflight & inventory** — resolve root, detect workspace type (npm/pnpm/yarn/turbo/nx/lerna/Cargo/go.work…), build the subsystem list, and note existing CLAUDE.md/AGENTS.md/settings/wiki.
2. **Parallel scan** — one `Explore` subagent per subsystem (plus a root agent and, if present, a wiki agent), dispatched concurrently, each returning a structured Directory Profile.
3. **Synthesize** — per-directory content, deny rules, `additionalDirectories` (from the dependency graph), `claudeMdExcludes` suggestions, code-intelligence recs, and the SessionStart path→context map.
4. **Plan** — write `.claude/disclosure-plan.md` and summarize in chat; **stop for approval**.
5. **Apply** — on approval, write the layered CLAUDE.md files, the thin AGENTS.md pointers, merged `.claude/settings.json`, and the SessionStart hook; log to the wiki if one exists.
6. **Verify** — JSON parses, pointers resolve, sentinels balanced; report counts + next steps.

See `skills/progressive-disclosure/SKILL.md` for the full phase detail and the design decisions (CLAUDE.md is source-of-truth, AGENTS.md points to it; idempotent managed sentinels; no overlap with `architect-agents`).

## Examples

```bash
/disclosure:map                                  # map the current repo at subsystem depth
/disclosure:map /Users/me/Projects/acme-monorepo # map a specific monorepo
/disclosure:map --depth diverge --no-wiki        # minimal files, skip the wiki
/disclosure:map --scope packages/api             # just one subtree
```

## Safety

- Nothing is written to the repo proper until you approve the plan.
- Existing hand-written content is preserved — only the `progressive-disclosure:managed` block is (re)written.
- A dirty working tree is reported, not blocked; the resulting git diff makes review easy.
