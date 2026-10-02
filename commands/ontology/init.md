---
name: "ontology:init"
description: "Generate this project's enforceable dot-notated ontology: mine the wiki (types, template and SCHEMA.md vocabularies, observed values, scope folders, tags, link fields), interview you on conflicts and outside values, write wiki/_schema/ontology.yaml + ONTOLOGY.md, and install the PreToolUse/PostToolUse/Bash guard, SessionStart banner and CLAUDE.md block. Every observed value ends classified; nothing is silently approved. Idempotent — a re-run only adds newly observed values as proposed."
argument-hint: "[--govern <dir>]... [--no-install] [--no-templates] [--force]"
allowed-tools: AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
disable-model-invocation: true
---

> **How this command loads its skill.** `project-ontology` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/project-ontology/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Project Ontology — Init

Follow the `project-ontology` skill (loaded as described above) with `mode: init` and forward:

```
$ARGUMENTS
```

The skill runs `scripts/ontology.py init --scan` (report at `.claude/ontology/init-report.json`), reads
`references/init-interview.md`, interviews you with `AskUserQuestion` (vocabulary conflicts, values
outside the declared vocabulary, scope spelling variants, tags, fields worth controlling, policy), records
the answers in `.claude/ontology/decisions.json`, then runs `init --write --decisions … --by <you>` —
which you confirm at the permission prompt, because declaring approved terms is a human gate.

It finishes by proving the hook blocks a deliberately bad value, reporting terms by status, classified
vs unknown (always 0), open violations (pre-existing ones never block), and offering `/ontology:apply
--dry-run` for the mechanical rewrites. Without a wiki pass `--govern docs/adr` (project-db's markdown
collections are used when present). See `skills/project-ontology/SKILL.md`.
