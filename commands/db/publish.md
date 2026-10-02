---
name: "db:publish"
description: "Publish the project database to Cloudflare D1 and deploy the read-only MCP Worker (modes d1 / both): sync, export a D1-safe import.sql, dry-run on local D1, then create/execute/deploy remotely with wrangler, smoke-test, and log. Confirms before the first create, deploy or secret write."
argument-hint: "[--dry-run] [--deploy]"
allowed-tools: AskUserQuestion, Bash, Read, Write, Edit
disable-model-invocation: true
---

> **How this command loads its skill.** `project-db` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/project-db/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Project DB — Publish

Follow the `project-db` skill (loaded as described above) with `mode: publish` and forward:

```
$ARGUMENTS
```

Read `${CLAUDE_PLUGIN_ROOT}/skills/project-db/references/d1-publish.md` first. The sequence: `db.py sync` →
`db.py export-d1` → scaffold `.claude/db/worker/` from `templates/d1/` if missing → **local D1 dry
run** (`wrangler d1 execute <name> --local --file=../d1/import.sql --yes`) → `wrangler whoami` →
`wrangler d1 create` once (store `database_id` in `wrangler.toml`) →
`--remote --file` → `wrangler deploy` (first time, or `--deploy`) → `secret put MCP_BEARER_TOKENS`
(first time) → smoke test `/health` and one `tools/call` → `db.py publish-record --database <name>
--database-id <id> --url <worker-url>` (stamps `last_publish`, stores the D1 settings in `config.json`,
appends the `wiki/_log.md` entry).

- `--dry-run` stops after the local D1 import and reports.
- The project must be `mode: d1` or `both` (`/db:init --force --mode both` to switch).
- Cloudflare actions are outward-facing: ask before the first `d1 create`, `deploy`, or secret write;
  data re-publishes to an existing database are routine.

Report: rows published, database name, Worker URL, how to connect a client (`claude mcp add
--transport http … --header "Authorization: Bearer …"`).
