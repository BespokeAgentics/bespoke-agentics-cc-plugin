# Schema design — how the database is shaped, and how to shape it without a wiki

The schema is the prompt. Every decision here is about making the agent's first query right.

## 1. Base tables (always present)

| Table | One row per | Why it exists |
|---|---|---|
| `pages` | markdown page | the index of the record: path, slug, type, title, scope (`client`), status, created/updated, full `frontmatter` JSON, `body`, word count, content hash |
| `page_fields` | frontmatter key (lists → one row per item) | filter on *any* key without knowing the views: `WHERE key='resolution-approach' AND value='custom-dev'` |
| `links` | `[[wikilink]]` in a body or frontmatter value | graph questions: backlinks, broken links, "what did this meeting touch"; `to_id` NULL = broken; `match` says how it resolved (slug / title / fuzzy) |
| `tags` | tag | `tag_counts`, "everything tagged legacy" |
| `sources` | cited raw document | traceability from synthesis to evidence; `raw_id` when the file was loaded |
| `sections` | heading in a body | fetch "## Current State" of one page instead of 13 KB of body |
| `raw_documents` | cited file that exists (≤ 5 MB by default) | transcripts, analyses, exports — full text, own FTS (`raw_fts`) |
| `log_entries` | `## heading` in `_log.md` | "what changed when" is a query, not a scroll |
| `column_docs` | documented column | the docs are data: the schema summary, `db_schema`, and any agent can read them |
| `sync_state` | engine key | last sync, counts, the rendered `schema_md` (published to D1 so the Worker can serve it) |
| `pages_fts`, `raw_fts` | FTS5 external-content indexes | `MATCH` with ranking and snippets; rebuilt after every changed sync |
| `ontology_terms`, `ontology_aliases`, `ontology_fields`, `ontology_violations` | term / alias / controlled field / current violation | present when **project-ontology** is installed (empty otherwise): the legal values of every controlled field, their lifecycle status, and every violation computed by the same engine the write hook runs; `pages.ontology_id` carries each page's derived dot-notated id |

Identity is `pages.path` (unique) with a stable integer `id`; `slug` is the filename stem and may
collide across folders (`README`, `overview`) — link resolution prefers the same scope when it does.

HTML comments in bodies are template guidance, not content, and code is code: links inside `<!-- -->`,
fenced code blocks and inline code are ignored.

Frontmatter is parsed by the engine's own YAML subset parser — never PyYAML, even when installed. With
PyYAML, `related: [[Page]]` becomes a nested list and the link disappears, so one wiki would index
differently on two machines. Block lists may be indented or written at the key's own indent.
`_schema/*` and `_lint-report-*` are excluded by default (docs *about* the wiki, whose example links
would all be "broken").

## 2. Typed views (generated every sync)

For each distinct `pages.type` (minus `index`, `log`, `lint-report`), a view named by the plural
(`entity` → `entities`, `gap` → `gaps`) with:

- base columns: `id, path, slug, title, client (= pages.scope), status, created, updated, word_count, body`
- one column per frontmatter key, in **template order first** (`_schema/templates/<type>.md`), then
  any key observed on real pages of that type; `some-key` becomes `some_key`; multi-valued keys
  (`tags`, `sources`) are left to their tables. Values are `json_extract(frontmatter, '$."key"')`, so a
  list value comes back as JSON text.

Column docs come from the template's `key: # a|b|c` comments. That is why `severity — critical|high|
medium|low` appears in SCHEMA.md without anyone writing documentation: the wiki author already did.
When project-ontology is installed, a controlled column's doc comes from the ontology instead
(`severity: → gap.severity: critical|high|medium|low (proposed: urgent)`) — the declared, enforced
vocabulary rather than a comment that may have drifted — and every typed view gains `ontology_id`.

Generated views are dropped and recreated each sync; never hand-edit them — add a curated view.

## 3. Curated views (`.claude/db/views.sql`)

Seeded once from `templates/views.wiki.sql` (or `views.generic.sql`); after that the file is the
user's. Conventions that keep them robust:

- Build on `pages` + `json_extract`, not on generated views (a generated view exists only when its
  type has pages; a curated view must compile on an empty vault too).
- Put `-- doc: …` on the line after `AS` — it becomes the view's description.
- Alias `p.scope AS client`. Keep `body` out of wide views. Always include `path` so the agent can
  open the record.
- Prefer status-normalizing `COALESCE(p.status,'open')` over trusting every page to have a status.

Which queries deserve a view: `python3 .claude/db/db.py audit --top` — anything run three times, and
anything that took three attempts to get right (`audit --errors` shows the attempts).

## 4. Tabular collections

A CSV / TSV / JSON (array of objects) / JSONL file becomes its own table (`config.json → tabular[]`):
columns from the header/keys (sanitized), types inferred (INTEGER / REAL / TEXT), `_row` as key,
reloaded whole when the file's hash changes. Add `doc` and `column_docs` in the config entry so
SCHEMA.md documents it:

```json
{"name": "customers", "kind": "csv", "path": "data/customers.csv", "table": "customers",
 "doc": "CRM export, one row per account", "column_docs": {"tier": "gold|silver|bronze"}}
```

## 5. No wiki — designing the schema from the project

Goal: the same shape (collections → pages → typed views) fed by whatever the project already uses as
its record, plus a mandate that makes the DB the first stop. Do not invent entity types the project
does not have; discover them.

### 5.1 Discovery scan (silent, before the interview)

Look for, and count:

- Markdown with YAML frontmatter, grouped by directory: `docs/`, `adr/`, `docs/adr`, `decisions/`,
  `plans/`, `reviews/`, `specs/`, `rfcs/`, `runbooks/`, `notes/`, `meetings/`. Note which have a
  `type:` key already and what the common keys are (a `status:` with a small vocabulary is gold).
- Markdown without frontmatter that is still structured (numbered ADRs `0001-*.md`, dated meeting
  notes) — candidates for a `default_type` collection.
- Tabular data: `data/**/*.csv|json|jsonl`, fixtures, exports.
- Existing schemas that describe the domain: `schema.prisma`, Drizzle/Knex migrations, `*.sql`,
  OpenAPI/GraphQL specs — not loaded, but they name the entities and vocabularies you should mirror.
- `CLAUDE.md` / `README.md` sections that declare where decisions and docs live.

### 5.2 Interview (one `AskUserQuestion` call, 2–4 questions)

1. **What must the database answer?** Offer concrete options built from the scan ("which ADRs are
   accepted and touch auth", "customer accounts by tier", "open review findings by severity"). The
   answers decide which collections matter and which views to seed.
2. **Which sources are the record?** Multi-select from the scan (docs/adr, plans/, data/*.csv…).
   Anything not selected is not loaded — the DB should not index noise.
3. **Entity types and statuses.** For markdown collections without `type:`: what type name each
   directory represents, and the status vocabulary if one exists (`proposed|accepted|superseded`).
4. **Exclusions / PII.** Keys or paths never to load.

### 5.3 Map answers to config

- Each selected markdown directory → `--markdown <type>=<dir>` (the engine sets `default_type` from
  the name, so pages without `type:` still get a typed view). Real `type:` frontmatter wins when
  present.
- Each tabular file → `--tabular <path>`; then add `doc`/`column_docs` to `config.json`.
- If sources lack frontmatter entirely and the user wants status/date columns, offer to seed minimal
  frontmatter (`type`, `status`, `created`) on those files — with confirmation, as a separate diff.
  Frontmatter is the contract that makes the typed view useful; without it the view is just bodies.
- Seed 3–5 curated views in `views.sql` that answer the questions from 5.2 directly (e.g.
  `accepted_adrs`, `open_findings`). Name them after the question.

### 5.4 Enforce the source of truth

The engine installs `templates/claude-md-block.standalone.md` (no wiki detected): query before
answering, update sources then sync, never write to the DB, follow the schema, log to
`.claude/db/LOG.md`. The SessionStart hook makes it visible every session. If the project later
adopts a wiki (`/wiki:init`), re-run `/db:init --force`: the wiki collection is added and the block
switches to the wiki flavour.

### 5.5 Iterate

Week one, run `audit --errors` and `audit --top`: errors show missing docs or misleading column
names (fix in templates/config), repeats show missing views. This loop — audit → docs/views → fewer
errors — is the whole method.
