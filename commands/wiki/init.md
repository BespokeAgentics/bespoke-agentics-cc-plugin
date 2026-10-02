---
name: "wiki:init"
description: "Initialize a Karpathy-style LLM wiki vault — scans the repo, interviews the user, and creates an Obsidian vault tailored to the project."
argument-hint: "[--wiki-dir <path>]"
allowed-tools: Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
disable-model-invocation: true
---

> **How this command loads its skill.** `wiki-init` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/wiki-init/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

Follow the `wiki-init` skill (loaded as described above) with the user's arguments:

```
$ARGUMENTS
```

The skill parses `[--wiki-dir <path>]` (default `./wiki`), scans the repo for context, runs the project-discovery interview, and writes the full Obsidian-compatible vault structure (schema, templates, indexes, project subtrees).

See `skills/wiki-init/SKILL.md` for the interview phases, vault layout, and entity templates.
