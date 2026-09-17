# project-ontology — enforceable dot-notated ontology over the wiki, the database, and the agent context

**Status:** done — designed, built, verified and released 2026-09-17 as plugin v2.8.0. Design interview
below; verification evidence at the end.
**Requested:** 2026-09-16, during the `project-db` build.

## The ask

Generate an **enforceable, dot-notated ontology** and apply it to the database, the wiki, and the
third surface (the request said "database, Wiki and database" — read as the **agent context layer**:
CLAUDE.md, hooks, SCHEMA.md). A **hook enforces use of the ontology in all places**.

## Why this is needed — evidence from this plugin's own wiki (scratch copy, 2026-09-17)

| Drift | Evidence |
|---|---|
| Scope written two ways | `client: Boston Beer Company` on 10 pages (5 meetings, 5 questions), `boston-beer-company` on 40, `shared` on 2 |
| Values no vocabulary declares | `status: draft` on 19/19 features; `priority: P0` on 2 (template: `P1\|P2\|P3`); feature `category` `custom-requests`, `inventory`; entity `category: process`, `status: legacy` |
| Four vocabularies that disagree | `wiki/_schema/SCHEMA.md` (gap status `open\|under-review\|resolved\|workaround`), `_schema/templates/gap.md` (`open\|mitigated\|resolved\|accepted`), `skills/wiki-lint/references/checks.md` (feature status `identified\|in-design\|in-dev\|delivered\|deprecated`), `skills/wiki-ingest-meeting` (writes `status: identified`) |
| Link targets | 745 wikilinks: 253 exact, 132 resolve only by title/label/folder fallback, 360 broken; `[[feature\|order-management]]` inverted form on all 10 gaps' `related-feature` |

## Settled decisions (design interview, 2026-09-17)

| # | Question | Decision |
|---|---|---|
| 1 | Where the id lives (sketch vs draft) | **Plain values, derived ids.** Pages keep `severity: critical`; the ontology declares `gap.severity.critical`; page ids are derived from the path (`client.boston-beer-company.gap.co-op-billing`) and never written into pages. |
| 2 | Default policy + migration | **Strict ratchet.** A write is blocked only when it *adds* a violation the file did not already have; existing violations are reported, not blocking. Tags default to `warn`. One gated `/ontology:apply` pass rewrites mechanical cases (aliases, case/slug variants, deprecated → replacement, uniquely-resolvable links); humans fix the rest on touch. |
| 3 | Third surface | **Wiki + DB + agent context** (CLAUDE.md managed block, SessionStart banner, SCHEMA.md namespaces, rendered ONTOLOGY.md). Codebase identifiers are out of scope. |
| 4 | Packaging + hook timing | **Separate `project-ontology` skill** (`/ontology:*`), project-db a consumer; **PreToolUse** hook blocks before the write (the post-edit file is computable — `Edit` is exact string replacement — so the draft's reason for PostToolUse does not hold). |
| 5 | Multi-client vaults | Vocabularies **global** (`gap.severity.*`); page ids **path-scoped** (`client.<slug>.<type>.<slug>`). |
| 6 | Who approves | **Human-only** gate (plugin stance: humans own every gate). |

Hook facts verified against current Claude Code docs (2026-09-17): PreToolUse exit 2 blocks and feeds
stderr to Claude; `permissionDecision: "deny"` blocks in every permission mode; `"ask"` shows the
permission prompt; PreToolUse has **no** non-blocking context channel, so non-blocking warnings go
through **PostToolUse `additionalContext`**; timeouts are in seconds; `Write`/`Edit` input field names
differ between doc versions (`file_path`/`path`, `content`/`contents`) — the hook accepts both.

## Design (as built)

### Files

| Path | What | Git |
|---|---|---|
| `wiki/_schema/ontology.yaml` (no wiki: `.claude/ontology/ontology.yaml`) | the declaration — the only source of truth | committed |
| `wiki/_schema/ONTOLOGY.md` | rendered for humans and agents; never hand-edited | committed |
| `.claude/ontology/ontology.py` | vendored stdlib engine (hook, CLI, project-db import) | committed |
| `.claude/ontology/config.json` | governed roots/excludes, ontology file path | committed |
| `.claude/ontology/state.json` | cached last full check (banner speed) | gitignored |
| `.claude/hooks/ontology-guard.sh` | PreToolUse (Write/Edit/MultiEdit + Bash) and PostToolUse dispatcher | committed |
| `.claude/hooks/ontology-context.sh` | SessionStart banner | committed |

### Term model — one id grammar, five kinds

`<segment>(.<segment>)*`, segments `[a-z0-9][a-z0-9-]*`. Each section of `ontology.yaml` holds one kind:

| Section | Id shape | Example | Governs |
|---|---|---|---|
| `types` | `type.<name>` | `type.gap` | the `type:` field; a declared type is also the namespace of its vocabularies |
| `vocabularies` | `<type>.<field>.<leaf>` | `gap.severity.critical` | a controlled frontmatter field (`value:` carries the exact spelling when it is not the leaf, e.g. `P1`, `🟡`) |
| `entities` | `<namespace>.<slug>` | `client.boston-beer-company` | scope fields (`client:`) — declared concepts that pages point at |
| `relations` | `rel.<name>` | `rel.related-feature` | frontmatter fields holding wikilinks; `domain` / `range` = page types |
| `tags` | `tag.<path>` | `tag.gap.critical` (`gap/critical`) | the `tags:` field |

Term attributes: `label`, `definition`, `status` (`proposed|approved|deprecated`), `value`, `aliases`,
`proposed-aliases`, `since`, `replaced-by`, `approved-by`, `approved-on`, `reason`, `source`.
`fields:` binds `<type>.<field>` (or `*.<field>`) to a kind — only bound fields are controlled; the
rest are free text. Page entity ids are **derived** (never declared): `ids.scope-folders` maps
`clients/` → `client`, so `clients/boston-beer-company/gaps/co-op-billing.md` (type gap) is
`client.boston-beer-company.gap.co-op-billing`; a folder note (`overview`, `README`, `index`) is the
scope entity itself (`platforms/merchtank/overview.md` → `platform.merchtank`); pages outside a scope
folder are `<type>.<slug>`.

### Rules (one implementation, shared by hook, CLI, project-db, wiki-lint, CI)

| Rule | Fires when | Family |
|---|---|---|
| `type-unknown` / `type-deprecated` | `type:` not registered / deprecated | type |
| `value-unknown` | a controlled value is not a registered term | vocab · entity · tag |
| `value-noncanonical` | value is an alias or a case/slug variant of a term | vocab · entity · tag |
| `value-deprecated` | term is deprecated (message names `replaced-by`) | vocab · entity · tag |
| `value-proposed` | term registered but not approved — **always warn** | vocab · entity · tag |
| `link-broken` / `link-ambiguous` / `link-noncanonical` | `[[target]]` resolves to no page / several pages / only via title-label-folder fallback | link |
| `relation-broken` / `relation-range` | relation field has no resolvable link / target type outside `range` | relation |
| `id-duplicate` | two governed files derive the same id (vault check) | id |

Policy per violation: most specific of `policy.overrides[<binding>]` → `[<namespace>]` → `[<family>]`
→ `policy.default` (`strict|warn|off`). Messages name the field, the value, the approved terms
(closest first), and the exact `propose` command.

### Enforcement

- **PreToolUse `Write|Edit|MultiEdit`** → `ontology.py hook pre`: reconstruct the post-write text
  (Write content; Edit/MultiEdit exact replacement on the file on disk), check old and new, block
  (exit 2, stderr to Claude) only violations that are **new** and `strict`. Writes to `ontology.yaml`
  itself must parse, and under `approval: human` may not approve a term (`status → approved`,
  `approved-by` change) — agents propose, humans approve.
- **PostToolUse `Write|Edit|MultiEdit`** → `hook post`: non-blocking `additionalContext` listing what
  still stands in the written file (pre-existing, `warn`, `value-proposed`).
- **PreToolUse `Bash`** → `hook bash`: `ontology.py approve|deprecate` returns
  `permissionDecision: "ask"` so a human confirms; the skill also confirms with `AskUserQuestion`
  (the fallback where a permission mode suppresses prompts). A Bash write that edits governed pages
  bypasses Write/Edit hooks — the SessionStart banner, `check --changed-since` in CI, and the
  project-db sync gate are the backstops.
- **Vault-wide**: `check --all` (exit 1 on strict violations), `check --changed-since <ref>` (CI
  ratchet: only violations new relative to the base ref), project-db sync (`ontology_violations`),
  wiki-lint Check 8.

### Governance

`propose <id>` (any agent; `status: proposed`, `since`, `source`) → `approve <id>… --by <human>`
(proposed aliases approved with the term) → `deprecate <id> --replaced-by <id> --reason … --by <human>`.
Every transition appends a `wiki/_log.md` entry. `apply [--dry-run]` rewrites aliases, case/slug
variants, deprecated values with a replacement, and uniquely-resolvable noncanonical links — frontmatter
and link text only, every other byte preserved; confirm the dry run with the user first.

### `/ontology:init`

1. `ontology.py init --scan` mines: observed `type:` values; template `key: # a|b|c` vocabularies;
   SCHEMA.md YAML-block vocabularies (conflicts with templates recorded, not resolved); observed values
   per controlled field; scope folders and scope-field values; tags; frontmatter fields holding
   wikilinks (relation candidates, range from resolved targets or the field name); link statistics.
   Output: `.claude/ontology/init-report.json`.
2. Interview (`AskUserQuestion`, grouped, ≤4 per call): vocabulary conflicts (template vs SCHEMA.md),
   each outside value (approve / alias of / deprecate → replacement / leave proposed), which
   uncontrolled low-cardinality fields to bind, tag policy, policy overrides.
3. `init --write [--decisions decisions.json | --defaults]`: declared values (templates, SCHEMA.md,
   scope folders) → `approved`; observed-only values → `proposed`; slug/case variants → proposed
   aliases. **Every observed value is classified; nothing is silently approved.** Renders ONTOLOGY.md,
   syncs template comments to `# <binding>: a|b|c`, installs hooks + CLAUDE.md block + SessionStart
   banner, logs.

### Database (project-db, small additions)

`ontology_terms`, `ontology_aliases`, `ontology_fields`, `ontology_violations` tables and
`pages.ontology_id`, loaded at sync by importing the vendored engine (no second rule implementation);
typed-view column docs name the binding and its approved values; SCHEMA.md "Ontology" section; banner
line; `verify` checks; `config.ontology.gate: off|warn|fail`; `search` expands aliases to canonical
values; `SCHEMA_VERSION` 1 → 2. `ontology_violations` is a table materialized by the shared engine at
sync rather than a SQL view: nearest-term suggestions and link resolution are not expressible in SQL,
and one implementation keeps the hook and the database from disagreeing.

### Consumers

| Skill | Change |
|---|---|
| `wiki-lint` | Check 8 "ontology" (runs `check --all --format lint`); Check 6 reads vocabularies from the ontology (else template comments) instead of its hard-coded lists |
| `wiki-init` | templates carry the binding next to each controlled key; offers `/ontology:init` after init |
| `wiki-ingest-meeting` / `-document` | write registered values (initial status from the vocabulary, not a hard-coded `identified`); propose unknown values instead of inventing them |
| `knowledge-loop` | rules cite ontology term ids (`terms:`) when an ontology exists |
| `project-db` | tables/view docs above; deterministic frontmatter parsing (no PyYAML branch) |

## Work breakdown

- [x] Engine `skills/project-ontology/scripts/ontology.py` (stdlib) + `test_ontology.py` — 59 tests
- [x] Hooks (`templates/ontology-guard.sh` pre/post/bash, `ontology-context.sh`), CLAUDE.md blocks, ONTOLOGY.md renderer, install
- [x] Skill docs: `SKILL.md`, `references/{term-model,enforcement,governance,init-interview}.md`, `commands/ontology/*` (7)
- [x] project-db integration (engine 1.1.0, schema v2) + tests — 23 tests
- [x] Consumers: wiki-lint (Check 8; Check 6 vault-driven), wiki-init, wiki-ingest-meeting/-document, knowledge-loop
- [x] Evals: `evals/fixtures/ontology-vault` (planted drift), `evals/evals.json` (3 evals), `evals/grade.py` (re-runs installed hooks), runs + benchmark
- [x] Acceptance on a copy of this plugin's wiki
- [x] Plugin bookkeeping: plugin.json + marketplace.json 2.8.0, README, CLAUDE.md, `wiki/_log.md`

## Acceptance

- `/ontology:init` on this plugin's wiki yields an ontology with every observed value classified
  (approved or proposed) and zero unknowns after the interview.
- Writing a gap page with `severity: urgent` is blocked (strict) with the nearest approved terms named.
- `SELECT * FROM ontology_violations` is empty on a clean vault and non-empty after a planted error.
- CLAUDE.md block and SessionStart banner installed; `wiki-lint` reports the ontology dimension.
- Evals: fixture vault with planted violations; assertions that the hook blocks a bad `severity`,
  `ontology_violations` lists it, and a proposal → approval clears it.

## Verification (2026-09-17)

### Acceptance

| Criterion | Evidence |
|---|---|
| `/ontology:init` on this plugin's wiki classifies every observed value, zero unknowns | scratch copy, defaults: 241 terms (93 approved, 148 proposed); observed values 51 approved · 147 proposed · 1 noncanonical · **0 unknown**; `test_plugin_wiki_performance_and_zero_unknowns` |
| A gap page with `severity: urgent` is blocked, nearest approved terms named | guard script exit 2: "severity: `urgent` is not a registered gap.severity value — approved: critical · high · medium · low" + the propose command; `test_write_with_unknown_severity_is_blocked_naming_approved_terms`; grader re-runs the installed hook |
| `ontology_violations` empty on a clean vault, non-empty after a planted error | `test_db.OntologyIntegrationTests.test_clean_vault_then_planted_error` |
| CLAUDE.md block + SessionStart banner installed; wiki-lint reports the ontology dimension | install tests; banner printed by `ontology-context.sh`; eval 3 lint report contains Check 8 |
| Evals: hook blocks a bad severity, violations listed, proposal → approval clears it | eval 1 (hook), eval 3 (listing), eval 2 + `test_proposal_then_approval_clears_the_violation` |

Plugin wiki (scratch copy, defaults, nothing edited): 698 open violations — strict 445 (288 broken links, 130
noncanonical links, 10 relation-broken, 10 client spelling variants, 7 ambiguous links), warn 253 — none
blocking; `apply --dry-run` = 140 mechanical rewrites in 31 files; project-db `verify` 32/32 with the
ontology loaded. Performance: hook 0.07–0.13 s per write on this wiki, 0.5–0.7 s on a synthetic 5,070-page
vault; full check 2.3 s cold there, 0.2 s cached (`init --write`, which runs the full check, took 55 s before the fix below).

### Evals (iteration 1, one run per configuration)

| Eval | With skill | Baseline | Baseline misses |
|---|---|---|---|
| 1 init-and-enforce (cold start on the fixture vault) | 11/11 · 888 s · 321k tok | 9/11 · 1,619 s · 320k tok | no SessionStart surfacing; rewrote 2 content pages unasked |
| 2 propose-approve (ontology pre-installed) | 10/10 · 579 s · 236k tok | 9/10 · 639 s · 263k tok | rewrote 2 pre-existing pages unasked (inferred: prompted by the old CLAUDE.md rule 5 wording "fix them when you are sure" — reworded) |
| 3 lint-ontology-dimension (wiki-lint skill) | 8/8 · 738 s · 253k tok | 7/8 · 825 s · 290k tok | did not log the lint run (interpretive) |
| **Mean** | **100%** · 735 s · 270k tok | **86.4% ± 3.4** · 1,028 s · 291k tok | |

Fixture `evals/fixtures/ontology-vault` plants a client spelling variant, an undeclared `P0`, an inverted
`[[type|slug]]` relation, a title-only link, a relation pointing at the wrong page type, a broken link, and a
template-vs-SCHEMA.md vocabulary conflict. `evals/grade.py` re-runs the hooks each run installed (block
`severity: urgent`, allow `severity: high`, allow an unrelated edit to a page with a pre-existing
violation) instead of trusting transcripts; oracle solutions score 11/11 · 10/10 · 8/8 and do-nothing
runs 1/11 · 1/10 · 1/8. Workspace (gitignored): `skills/project-ontology-workspace/iteration-1/`
(`benchmark.md` has the analyst notes). One run per configuration — indicative, not statistical; the
eval 1 baseline reported that this repo's CLAUDE.md (which documents the skill) loaded mid-run.

### Defects found and fixed during the build

| Defect | Found by | Fix · pinned by |
|---|---|---|
| project-db parsed frontmatter with PyYAML when installed (`related: [[Page]]` lost its link on those machines) and dropped unindented YAML block lists | parser-parity design | subset parser only, unindented lists · `test_parse_never_depends_on_pyyaml`, parity test |
| Links inside fenced/inline code counted as links (project-db and engine) | review | `visible_body` · `test_links_inside_code_are_not_links` |
| `[[gap\|slug]]` resolved to `_schema/templates/gap.md` — a false "ok" | first real-vault run | templates excluded as link targets; the type word disambiguates label links · two tests |
| Vault check was quadratic (folder fallback walked every file per broken link; difflib per link): 55 s at 5,070 pages | synthetic benchmark | folder index, suggestions only on single-file checks · `test_vault_check_is_not_quadratic_in_broken_links` |
| Folder-note titles not recognized as entity spellings; relation range absorbed the bad targets it exists to catch | eval fixture | title spellings, name-stated range · `test_folder_note_title_is_a_spelling_and_field_name_states_the_range` |
| An agent could flip `approval` to agent and approve in one write; removing/re-spelling terms and loosening policy were not gated | review | gate on the pre-write approval mode · `test_ontology_file_guard` |
| `apply` rewrote every textual copy of a link, including inside code/comments | review | span edits · `test_apply_touches_only_the_flagged_link_not_copies_in_code` |
| `check --changed-since` passed silently when the project is a git subfolder | plugin validator | `--relative`, `-z`, `REF:./path` · `test_changed_since_works_from_a_subfolder_of_the_repo` |
| Unquoted `$CLAUDE_PROJECT_DIR` in hook commands (ontology and project-db): a space in the path silently disabled the hooks | plugin validator, eval 1 | quoted, install upgrades old entries · two tests |
| `propose` could not place a value in a ranked vocabulary (both eval-2 agents hand-moved `urgent`) | eval 2 | `--before`/`--after` · `test_propose_can_place_a_term_in_ranking_order` |
| CLAUDE.md block invited fixing pre-existing violations as a side effect (eval-2 baseline rewrote 3 pages unasked) | eval 2 | rule 5 reworded · install test assertion |
| Stray separator in ONTOLOGY.md alias cells; "usable now" wording under `policy.proposed: strict`; logs' `updated:` never bumped (engine and project-db) | eval 1 | · `test_alias_cell_and_strict_proposed_wording`, `test_log_updated_date_follows_new_entries`, `HookPathTests` |
| wiki-lint Check 6 hard-coded vocabularies and required keys that contradicted the vault; example records' severities contradicted their headings | this plan's evidence, eval 3 | vault-driven Check 6, one issue per page, severities aligned |
| wiki-ingest-meeting wrote `status: identified` (undeclared) and its command frontmatter was invalid YAML | this plan's evidence, plugin validator | vocabulary-driven defaults; quoted `argument-hint` |
| `.gitignore` `skills/*-workspace/` also ignored the real `skills/bun-workspace/`; project-db evals hard-coded an absolute path; CLAUDE.md tree listed six non-existent `commands/wiki/*.md` files | plugin validator, review | negation rule; relative path; tree corrected |

## History

- 2026-09-16 — backlog entry written during the `project-db` build; a forked session drafted an
  engine-integrated version (the ontology living inside `db.py`, an explicit `ontology:` key per page,
  PostToolUse). Parked so the project-db eval iteration stayed clean.
- 2026-09-17 — design interview (decisions above) superseded that draft: plain values with derived ids,
  a separate skill, a PreToolUse ratchet. The draft folder was deleted once this plan carried its
  rationale — the "Settled decisions" table above is the record of what it got wrong and why.
- 2026-09-17 — built, evaluated and verified (sections above).
- 2026-09-17 — released: `project-db` (2.7.0) and `project-ontology` (2.8.0) committed and merged to
  `main`, plugin version 2.8.0.
