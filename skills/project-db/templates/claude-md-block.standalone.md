## Project Database (project-db) — source of truth

This project keeps its knowledge in a queryable SQLite database at `.claude/db/project.sqlite` (slug `{{SLUG}}`, mode `{{MODE}}`), built from the source collections declared in `.claude/db/config.json` and rebuilt incrementally by a SessionStart hook. Every agent operating in this repository MUST use it as the primary knowledge layer.

### Rules

1. **Query the database before answering any project question.** Decisions, entities, status, data, history: if a table or view exists for it, do not rely on memory or general knowledge. Run `python3 .claude/db/db.py query "SELECT …"` first; open the source file at `pages.path` for the full text.
2. **Read `.claude/db/SCHEMA.md` before writing SQL.** Prefer the typed views (one per page type) and the curated views over raw tables.
3. **Update the sources after every content-producing operation, then sync.** New decisions, analyses, findings or data belong in the configured collections (markdown with frontmatter, or the tabular files) — not only in chat. Then `/db:sync`. Knowledge that exists only in a conversation is lost knowledge.
4. **Never modify raw sources; never write to the database by hand.** Sources are the record; the database is derived and rebuildable. Correct a source by editing it (or, for immutable inputs, by adding a page that records the correction and links back).
5. **Follow the schema.** A new kind of knowledge gets a collection in `.claude/db/config.json` (with a `default_type`) so it gets a typed view; a reusable query becomes a view in `.claude/db/views.sql` with a `-- doc:` line. `/db:sync` applies both and SCHEMA.md advertises them.
6. **Guardrails are the contract.** Read-only connection (SQLite authorizer), one statement per call, {{ROW_LIMIT}}-row cap, {{TIMEOUT}} s timeout, CSV output with cells cut at {{MAX_CELL}} chars, every query logged to `.claude/db/audit.sqlite`. Narrow the query instead of raising the caps.
7. **Log operations.** Builds and publishes are recorded in `.claude/db/LOG.md` by the engine; record schema changes there too (what collection or view changed, and why).

### Commands

| Situation | Command |
|---|---|
| Any structured question about the project | `python3 .claude/db/db.py query "<one SELECT>"` |
| Find pages by words, phrases, prefixes | `python3 .claude/db/db.py search "<fts terms>" [--type adr]` |
| What tables / views / columns exist | `.claude/db/SCHEMA.md` or `python3 .claude/db/db.py schema [object]` |
| Sources changed | `/db:sync` (hook does this at session start) |
| New source kind or reusable query | edit `.claude/db/config.json` / `.claude/db/views.sql`, then `/db:sync` |
| Which queries agents actually run, which failed | `python3 .claude/db/db.py audit [--top\|--errors]` |
| Publish to Cloudflare D1 / redeploy the MCP Worker (modes d1, both) | `/db:publish` |
| Health check | `python3 .claude/db/db.py verify` |
