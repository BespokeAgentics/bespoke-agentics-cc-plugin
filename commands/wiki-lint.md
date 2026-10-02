---
name: "wiki:lint"
description: "Lint and validate the wiki. Checks for broken links, orphaned pages, contradictions, stale pages, missing cross-references, frontmatter errors, decision drift, and ontology violations (when project-ontology is installed). Optionally auto-fix issues."
argument-hint: '[--scope full|client:<slug>|recent] [--fix]'
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
disable-model-invocation: true
---

> **How this command loads its skill.** `wiki-lint` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/wiki-lint/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

Follow the `wiki-lint` skill (loaded as described above) with the user's arguments:

```
$ARGUMENTS
```

The skill parses `[--scope full|client:<slug>|recent] [--fix]`. `--fix` means `fix=true, report-only=false` — the user asked for fixes. If no arguments are given, run `--scope full` report-only (no auto-fix). After the skill runs, print the health-score summary it produced and the path of the saved lint report.

See `skills/wiki-lint/SKILL.md` for the full lint pipeline — eight checks: broken links, orphans, contradictions, stale pages, missing cross-references, frontmatter validation (against the vault's own vocabulary), decision drift, and the ontology dimension when project-ontology is installed — and the report schema.
