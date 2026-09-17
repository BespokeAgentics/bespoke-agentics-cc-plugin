# Init — what the scan mines, the interview, decisions.json

## What `init --scan` mines

| Source | Becomes | Default status |
|---|---|---|
| `type:` values on pages; page templates; the SCHEMA.md type list | `types` | approved when a template or SCHEMA.md declares it, or it is structural (index, log, lint-report); else proposed |
| template comments `key: # a\|b\|c` (or `# <binding>: a\|b\|c`) | a vocabulary binding + terms | approved |
| SCHEMA.md fenced YAML blocks (`type: gap` + `severity: critical\|high`) | a binding + terms, for fields the templates do not control and that pages or templates use | approved |
| a field both declare with different values | a **conflict** in the report; the template wins by default | — |
| observed values outside the declared vocabulary | terms | **proposed** |
| observed spelling variants of a declared value | proposed aliases | proposed |
| folders under `clients/`, `projects/`, `platforms/`, `teams/`, `domains/`, `products/`, `orgs/` | entities `<namespace>.<folder>` + `ids.scope-folders` | approved |
| the scope field (`client:` for `clients/`) | `*.client` entity binding | — |
| SCHEMA.md literal alternatives for the scope field (`{client-slug}\|shared`) | entities (`client.shared`) | approved |
| observed tags | `tags` terms + `*.tags` binding (policy `warn`) | proposed |
| frontmatter fields whose values hold `[[links]]` (not `sources`/`tags`) | relations; `range` from the resolved targets' types, else from the field name (`related-feature` → feature) | proposed |
| low-cardinality free-text fields | `unbound_candidates` in the report (not bound) | — |
| body links | link statistics | — |

**Nothing observed is silently approved.** `init --write` classifies every observed value and exits 1
if any is left unknown.

## Reading the scan summary

```
types                 page counts per type
controlled_fields     binding → declared_by (template|schema), values outside the declaration
conflicts             binding, template values, SCHEMA.md values + line
scopes                namespace → folder members, observed values (spelling variants show up here)
tags                  number of distinct tags
relations             field → domain, range
unbound_candidates    <type>.<field> worth considering
links                 ok / noncanonical / ambiguous / broken (body links)
```

The full report is `.claude/ontology/init-report.json` (observed value counts per field, per tag).

## The interview

`AskUserQuestion`, ≤4 questions per call, ≤3 calls. Order by pages affected. Every option names its
consequence in page terms. Skip any question the scan already answers (no conflicts → no conflict
question). Put the recommended option first.

### 1. Vocabulary conflicts (one question per conflicting binding)

> **gap.status** — the template says `open | mitigated | resolved | accepted`, SCHEMA.md (line 385) says
> `open | under-review | resolved | workaround`. Pages use: `open` (10). Which list is the vocabulary?

- *Template (Recommended when pages were created from it)* — SCHEMA.md-only values are not registered.
- *SCHEMA.md* — template-only values are not registered; the template comment is rewritten to match.
- *Both (union)* — every value from either list is approved.

→ `"vocab_source": {"gap.status": "template" | "schema" | "union"}`

### 2. Values outside the vocabulary (group per field; biggest first)

> **feature.status** — 19 features use `draft`, which neither the template nor SCHEMA.md declares
> (SCHEMA.md: `active | deprecated | in-discovery | blocked`). What is `draft`?

- *A real status — approve it* → `"approve": ["feature.status.draft"]` (ask for a one-line definition)
- *Same as an approved value* (name it) → `"deprecate": {"feature.status.draft": "feature.status.in-discovery"}`; `apply` rewrites the pages
- *Decide later — leave proposed* (default: usable, flagged as warn)

For many values in one field, ask about the field as a whole ("approve all observed categories" / "leave
proposed") and let the user name exceptions under Other.

### 3. Scope spelling variants

> **client** — 10 pages write `Boston Beer Company`, 40 write `boston-beer-company` (the folder name).

- *Alias; rewrite pages to `boston-beer-company` (Recommended)* → `"approve_aliases": ["client.boston-beer-company"]` then offer `apply`
- *Alias only, do not rewrite yet* → same decision, no apply
- *Leave the variant proposed*

### 4. Tags, unbound fields, policy (one call)

- **Tags** (N distinct, most used once): *leave proposed, warn-only (Recommended)* · *approve all observed* (`"approve": ["tag.*"]`) · *enforce strictly after approving* (`"policy": {"overrides": {"tag": "strict"}}`).
- **Unbound candidates** (multiSelect): control `integration.auth-method`, `platform.status`… → `"bind": {"integration.auth-method": "vocab"}` (observed values become proposed terms).
- **Relations** inferred: confirm `rel.related-feature` → feature pages → `"approve": ["rel.related-feature"]`.
- **Policy**: *strict for values and links, warn for tags (Recommended)* · *warn everywhere while migrating* (`"policy": {"default": "warn"}`).

## decisions.json

Every key is optional; ids accept shell-style globs where a list is expected.

```json
{
  "name": "bbc-wiki",
  "vocab_source": {"gap.status": "template", "feature.priority": "union"},
  "approve": ["feature.status.draft", "tag.*", "rel.related-feature"],
  "propose": ["feature.category.inventory"],
  "deprecate": {"feature.priority.p0": "feature.priority.p1", "entity.status.legacy": ""},
  "aliases": {"client.boston-beer-company": ["BBC"]},
  "approve_aliases": ["client.boston-beer-company"],
  "bind": {"integration.auth-method": "vocab"},
  "unbind": ["integration.frequency"],
  "labels": {"feature.status.draft": "Draft"},
  "definitions": {"feature.status.draft": "Captured from a meeting; not yet assessed"},
  "policy": {"default": "strict", "overrides": {"tag": "warn"}},
  "terms": {"client.acme-labs": {"label": "Acme Labs", "status": "approved", "definition": "Second client"}},
  "fields": {"*.owner": {"kind": "entity", "namespace": "person"}}
}
```

Write it to `.claude/ontology/decisions.json`, then:

```bash
python3 "$SKILL_DIR/scripts/ontology.py" init --write --root . --skill-dir "$SKILL_DIR" \
  --decisions .claude/ontology/decisions.json --by "<the user's name>"
```

`approve` entries are stamped `approved-by: <--by>`; values declared by templates / SCHEMA.md / folders
are stamped `approved-by: declared in source`. Re-running `init --write` on an existing ontology only
adds newly observed values (as proposed) — use `--force` to rebuild from scratch.

## Worked example — this plugin's wiki (scratch copy, 2026-09-17, defaults only)

| Scan finding | Default outcome |
|---|---|
| 10 types observed/templated | 9 approved (7 templated + index, log), `platform` proposed |
| 18 controlled fields (15 template, 3 SCHEMA.md) | 79 approved vocabulary terms |
| 5 conflicts: `feature.priority`, `gap.status`, `integration.frequency`, `question.priority`, `question.status` | template wins; recorded for the interview |
| outside values: feature `status: draft` (19), `category` custom-requests/inventory, `priority: P0`; entity `category: process`, `status: legacy` | 6 proposed vocabulary terms |
| `client`: `boston-beer-company` (40), `Boston Beer Company` (10), `shared` (2) | `client.boston-beer-company` approved with a proposed alias; `client.shared` approved (SCHEMA.md) |
| 140 distinct tags | 140 proposed tags (warn) |
| `gap.related-feature` holds links | `rel.related-feature` proposed, range feature |
| classified observed values | 51 approved · 147 proposed · 1 noncanonical · **0 unknown** |
| open violations | 698 — strict 445 (288 broken links, 130 noncanonical links, 10 relation-broken, 10 client variants, 7 ambiguous links), warn 253 — none block (ratchet) |
| `apply --dry-run` | 140 mechanical rewrites in 31 files |
