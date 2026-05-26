---
name: "wiki:status"
description: "Display a dashboard of wiki health and recent activity. Shows page counts by type, recent operations, and overall health metrics."
argument-hint: '[--client <slug>]'
allowed-tools: Skill(wiki-status), Bash, Read, Glob, Grep
---

Invoke the `wiki-status` skill with the user's arguments:

```
$ARGUMENTS
```

Optional: `--client <slug>` to scope the dashboard to a single client wiki. Without arguments, show the workspace-wide view.

See `skills/wiki-status/SKILL.md` for the dashboard sections, fallback rules, and per-client vs workspace-wide templates.
