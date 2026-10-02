---
name: "wiki:new-client"
description: "Bootstrap a new client workspace in the wiki. Creates directory structure, templates, and optionally imports initial platform or document context."
argument-hint: '<company>' '<platform-source>' [--target '<platform-target>'] [--context '<document-path>']
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
disable-model-invocation: true
---

> **How this command loads its skill.** `wiki-scaffold-client` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/wiki-scaffold-client/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

Follow the `wiki-scaffold-client` skill (loaded as described above) with the user's arguments:

```
$ARGUMENTS
```

Expected positional args: `<company> <platform-source>`. Optional: `--target <platform-target>` to set a migration target (when omitted, the skill uses the vault's default target platform from `wiki/_schema/SCHEMA.md`, or asks), `--context <document-path>` to ingest an initial source document (RFP, kickoff brief, etc.).

The skill derives and validates the client slug, creates the client folder tree and initial entity pages, ingests the initial document if `--context` was given (so the client wiki starts with real content), writes the client README, and updates `wiki/_index.md` and appends a heading entry to `wiki/_log.md`. See `skills/wiki-scaffold-client/SKILL.md` for workspace layout and entity templates.
