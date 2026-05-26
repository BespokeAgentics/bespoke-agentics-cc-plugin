---
name: "wiki:new-client"
description: "Bootstrap a new client workspace in the wiki. Creates directory structure, templates, and optionally imports initial platform or document context."
argument-hint: '<company>' '<platform-source>' [--target '<platform-target>'] [--context '<document-path>']
allowed-tools: Skill(wiki-scaffold-client), Agent, Bash, Read, Write, Edit, Glob, Grep
---

Invoke the `wiki-scaffold-client` skill with the user's arguments:

```
$ARGUMENTS
```

Expected positional args: `<company> <platform-source>`. Optional: `--target <platform-target>` to set a migration target, `--context <document-path>` to ingest an initial source document (RFP, kickoff brief, etc.).

The skill creates the client folder tree, instantiates entity templates, runs an intake interview, and (if `--context` was given) ingests the initial document so the client wiki starts with real content. See `skills/wiki-scaffold-client/SKILL.md` for workspace layout and entity templates.
