---
name: "wiki:ingest-meeting"
description: "Ingest a completed migration pipeline meeting output into the Karpathy-style LLM Wiki. Validates meeting analysis outputs and imports structured data."
argument-hint: '<company>' '<meeting-dir>' '<meeting-label>'
allowed-tools: Skill(wiki-ingest-meeting), Agent, Bash, Read, Write, Edit, Glob, Grep
---

Invoke the `wiki-ingest-meeting` skill with the user's arguments:

```
$ARGUMENTS
```

Expected positional args: `<company> <meeting-dir> <meeting-label>`. `<meeting-dir>` is the analysis-output directory from a migration-pipeline meeting; `<meeting-label>` is a short slug used to title the meeting page (e.g. `2026-05-26-discovery`).

The skill validates the meeting outputs, creates/updates feature/gap/question/decision pages, then links every entity back to a single meeting summary page. See `skills/wiki-ingest-meeting/SKILL.md` for validation rules and entity-routing logic.
