## Project Database (project-db) — the query layer over the wiki

This project has a queryable SQLite index of `{{WIKI_ROOT}}/` at `.claude/db/project.sqlite` (slug `{{SLUG}}`, mode `{{MODE}}`), rebuilt incrementally by a SessionStart hook. The **wiki remains the record**; the database is the **index**. Treat it the way a data team treats a read replica: query freely, never write.

### Rules

1. **Query the database for structured questions before grepping or reading pages.** Counts, filters, joins, "all X where Y", "what links to Z", "which meetings discussed W", "gaps without a decision" are SQL questions. Run `python3 .claude/db/db.py query "SELECT …"`, then open the page at `pages.path` for narrative context. Reading twenty pages to answer a question the database answers in one query is the failure mode this exists to prevent.
2. **Read `.claude/db/SCHEMA.md` before writing SQL.** Prefer the typed views (one per page type, frontmatter keys as real columns) over `pages` + `json_extract`. Column docs come from the wiki templates, so value vocabularies (`severity: critical|high|medium|low`) are in the schema, not guessed.
3. **Never write to the database.** It is derived. Change knowledge by editing wiki pages or running the wiki ingest commands, then `/db:sync` (the SessionStart hook also syncs). A fact that exists only in the database is a bug.
4. **Turn repeated queries into views.** Writing the same multi-table query twice means it belongs in `.claude/db/views.sql` with a `-- doc:` line; `/db:sync` applies it and SCHEMA.md advertises it. Views are the SQL form of skills. `python3 .claude/db/db.py audit --top` lists the candidates.
5. **Guardrails are the contract, not an obstacle.** Read-only connection (SQLite authorizer), one statement per call, {{ROW_LIMIT}}-row cap, {{TIMEOUT}} s timeout, CSV output with cells cut at {{MAX_CELL}} chars, every query logged to `.claude/db/audit.sqlite`. Narrow the query instead of raising the caps. A query error is information: fix the SQL and rerun.
6. **Full-text search is one call:** `python3 .claude/db/db.py search "budget AND approval"` (FTS5; `--raw` includes cited raw documents such as transcripts).

### Commands

| Situation | Command |
|---|---|
| Structured question about the project (counts, filters, joins, links) | `python3 .claude/db/db.py query "<one SELECT>"` |
| Find pages by words, phrases, prefixes | `python3 .claude/db/db.py search "<fts terms>" [--type gap] [--raw]` |
| What tables / views / columns exist | `.claude/db/SCHEMA.md` or `python3 .claude/db/db.py schema [object]` |
| Wiki changed (ingest, edit, lint --fix) | `/db:sync` (hook does this at session start) |
| A query worth keeping | add a view to `.claude/db/views.sql`, then `/db:sync` |
| Which queries agents actually run, which failed | `python3 .claude/db/db.py audit [--top\|--errors]` |
| Publish to Cloudflare D1 / redeploy the MCP Worker (modes d1, both) | `/db:publish` |
| Health check (counts match files, views compile, read-only enforced) | `python3 .claude/db/db.py verify` |
