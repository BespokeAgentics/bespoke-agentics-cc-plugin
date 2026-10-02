---
name: "wiki:query"
description: "Query the wiki for knowledge synthesis. Searches across all pages and synthesizes an answer with citations."
argument-hint: '<question>' [--client <slug>] [--promote]
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
---

> **How this command loads its skill.** `wiki-query` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

Follow the `wiki-query` skill (loaded as described above) with the user's arguments:

```
$ARGUMENTS
```

Expected: `<question>` plus optional `--client <slug>` (scope to one client) and `--promote` (promote a substantive answer into a new wiki page).

The skill identifies relevant entity types, searches the wiki, reads sources, and synthesizes an answer with citations. See `skills/wiki-query/SKILL.md` for the search-and-synthesis pipeline and promotion rules.
