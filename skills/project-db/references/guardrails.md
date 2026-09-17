# Guardrails — what each one prevents, where it lives, what to do when it fires

"Give the agent SQL" sounds risky because people imagine an unguarded write connection. Data teams
solved this years ago for humans; the same plumbing works for agents. Each guardrail below names the
failure it exists for, so nobody removes it to "make a query work".

## Read-only, structurally

- **Mechanism**: the CLI and local MCP open `file:…?mode=ro` and install a SQLite **authorizer** that
  returns DENY for every action except `SQLITE_SELECT`, `SQLITE_READ`, `SQLITE_FUNCTION`,
  `SQLITE_RECURSIVE` and a fixed set of read-only pragmas (`data_version` for FTS5, `table_info`…).
- **Prevents**: any write, DDL, `ATTACH` of another file, `PRAGMA writable_schema`, temp tables —
  regardless of how the SQL is phrased or what the validator missed.
- **When it fires**: `authorization denied` / `attempt to write a readonly database`. The answer is
  never "open it read-write": edit the source page and `/db:sync`.
- **D1**: there is no read-only role. The Worker's validator plus the bearer token *are* the role.
  Data changes arrive only through `/db:publish`.

## Validator (belt to the authorizer's braces)

- **Mechanism**: `validate_sql` — exactly one statement (`;` outside strings splits), must start with
  `SELECT`, `WITH`, or `EXPLAIN`; a forbidden-keyword scan (`insert|update|delete|drop|alter|create|
  replace|attach|detach|pragma|vacuum|reindex|begin|commit|rollback|savepoint|release`) on the text
  with strings and comments stripped. The Worker implements the same in TypeScript.
- **Prevents**: multi-statement smuggling (`SELECT 1; DROP …`), CTE-disguised writes
  (`WITH t AS (…) INSERT …`), and gives a *readable* error before SQLite's terse one.
- **When it fires**: rewrite as one SELECT. `REPLACE(...)` the function inside a `WITH … SELECT` is
  tolerated; `REPLACE INTO` is not.

## Statement timeout

- **Mechanism**: `set_progress_handler` with a deadline (default 5 s, `--timeout`); D1 enforces 30 s.
- **Prevents**: an unbounded recursive CTE or a cross join over `sections × links` eating the session.
- **When it fires**: `statement timeout after Ns`. Add a WHERE, join through an indexed column
  (`pages.id`, `links.to_id`, `pages.slug`), or `--explain` to see the plan. Raising the timeout is
  the last resort, not the first.

## Row cap and cell truncation, CSV by default

- **Mechanism**: `fetchmany(limit+1)` (default 200, `--limit`) with a `TRUNCATED` note; cells cut at
  400 chars (`--max-cell`; `0` = full) with `…[+N chars]`; CSV output (JSON is ~3× the tokens of CSV
  for the same rows; `--format md` for human eyes).
- **Prevents**: a `SELECT body FROM pages` from filling the context window. The talk's point: result
  size, not query power, is what breaks agents.
- **When it fires**: narrow, aggregate, or page (`ORDER BY … LIMIT 50 OFFSET 50`). Fetch one `body`
  by slug when you actually need it, or one `sections` row.

## Audit log

- **Mechanism**: every query (CLI, local MCP) appends to `.claude/db/audit.sqlite → query_log`
  (ts, actor, session, sql, rows, ms, truncated, error). The Worker writes `_query_log` on D1. Auditing
  failures print a warning but never block a query.
- **Prevents**: opacity. It is also the improvement loop: `audit --top` (repeated queries → views),
  `audit --errors` (what the schema docs failed to make obvious).
- **Retention**: the file is gitignored; delete it to reset. Actor comes from `--actor`,
  `$PROJECT_DB_ACTOR`, or `$USER`.

## Scope and PII

- **Mechanism**: `config.json → exclude_keys` (frontmatter keys never loaded), collection `exclude`
  globs (paths never scanned), raw `max_bytes` and `extensions`. What is not loaded cannot be queried,
  which is the only PII control that survives a clever query.
- **Policy**: before loading raw documents (transcripts often contain names, emails, phone numbers),
  ask. Before publishing to D1 (a remote copy, readable by anyone with a token), ask again and say what
  is in it. Client-scoped views (`WHERE client = …`) are convenience, not access control; if two
  audiences must not see each other's data, they get two databases.
- **The honest status**: the talk called this "YOLO mode" in production; this skill makes exclusion
  explicit and asked-about, which is better than nothing and not a substitute for real access control.

## Tokens and the Worker

- `MCP_BEARER_TOKENS` (comma-separated) is a Worker secret; with it unset the Worker returns 503 for
  every `/mcp` request (fail closed). Rotate with `wrangler secret put`. `/health` is public and
  reports only counts and freshness.
- The Worker binds `ROW_LIMIT` / `MAX_CELL_CHARS` as vars; change them in `wrangler.toml`, not by
  editing the validator.

## What "safe" does not mean

The database is derived and rebuildable, so the worst case of a guardrail failure is a corrupted
index, not lost knowledge — the wiki (or the source files) is the record. Keep it that way: nothing
should ever write knowledge into the DB that is not also in a source file.
