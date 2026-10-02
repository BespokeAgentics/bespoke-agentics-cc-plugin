---
name: "wiki:ingest-document"
description: "Ingest an individual document (email, PDF, spec, Slack export) into the wiki. Extracts structured insights and creates source references."
argument-hint: '<company>' '<document-path>' '<type>' [--summary 'brief description']
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
---

> **How this command loads its skill.** `wiki-ingest-document` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/wiki-ingest-document/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

Follow the `wiki-ingest-document` skill (loaded as described above) with the user's arguments:

```
$ARGUMENTS
```

Expected positional args: `<company> <document-path> <type>` where `<type>` is one of `email | pdf | spec | slack | other`. Optional `--summary` provides a one-line description for the source page.

The skill extracts structured insights from the document and updates affected feature, gap, decision, and question pages, then registers the document as a source. See `skills/wiki-ingest-document/SKILL.md` for type-specific parsing rules and entity-routing logic.
