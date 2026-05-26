---
name: "wiki:lint"
description: "Lint and validate the wiki. Checks for broken links, orphaned pages, contradictions, and data quality. Optionally auto-fix issues."
argument-hint: '[--scope full|client:<slug>|recent] [--fix]'
allowed-tools: Skill(wiki-lint), Agent, Bash, Read, Write, Edit, Glob, Grep
---

Invoke the `wiki-lint` skill with the user's arguments:

```
$ARGUMENTS
```

The skill parses `[--scope full|client:<slug>|recent] [--fix]`. If no arguments are given, default to `--scope full` (no auto-fix). After the skill runs, print the health-score summary it produced and the path of the saved lint report.

See `skills/wiki-lint/SKILL.md` for the full lint pipeline (link validation, orphan detection, contradiction check, metadata validation, duplicates, coverage, entity resolution, dates) and report schema.
