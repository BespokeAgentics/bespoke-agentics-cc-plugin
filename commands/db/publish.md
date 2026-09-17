---
name: "db:publish"
description: "Publish the project database to Cloudflare D1 and deploy the read-only MCP Worker (modes d1 / both): sync, export a D1-safe import.sql, dry-run on local D1, then create/execute/deploy remotely with wrangler, smoke-test, and log. Confirms before the first create, deploy or secret write."
argument-hint: "[--dry-run] [--deploy] [--no-deploy]"
allowed-tools: Skill(project-db), AskUserQuestion, Bash, Read, Write, Edit
---

# Project DB — Publish

Invoke the `project-db` skill with `mode: publish` and forward:

```
$ARGUMENTS
```

Read `skills/project-db/references/d1-publish.md` first. The sequence: `db.py sync` →
`db.py export-d1` → scaffold `.claude/db/worker/` from `templates/d1/` if missing → **local D1 dry
run** (`wrangler d1 execute <name> --local --file=../d1/import.sql --yes`) → `wrangler whoami` →
`wrangler d1 create` once (store `database_id` in `wrangler.toml` and `config.json`) →
`--remote --file` → `wrangler deploy` (first time, or `--deploy`) → `secret put MCP_BEARER_TOKENS`
(first time) → smoke test `/health` and one `tools/call` → append a `wiki/_log.md` entry with counts
and the Worker URL.

- `--dry-run` stops after the local D1 import and reports.
- The project must be `mode: d1` or `both` (`/db:init --force --mode both` to switch).
- Cloudflare actions are outward-facing: ask before the first `d1 create`, `deploy`, or secret write;
  data re-publishes to an existing database are routine.

Report: rows published, database name, Worker URL, how to connect a client (`claude mcp add
--transport http … --header "Authorization: Bearer …"`).
