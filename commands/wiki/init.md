---
name: "wiki:init"
description: "Initialize a Karpathy-style LLM wiki vault — scans the repo, interviews the user, and creates an Obsidian vault tailored to the project."
argument-hint: "[--wiki-dir <path>]"
allowed-tools: Skill(wiki-init), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

Invoke the `wiki-init` skill with the user's arguments:

```
$ARGUMENTS
```

The skill parses `[--wiki-dir <path>]` (default `./wiki`), scans the repo for context, runs the project-discovery interview, and writes the full Obsidian-compatible vault structure (schema, templates, indexes, project subtrees).

See `skills/wiki-init/SKILL.md` for the interview phases, vault layout, and entity templates.
