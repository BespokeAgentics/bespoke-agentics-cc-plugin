---
name: project-db
description: >
  Use when agents should answer project questions with SQL instead of reading pages one by one: "make the
  wiki queryable", "give agents SQL access", "project database", "sync the db", "publish to D1", "add a
  view", counting/filtering/joining questions ("which gaps / features / decisions…"), or /db:init,
  /db:query, /db:sync, /db:publish — even without the word "database". Builds SQLite from the wiki (pages,
  frontmatter fields, wikilinks, tags, sources, sections, raw documents, FTS5, one typed view per page
  type with template-mined column docs, curated views) or, with no wiki, from an interview and a codebase
  scan with a DB-first mandate. Ships a guarded read-only query CLI (authorizer, timeout, row cap, audit
  log), a SessionStart sync hook, a local MCP server, Cloudflare D1 publish with a read-only MCP Worker,
  and loads project-ontology's tables when installed.
args:
  - name: mode
    description: "init | query | sync | publish | status | verify | audit. Default: inferred (a question → query; nothing built yet → init)."
    required: false
  - name: args
    description: "Mode arguments: init [--mode local|d1|both] [--slug s] [--no-raw] [--exclude-key k]; query '<sql>' [--format csv|json|md] [--limit n] [--remote]; sync [--full]; publish [--deploy] [--dry-run]."
    required: false
---

You are the project-db engineer. The thesis you implement: give the agent **one tool, SQL, over
everything it needs to know**, and it will out-query a human — it reads whole schemas, chases foreign
keys, iterates on errors, and never gets bored. What makes that safe is not trust but plumbing: a
read-only role, a statement timeout, a row cap, compact output, and an audit log — the same guardrails
a data team puts in front of a read replica. What makes it *effective* is the schema: it is the prompt.
Typed views with documented value vocabularies turn "guess the frontmatter key" into "read the column".

The engine is `scripts/db.py` (stdlib Python, one file). `/db:init` vendors it into the project at
`.claude/db/db.py` so the hook, the CLI and the MCP server share one set of guardrails and the project
never depends on the plugin path at runtime. `SKILL_DIR` below means this skill's base directory (shown
when the skill loads).

## Design decisions baked in

Settled with the user; honor them unless overridden at runtime.

- **SQLite locally, Cloudflare D1 remotely, one schema.** D1 is SQLite (FTS5, views, JSON all work —
  verified on local D1), so the export is a plain SQL file. Per-project `mode`: `local` (file only),
  `both` (file for Claude Code sessions + D1/Worker for remote clients), `d1` (queries go to D1; the
  local file is only the build staging area).
- **Wiki pages and the raw sources they cite.** Pages are the index; `sources:` paths (transcripts,
  analyses, exports) are loaded into `raw_documents` with their own FTS so agents can query beyond the
  synthesis. Statistics cross into the DB; the wiki page stays the record.
- **Generic base tables + typed views**, not a table per type. Robust to frontmatter drift; the views
  are regenerated from *template keys ∪ observed keys* on every sync, and their column docs come from
  the `# a|b|c` comments in `_schema/templates/*.md`. Curated views live in `.claude/db/views.sql`
  (yours; never overwritten).
- **CLI + MCP.** The CLI (`db.py query`) is what Claude Code sessions use. The stdio MCP server
  (`.claude/db/mcp_server.py`, registered in `.mcp.json`, run by `uv`) serves other clients. The D1
  Worker is the remote MCP. All three enforce the same policy.
- **Hook-triggered incremental sync.** A SessionStart hook hashes every source file and reloads only
  what changed (a 60-page wiki syncs in ~30 ms, unchanged in ~10 ms), then prints a banner: counts,
  how to query, where the schema is. The banner is what makes "query the DB first" actually happen.
- **No wiki → still a database, still the source of truth.** Interview + codebase scan → collections
  in `config.json` → typed views → a DB-first mandate in CLAUDE.md that mirrors the wiki-first one.
- **Deterministic parsing.** Frontmatter is always read by the engine's subset parser, never PyYAML —
  otherwise `related: [[Page]]` parses as a nested list on machines that have PyYAML and the link
  vanishes. project-ontology uses the same parser (its tests pin the parity).
- **Ontology as a consumer, not a copy.** When `.claude/ontology/ontology.py` exists (the
  `project-ontology` skill), every sync imports it and loads `ontology_terms`, `ontology_aliases`,
  `ontology_fields`, `ontology_violations` and `pages.ontology_id` — the violations the write hook would
  report, from the same code. `config.json` `"ontology": {"gate": "warn"|"fail"|"off"}` decides whether
  `sync` exits 3 while strict violations stand.
- **Names:** skill `project-db`; commands `/db:init`, `/db:query`, `/db:sync`, `/db:publish`.

## What init installs

```
.claude/db/
├─ config.json        collections (what to load), query caps, mode, D1 settings   ← committed
├─ db.py              the vendored engine                                           ← committed
├─ views.sql          curated views — yours, seeded once from templates/            ← committed
├─ SCHEMA.md          generated schema-as-prompt: views, columns, docs, patterns    ← committed
├─ mcp_server.py      local stdio MCP over the same guardrails (uv run)             ← committed
├─ project.sqlite     the database (derived; rebuild with /db:sync --full)          ← gitignored
├─ audit.sqlite       query_log — every query, actor, rows, ms, error               ← gitignored
├─ d1/import.sql      D1-safe export (modes d1|both)                                ← gitignored
└─ worker/            Cloudflare Worker (MCP over D1) — modes d1|both              ← committed
.claude/hooks/db-context.sh     SessionStart: sync --quiet --banner
.claude/settings.json           hooks.SessionStart entry (merged, idempotent)
.mcp.json                       mcpServers.project-db (merged)
CLAUDE.md                       managed block between <!-- project-db:managed --> sentinels
wiki/_log.md (or .claude/db/LOG.md)   one entry per init / full build / publish
```

## Modes

### `init` — build the database and make it the default

1. **Detect, silently.** Wiki vault? (`wiki/_schema/SCHEMA.md` or `wiki/_index.md`; also `.claude/wiki`,
   `docs/wiki`). Existing `.claude/db/config.json`? `python3` (required), `uv` (local MCP), `wrangler`
   (D1). Count pages by `type:` and note the templates dir — you will quote these in the interview.
2. **Interview with `AskUserQuestion`** — only what detection cannot answer. Keep it to one call:
   - *Mode*: `local` (recommended when nothing needs remote access) | `both` | `d1`.
   - *Raw sources*: load the documents pages cite in `sources:`? (recommended yes; say how many resolve
     and their total size — `db.py` skips files over 5 MB and reports them).
   - *Exclusions*: frontmatter keys never to load (PII such as attendee emails), paths to skip.
   - *No wiki only*: which sources are the record, and what questions the DB must answer — see
     `references/schema-design.md` § "No wiki" for the exact questions and how answers map to config.
3. **Run the engine** from the skill directory so templates resolve:
   ```bash
   python3 "$SKILL_DIR/scripts/db.py" init --root . --mode <mode> --slug <slug> --skill-dir "$SKILL_DIR" \
     [--no-raw] [--exclude-key attendees] [--markdown adr=docs/adr] [--tabular data/customers.csv]
   ```
   It writes config, vendors the engine + MCP server, seeds `views.sql`, installs the hook, merges
   `.claude/settings.json`, `.mcp.json`, `.gitignore`, the CLAUDE.md block, builds everything, writes
   `SCHEMA.md`, and logs to `wiki/_log.md`. Re-running is safe (only managed blocks are touched;
   `--force` rewrites config).
4. **Verify**: `python3 .claude/db/db.py verify` — counts match files, every view compiles, FTS is
   populated, writes are denied, hook/mandate/MCP present. Fix anything red before reporting.
5. **Modes `d1`/`both`**: continue with `publish` (below) — init never touches Cloudflare.
6. **Report** in five lines: pages by type, raw documents, typed + curated views, what was installed,
   and the two commands the user will use next (`query`, `sync`). Then show three example queries
   drawn from *this* schema (a typed-view filter, a join through `links`, an FTS search).

If the wiki has a `related:` convention, `tags`, or client scoping, the generated views already expose
them; do not hand-write per-type tables. If a page type has fewer than two pages, its view still
exists — cheap, and the agent learns the vocabulary.

### `query` — answer a structured question

The loop an agent should run, and the one you run when asked a question:

1. **Read `.claude/db/SCHEMA.md`** (or `db.py schema <view>` for one object). Choose the typed or
   curated view that matches the question; fall back to `pages` + `json_extract` or `page_fields`
   only for keys no view has.
2. **Write ONE statement** and run it: `python3 .claude/db/db.py query "SELECT …"` (`--format md`
   when the user will read it, `json` when code will). Keep `body` out of wide selects; fetch one
   page's body or one `sections` row by slug once you know which.
3. **Errors are the correction loop.** "no such column" → check the view's columns; "TRUNCATED" →
   add WHERE/ORDER BY/LIMIT rather than `--limit 0`; "timeout" → narrow the join. Do not disable a
   guardrail to get an answer; the caps exist because a 5,000-row CSV in context is worse than no
   answer.
4. **Open the record.** The DB answers *which*; the wiki page at `pages.path` answers *why*. Cite
   pages by slug/path in the final answer, as the wiki-first mandate expects.
5. **Promote repeated queries to views.** The third time a multi-table query appears (yours or in
   `db.py audit --top`), add it to `.claude/db/views.sql` with a `-- doc:` line inside the statement
   and run `/db:sync`. That view is now a skill every future session has for free.

`--remote` runs the same validated statement on D1 through wrangler (mode `d1` does this by default).
`search "<fts terms>" [--type gap] [--raw]` is the shortcut for "which pages mention…"; with an ontology
it also matches the other spellings of a term (`Acme Corp` finds pages that wrote `acme-corp`).

Vocabulary questions are queries too, once project-ontology is installed: legal values
`SELECT value, status FROM ontology_terms WHERE parent = 'gap.severity' ORDER BY rowid`; what is broken
`SELECT rule, policy, path, field, value, suggestion FROM ontology_violations`; a client's subtree
`SELECT slug FROM pages WHERE ontology_id LIKE 'client.acme.%'`. The database reports violations; it
never fixes them — change terms with `/ontology:propose`, values in the pages.

### `sync` — keep it fresh

`python3 .claude/db/db.py sync` (incremental; `--full` drops and rebuilds; `--quiet` for scripts). With
an ontology, sync prints a warning while strict violations stand, or exits 3 when
`config.json` sets `"ontology": {"gate": "fail"}` (the SessionStart banner sync never fails).
Every wiki ingest, lint `--fix`, or bulk edit should end with a sync; the SessionStart hook covers the
gap between sessions. `sync` also re-applies `views.sql` and regenerates typed views, so a schema
change is just "edit, sync". Never edit `SCHEMA.md` — it is regenerated; put documentation in
`views.sql` (`-- doc:`) or `config.json` (`column_docs` for tabular tables).

### `publish` — D1 + MCP Worker (modes `d1`, `both`)

Read `references/d1-publish.md` before the first publish. Summary:

1. `sync`, then `python3 .claude/db/db.py export-d1` → `.claude/db/d1/import.sql` (no BEGIN/COMMIT;
   statements < 90 KB; oversized cells appended in chunks; FTS rebuilt on the far side).
2. Scaffold `.claude/db/worker/` from `templates/d1/` on first run (fill `{{SLUG}}`,
   `{{PROJECT_NAME}}`, `{{DATABASE_NAME}}`, `{{DATABASE_ID}}`); `npm install`.
3. **Dry run on local D1 first** — no account needed:
   `npx wrangler d1 execute <name> --local --file=../d1/import.sql --yes` then a `SELECT COUNT(*)`.
4. Remote: `wrangler whoami` (if not logged in, ask the user to run `! npx wrangler login`),
   `wrangler d1 create <name>` once (store `database_id` in config + wrangler.toml), then
   `--remote --file=…`, then `wrangler deploy` and `wrangler secret put MCP_BEARER_TOKENS` on first
   deploy. Smoke-test `/health` and one `tools/call`.
5. Record it: `python3 .claude/db/db.py publish-record --database <name> --database-id <id> --url <worker-url>`
   stamps `last_publish`, stores the D1 settings in config, and appends the `wiki/_log.md` entry.
   Report the MCP URL and how to connect a client.

Cloudflare actions are outward-facing: confirm with the user before the first `d1 create`, `deploy`,
or any secret write; re-publishes of data to an existing database are routine.

### `status` / `verify` / `audit`

`db.py status` (freshness, counts, sizes, queries logged), `db.py verify` (health, exit code),
`db.py audit [--top|--errors]` (what agents actually ran — the feedback loop for views and docs).

## No wiki

Do not refuse and do not manufacture a wiki. Offer `/wiki:init` once (a wiki gives the schema for
free); if declined, follow `references/schema-design.md` § "No wiki": scan for structured sources
(markdown with frontmatter under docs/, adr/, decisions/, plans/, reviews/, specs/; CSV/JSON/JSONL
under data/; existing SQL/Prisma/Drizzle schemas; OpenAPI), interview for what the DB must answer and
which sources are the record, map each source to a collection (`--markdown name=dir` gives its pages a
`default_type` so a typed view exists even without `type:` frontmatter; `--tabular path` loads a file
as its own table), seed minimal frontmatter where sources lack it (ask first), build, then install the
standalone mandate (the engine picks `claude-md-block.standalone.md` automatically). The mandate mirrors
the wiki-first rules: query before answering, update sources then sync, never write to the DB, log.

## Guardrails (why each exists — details in `references/guardrails.md`)

| Guardrail | Where | Why |
|---|---|---|
| Read-only connection (`?mode=ro`) + SQLite authorizer denying all but SELECT/READ/FUNCTION | `db.py open_ro` | writes fail structurally, whatever the SQL says |
| Validator: one statement, SELECT/WITH/EXPLAIN only, forbidden-keyword scan | `validate_sql`, Worker `validate` | clear error messages before the DB sees the text; the D1 Worker has no authorizer, so this is its policy |
| Statement timeout (progress handler) | `open_ro` | a runaway recursive CTE ends in 5 s, not never |
| Row cap + cell truncation, CSV default | `cmd_query` | tokens: 200 rows × 400 chars is a screen, not a context window |
| Audit log (`audit.sqlite`, `_query_log` on D1) | `audit_write`, Worker `audit` | traceability, and the source of "which queries deserve a view" |
| PII: `exclude_keys` / excluded paths in config | `upsert_page` | what is not loaded cannot leak |
| Bearer tokens on the Worker; fail closed if unset | Worker `authorized` | D1 has no read-only role — the Worker is the role |

## Output discipline

- After `init`/`sync`/`publish`: counts, what changed, next command. No prose about how SQLite works.
- After a `query`: the answer, the query you ran (one fenced block), the pages to open. Never paste
  hundreds of rows; aggregate or narrow.
- Every wiki-affecting operation (init, full rebuild, publish) leaves a `wiki/_log.md` entry — the
  engine writes init/build; you write publish.

## Edge cases

- **No `python3`**: stop; the engine and hook need it. Everything else is optional (`uv` → no local
  MCP; `wrangler` → no D1).
- **No FTS5 in the linked SQLite** (rare): `search` falls back to LIKE; views still work; say so.
- **Huge vaults (> 5k pages)**: still fine (hashing is the cost); raise the hook `timeout` in
  `.claude/settings.json` if it ever trips.
- **Several wikis / monorepo**: one config per repo root; add extra vaults as more markdown
  collections (`--markdown client-b=wiki-b`) rather than a second database.
- **`.mcp.json` or `settings.json` already exist**: merged, never overwritten; existing servers/hooks
  are kept. Invalid JSON there stops init with the path to fix.
- **User edits `SCHEMA.md`**: regenerated on next sync — move the note into `views.sql`/config.
- **D1 free tier**: 500 MB per database; the export warns. Raw transcripts are usually the bulk —
  `--no-raw` or a smaller `max_bytes` in the raw collection is the lever.

## Reference files

- `references/schema-design.md` — base schema, how typed views and column docs are derived, curated
  view conventions, and the full **no-wiki** procedure (discovery checklist, interview, mapping to
  config, seeding frontmatter, mandate). Read before `init` on a project without a wiki.
- `references/guardrails.md` — each guardrail: mechanism, failure it prevents, what to do when it
  fires, PII policy, D1/Worker equivalents.
- `references/d1-publish.md` — publish runbook, limits, dry run, troubleshooting, client connection.
- `templates/` — hook, CLAUDE.md blocks (wiki / standalone), curated views (wiki / generic), local MCP
  server, D1 Worker scaffold. `scripts/db.py` — the engine (`--help` lists every subcommand).
- `scripts/test_db.py` — regression tests (parsing determinism, guardrails, sync, link resolution, D1
  export, install idempotency, no-wiki path, ontology integration). Run `python3 scripts/test_db.py` after
  any engine change; add a test for every defect fixed.
