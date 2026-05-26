---
name: "wiki:query"
description: "Query the wiki for knowledge synthesis. Searches across all pages and synthesizes an answer with citations."
argument-hint: '<question>' [--client <slug>] [--promote]
allowed-tools: Skill(wiki-query), Agent, Bash, Read, Write, Edit, Glob, Grep
---

Invoke the `wiki-query` skill with the user's arguments:

```
$ARGUMENTS
```

Expected: `<question>` plus optional `--client <slug>` (scope to one client) and `--promote` (promote a substantive answer into a new wiki page).

The skill identifies relevant entity types, searches the wiki, reads sources, and synthesizes an answer with citations. See `skills/wiki-query/SKILL.md` for the search-and-synthesis pipeline and promotion rules.
