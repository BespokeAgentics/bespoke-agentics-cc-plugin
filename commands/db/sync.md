---
name: "db:sync"
description: "Refresh the project database from its sources — incremental by content hash (only changed pages reload), regenerates typed views, re-applies views.sql, rebuilds full-text search, rewrites SCHEMA.md. Use --full to drop and rebuild; --verify to run the health checks after."
argument-hint: "[--full] [--verify] [--status]"
allowed-tools: Bash, Read
---

> **How this command loads its skill.** `project-db` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/project-db/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Project DB — Sync

Follow the `project-db` skill (loaded as described above) with `mode: sync` and forward:

```
$ARGUMENTS
```

Runs `python3 .claude/db/db.py sync [--full]`, then `verify` when `--verify` is given and `status`
when `--status` is given. Report the one-line sync summary (pages added / changed / removed, raw
docs, views), any curated view that failed to compile (with its error — fix `views.sql` and rerun),
and the counts.

Run this after wiki ingests, `/wiki:lint --fix`, `/ontology:apply`, bulk edits, or after editing
`.claude/db/views.sql` or `config.json`. The SessionStart hook runs the same incremental sync at every
session start. When project-ontology is installed, the sync also reloads the ontology tables and reports
strict violations (exit 3 with `"ontology": {"gate": "fail"}` in `config.json`).
See `skills/project-db/SKILL.md` § sync.
