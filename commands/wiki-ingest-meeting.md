---
name: "wiki:ingest-meeting"
description: "Ingest a completed meeting-analysis pipeline output into the Karpathy-style LLM Wiki. Validates meeting analysis outputs and imports structured data."
argument-hint: "'<company>' '<meeting-dir>' '<meeting-label>'"
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
---

> **How this command loads its skill.** `wiki-ingest-meeting` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/wiki-ingest-meeting/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

Follow the `wiki-ingest-meeting` skill (loaded as described above) with the user's arguments:

```
$ARGUMENTS
```

Expected positional args: `<company> <meeting-dir> <meeting-label>`. `<meeting-dir>` is the analysis-output directory (markdown analysis files) from a meeting-analysis pipeline run; `<meeting-label>` is a short slug used to title the meeting page (e.g. `2026-05-26-discovery`).

The skill validates the meeting outputs, creates/updates feature/gap/question/decision pages, then links every entity back to a single meeting summary page. See `skills/wiki-ingest-meeting/SKILL.md` for validation rules and entity-routing logic.
