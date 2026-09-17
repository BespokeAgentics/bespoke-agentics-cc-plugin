# Publish to Cloudflare D1 — runbook

Modes `d1` and `both` add a remote copy of the database on D1 and a Worker that serves it as read-only
MCP tools. D1 is SQLite, so the schema, views, FTS5 and JSON functions are identical; the only work is
moving rows within D1's limits and putting a token in front.

## Prerequisites

- `wrangler` ≥ 4 (`npx wrangler --version`; `npm i -g wrangler` or use `npx`).
- A Cloudflare account; `npx wrangler login` (interactive — ask the user to run `! npx wrangler login`)
  or `CLOUDFLARE_API_TOKEN` in the environment.
- Node ≥ 20 for the Worker build.

## Step 0 — sync and export

```bash
python3 .claude/db/db.py sync
python3 .claude/db/db.py export-d1            # → .claude/db/d1/import.sql ; prints stats
```

Check the printed stats: `max_statement_bytes` must be < 100 000 (the export batches at 90 KB and
chunks oversized cells, so this only fails if a single row's fixed columns exceed the limit);
`bytes` should be under 500 MB on the free tier (10 GB paid). If raw documents are the bulk, set
`max_bytes` lower on the raw collection or `--no-raw`.

## Step 1 — scaffold the Worker (first time only)

```bash
mkdir -p .claude/db/worker/src
# from the skill's templates/d1/: wrangler.toml.tmpl, package.json.tmpl, tsconfig.json,
# src/index.ts.tmpl, DEPLOY.md.tmpl → fill {{SLUG}}, {{PROJECT_NAME}}, {{DATABASE_NAME}}, {{DATABASE_ID}}
cd .claude/db/worker && npm install
```

`{{DATABASE_ID}}` can be left as a placeholder for the local dry run; the remote step fills it.

## Step 2 — dry run on local D1 (no account needed)

```bash
cd .claude/db/worker
npx wrangler d1 execute <DATABASE_NAME> --local --file=../d1/import.sql --yes
npx wrangler d1 execute <DATABASE_NAME> --local --command "SELECT type, COUNT(*) AS n FROM pages GROUP BY 1"
npx wrangler d1 execute <DATABASE_NAME> --local --command "SELECT slug FROM pages_fts JOIN pages p ON p.id = pages_fts.rowid WHERE pages_fts MATCH 'budget' LIMIT 3"
```

If this fails, fix it here; the remote run executes the same file in one transactional batch and
rolls back on the first error.

## Step 3 — remote (confirm with the user before the first create / deploy / secret)

```bash
npx wrangler whoami                                   # logged in?
npx wrangler d1 create <DATABASE_NAME>                # once; copy database_id into wrangler.toml AND config.json → d1.database_id
npx wrangler d1 execute <DATABASE_NAME> --remote --file=../d1/import.sql --yes
npx wrangler deploy                                   # first time, and after any src/index.ts change
npx wrangler secret put MCP_BEARER_TOKENS             # comma-separated; generate with: openssl rand -hex 24
```

Re-publishing data to an existing database is `export-d1` + `execute --remote --file` — the import
drops and recreates tables and views, keeps `_query_log`, and rebuilds FTS.

## Step 4 — smoke test

```bash
URL="https://project-db-<slug>.<subdomain>.workers.dev"
curl -fsS "$URL/health"
curl -fsS -X POST "$URL/mcp" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
curl -fsS -X POST "$URL/mcp" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"db_query","arguments":{"sql":"SELECT type, COUNT(*) AS n FROM pages GROUP BY 1"}}}'
```

Then record it:

```bash
python3 .claude/db/db.py publish-record --database <DATABASE_NAME> --database-id <id> --url "$URL"
```

This stamps `last_publish` in `sync_state` (shown by `status` and the session banner), stores the
D1 name/id/URL in `config.json`, and appends the `wiki/_log.md` (or `.claude/db/LOG.md`) entry with
row counts, database name and Worker URL.

## Connecting clients

- Claude Code: `claude mcp add --transport http project-db "$URL/mcp" --header "Authorization: Bearer $TOKEN"`
  (or the equivalent `.mcp.json` entry with `"type": "http"`).
- Any MCP client that speaks JSON-RPC over HTTPS. The Worker does not implement server-initiated
  streams; single request/response per call is all these tools need.
- `mode: d1` projects: the CLI's `query` runs `--remote` automatically through wrangler, so local
  sessions and remote clients see the same data.

## Limits that matter

| D1 limit | Value | project-db behaviour |
|---|---|---|
| SQL statement length | 100 KB | export batches ≤ 90 KB; cells > 60 KB appended via `UPDATE … ||` |
| `d1 execute --file` size | 5 GB | far above any wiki |
| Database size | 500 MB free / 10 GB paid | export warns > 500 MB |
| Query timeout | 30 s | Worker caps rows; narrow queries |
| Bound parameters | 100 | tools bind ≤ 2 |
| Columns per table | 100 | typed views are views; base tables have ≤ 16 columns |

## Troubleshooting

- `Authentication error` / `not logged in` → `! npx wrangler login`, or set `CLOUDFLARE_API_TOKEN`.
- `D1_ERROR: … statement too long` → a fixed column exceeded 100 KB; inspect with
  `SELECT path, length(body) FROM pages ORDER BY 2 DESC LIMIT 3`, then exclude or split.
- `no such table: pages_fts` on the Worker → FTS creation failed in the import; run the local dry run
  and read the first error.
- 503 from `/mcp` → `MCP_BEARER_TOKENS` not set. 401 → wrong token.
- Rows missing on D1 but present locally → the import batch rolled back; rerun the remote execute and
  read its output (it prints per-statement results).
