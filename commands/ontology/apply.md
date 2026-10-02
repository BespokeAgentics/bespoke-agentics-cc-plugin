---
name: "ontology:apply"
description: "Rewrite the mechanical ontology violations to canonical form — aliases and spelling variants to the canonical value, deprecated values to their replacement, title/label/folder links to the canonical [[link]] keeping the visible text. Frontmatter tokens and link text only; every other byte preserved. Always dry-run first and confirm."
argument-hint: "[--dry-run] [<path>...]"
allowed-tools: AskUserQuestion, Bash, Read
disable-model-invocation: true
---

> **How this command loads its skill.** `project-ontology` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/project-ontology/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Project Ontology — Apply

Follow the `project-ontology` skill (loaded as described above) with `mode: apply` and forward:

```
$ARGUMENTS
```

Runs `python3 .claude/ontology/ontology.py apply --dry-run` first and shows the summary (rewrites per
rule, files touched, a sample of lines). Only after you confirm does it run `apply`, which logs to
`wiki/_log.md` and reports the violations that remain — unknown values, ambiguous or broken links, and
relation-range problems are judgment calls it never touches. When project-db is installed, finish with
`/db:sync`.
