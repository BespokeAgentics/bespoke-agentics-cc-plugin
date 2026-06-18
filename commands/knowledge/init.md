---
name: "knowledge:init"
description: "Set up the self-improving knowledge loop: scaffold the facts/hypotheses/rules store (inside the wiki vault), write the before/after-task mandate into CLAUDE.md, and install a SessionStart hook that surfaces active rules. Idempotent."
argument-hint: "[--path <dir>] [--domains <a,b,c>]"
allowed-tools: Skill(knowledge-loop), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Knowledge Loop — Init

Stand up the knowledge loop end-to-end so the project learns from every task: review rules before
work, apply them by default, extract insights after, promote hypotheses to rules at 3+
confirmations, and demote rules that new data contradicts.

## Arguments

Parse from `$ARGUMENTS`:

```
[--path <dir>] [--domains <a,b,c>]
```

- `--path <dir>` — where the store lives. Default `wiki/knowledge/` when a `wiki/` vault exists,
  else `./knowledge/`.
- `--domains <a,b,c>` — seed these domains. If omitted, the skill proposes a set from the repo and
  wiki and confirms with you (seeding none is fine — domains grow on first `extract`).

## Process

Invoke the `knowledge-loop` skill with `mode: init` and forward `$ARGUMENTS`. The skill:

1. **Locates the store** and, if a wiki exists, reads `wiki/_schema/SCHEMA.md` + `wiki/_index.md`
   so the store conforms and links in.
2. **Confirms domains** via `AskUserQuestion` (don't hardcode — propose from repo/wiki context).
3. **Scaffolds** `INDEX.md`, `_schema.md`, and a `knowledge.md` / `hypotheses.md` / `rules.md`
   trio per domain from the skill's templates.
4. **Installs the mandate** — merges the before/after-task loop rules (and the 3+ promotion /
   contradiction-demotion rules + command table) into the project `CLAUDE.md` inside
   `<!-- knowledge-loop:managed -->` sentinels, preserving everything else. Where a Wiki-First
   Mandate exists, the loop is added as a subsection that reinforces it.
5. **Installs the SessionStart hook** — writes `.claude/hooks/knowledge-context.sh`, makes it
   executable, fills its store path, and registers it in `.claude/settings.json` (merged) so the
   active rules surface before the first prompt.
6. **Registers with the wiki** — logs to `wiki/_log.md` and links the store from `wiki/_index.md`.

See `skills/knowledge-loop/SKILL.md` for mode detail and `references/loop-algorithm.md` for the
promotion/demotion spec and counter-integrity rules.

## Examples

```bash
/knowledge:init                                  # store under wiki/knowledge/, propose domains
/knowledge:init --domains pricing,onboarding     # seed two domains up front
/knowledge:init --path ./knowledge               # no wiki vault — keep it at the repo root
```

## Safety

- Idempotent: only the `knowledge-loop:managed` block of `CLAUDE.md` and the hook are (re)written;
  hand-written content is preserved.
- Nothing in the wiki's raw sources is touched. The store is new content under `wiki/knowledge/`.
