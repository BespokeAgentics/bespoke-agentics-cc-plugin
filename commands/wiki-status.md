---
name: "wiki:status"
description: "Display a dashboard of wiki health and recent activity. Shows page counts by type, recent operations, and overall health metrics."
argument-hint: '[--client <slug>]'
allowed-tools: Bash, Read, Glob, Grep
disable-model-invocation: true
---

> **How this command loads its skill.** `wiki-status` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/wiki-status/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

Follow the `wiki-status` skill (loaded as described above) with the user's arguments:

```
$ARGUMENTS
```

Optional: `--client <slug>` to scope the dashboard to a single client wiki. Without arguments, show the workspace-wide view.

See `skills/wiki-status/SKILL.md` for the dashboard sections, fallback rules, and per-client vs workspace-wide templates.
