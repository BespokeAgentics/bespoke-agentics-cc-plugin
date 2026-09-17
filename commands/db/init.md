---
name: "db:init"
description: "Build a queryable SQLite (and optionally Cloudflare D1) database for this project — schema from the wiki when one exists, otherwise from an interview + codebase scan — and install the guarded query CLI, SessionStart sync hook, local MCP server and the DB-first mandate in CLAUDE.md. Idempotent."
argument-hint: "[--mode local|d1|both] [--slug <slug>] [--no-raw] [--exclude-key <key>]... [--markdown <type>=<dir>]... [--tabular <path>]... [--force]"
allowed-tools: Skill(project-db), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Project DB — Init

Invoke the `project-db` skill with `mode: init` and forward:

```
$ARGUMENTS
```

The skill detects the wiki (`wiki/_schema/SCHEMA.md` or `wiki/_index.md`) and the available tools
(`python3` required; `uv` for the local MCP server; `wrangler` for D1), interviews you with one
`AskUserQuestion` call (mode, raw sources, exclusions; plus sources/entities when there is no wiki),
then runs `scripts/db.py init` which writes `.claude/db/config.json`, vendors the engine, seeds
`views.sql`, installs `.claude/hooks/db-context.sh` + the `settings.json` hook entry, merges
`.mcp.json`, adds the managed block to `CLAUDE.md`, builds the database, writes
`.claude/db/SCHEMA.md`, verifies, and logs to `wiki/_log.md`.

- `--mode local` (default) keeps everything in `.claude/db/project.sqlite`; `both` adds D1 + a
  read-only MCP Worker via `/db:publish`; `d1` makes queries run remotely.
- `--markdown adr=docs/adr` / `--tabular data/customers.csv` add collections (mainly for projects
  without a wiki). `--exclude-key attendees` keeps a frontmatter key out of the database.

Finish with the counts (pages by type, raw docs, views), what was installed, and three example queries
from this schema. See `skills/project-db/SKILL.md`.
