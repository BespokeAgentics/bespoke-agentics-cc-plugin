# Term model — ids, kinds, the declaration file, bindings, page ids

## The id grammar

```
<segment>(.<segment>)*        segment = [a-z0-9][a-z0-9-]*
```

Dots separate levels; hyphens join words. Ids are lowercase so they sort, prefix-match and survive SQL
`LIKE 'gap.%'`. The **exact spelling a page uses** lives in the term's `value` when it is not the id's
last segment (`P1`, `🟡`, `Boston Beer Company`).

## Five kinds, one section each

| Section in `ontology.yaml` | Kind | Id shape | Example id | Value on a page |
|---|---|---|---|---|
| `types` | type | `type.<name>` | `type.gap` | `type: gap` |
| `vocabularies` | vocab | `<type>.<field>.<leaf>` | `gap.severity.critical`, `feature.priority.p1` (`value: P1`) | `severity: critical`, `priority: P1` |
| `entities` | entity | `<namespace>.<slug>` | `client.boston-beer-company`, `client.shared` | `client: boston-beer-company` |
| `relations` | relation | `rel.<name>` | `rel.related-feature` (`domain: [gap]`, `range: [feature]`) | `related-feature: "[[order-management]]"` |
| `tags` | tag | `tag.<path>` | `tag.budget-management`, `tag.gap.critical` (`gap/critical`) | `tags: [budget-management]` |

A vocabulary id's first segment must be a declared type — the type is the namespace of its fields.
Relation terms have no page value; they constrain the pages a link field may point at. Emoji values get
readable leaves: 🟢 `ootb`, 🔵 `config`, 🟡 `custom-dev`, 🔴 `gap`, ⚪ `tbd`, 🟣 `third-party`.

## Term attributes

| Attribute | Meaning |
|---|---|
| `label` | human name |
| `value` | exact page spelling when it differs from the leaf |
| `definition` | what the term means — required to propose; what a reviewer approves |
| `status` | `proposed` · `approved` · `deprecated` |
| `aliases` | approved alternative spellings (flagged `value-noncanonical`, rewritten by `apply`) |
| `proposed-aliases` | alternative spellings awaiting approval (approved together with the term) |
| `domain`, `range` | relations only: page types that may carry the field / be linked |
| `replaced-by` | deprecated terms: the term to use instead (same kind, same parent) |
| `reason` | why it was deprecated |
| `since`, `source` | when and from where it entered (template, SCHEMA.md, folder, observed on N pages, a page that needed it) |
| `proposed-by`, `approved-by`, `approved-on`, `deprecated-by`, `deprecated-on` | the audit trail |

## The file

`wiki/_schema/ontology.yaml` (projects without a wiki: `.claude/ontology/ontology.yaml`). A strict YAML
subset — block mappings, scalars, single- or double-quoted strings, `[inline, lists]`, block lists — so
the stdlib engine parses it identically everywhere. Anything else (flow mappings `{}`, anchors, block
scalars `|`, tabs, duplicate keys) is an error **with a line number**, never a silent misread.

```yaml
version: 1
name: acme-wiki
updated: 2026-09-17
policy:
  default: strict          # strict | warn | off
  proposed: warn           # cap for value-proposed (default warn: proposing never blocks)
  approval: human          # human | agent
  overrides:
    tag: warn              # keys: a binding (gap.severity), a namespace (gap, client, tag), or a family (link, relation)
ids:
  scope-folders:
    clients: client        # clients/<slug>/… pages get ids client.<slug>.<type>.<file>
    platforms: platform
  folder-notes: [overview, readme, index]
  ignore-types: [index, log, lint-report]   # structural pages: links checked, fields not

fields:
  '*.type':
    kind: type
  '*.client':
    kind: entity
    namespace: client
  '*.tags':
    kind: tag
  gap.severity:
    kind: vocab
  gap.related-feature:
    kind: relation
    relation: rel.related-feature

types:
  type.gap:
    label: Gap
    definition: A difference between the legacy platform and the target, with evidence.
    status: approved
vocabularies:
  gap.severity.critical:
    label: critical
    status: approved
  feature.priority.p1:
    label: P1
    value: P1
    status: approved
entities:
  client.boston-beer-company:
    label: Boston Beer Company
    status: approved
    aliases: [Boston Beer Company]
relations:
  rel.related-feature:
    label: Related feature
    domain: [gap]
    range: [feature]
    status: approved
tags:
  tag.budget-management:
    status: proposed
```

The engine rewrites the file deterministically on every governance change: **comments are not
preserved** — rationale belongs in `definition` and `reason`. Term order inside a section is kept (a
vocabulary's order is meaningful: `critical|high|medium|low`), and a newly proposed term is inserted
after its siblings — or exactly where `propose --before <id>` / `--after <id>` places it.

## Bindings — which fields are controlled

Only fields listed under `fields:` are controlled; everything else is free text (owners, dates, paths).
A binding key is `<type>.<field>` or `*.<field>`; field names are compared after slugifying
(`decision_category` ≡ `decision-category`). The most specific binding wins (`gap.status` before
`*.status`). A wildcard vocabulary binding means "each type has its own vocabulary": `*.status` on a gap
page looks for `gap.status.*` terms. `init` writes explicit per-type bindings so the file says exactly
what is controlled.

| Kind | What a value must be |
|---|---|
| type | a `types` term |
| vocab | a `vocabularies` term under `<page type>.<field>` |
| entity | an `entities` term under the binding's `namespace` |
| tag | a `tags` term (a tag written `a/b` is `tag.a.b`) |
| relation | a `[[wikilink]]` that resolves to exactly one page whose `type` is in the relation's `range` |

## Matching a value

1. **Canonical** — equals a term's value. Approved: fine. Proposed: `value-proposed` (warn). Deprecated:
   `value-deprecated`.
2. **Alias** — equals an approved alias → `value-noncanonical` (rewrite with `apply`).
3. **Proposed alias** — equals a proposed alias → `value-noncanonical` ("awaiting approval").
4. **Spelling variant** — same slug or same case-folded text as exactly one term's value or alias
   (`Boston Beer Company` ≡ `boston-beer-company`, `p1` ≡ `P1`) → `value-noncanonical`.
5. Otherwise **unknown** → `value-unknown` / `type-unknown`, with the approved values listed and the
   closest ones named.

Empty values are not checked (required-ness is `wiki-lint`'s job). Tags written as one comma-separated
string (`tags: a, b`) are checked item by item, like project-db loads them.

## Page ids (derived, never stored)

| Path (inside the wiki) | `type` | Id |
|---|---|---|
| `clients/boston-beer-company/gaps/co-op-billing.md` | gap | `client.boston-beer-company.gap.co-op-billing` |
| `clients/boston-beer-company/features/co-op-billing.md` | feature | `client.boston-beer-company.feature.co-op-billing` |
| `clients/boston-beer-company/README.md` | — | `client.boston-beer-company` (folder note) |
| `platforms/merchtank/overview.md` | platform | `platform.merchtank` (folder note) |
| `verndale/processes/wiki-maintenance.md` | entity | `entity.wiki-maintenance` |
| `notes/scratch.md` | — | `page.scratch` |

Scope folders come from `ids.scope-folders`; folder notes from `ids.folder-notes`. Two governed files that
derive the same id raise `id-duplicate`. project-db stores the id in `pages.ontology_id` (and every typed
view), so `WHERE ontology_id LIKE 'client.acme.%'` selects a client's subtree.

## Canonical link forms

A link must resolve to exactly one page the way Obsidian does: by file name (`[[co-op-billing]]`), or by
path inside the vault when two files share a name (`[[clients/acme/gaps/co-op-billing]]`). Page
templates (`_schema/templates/*`) are never link targets. The engine suggests, and `apply` writes, the
full vault path for ambiguous names — the one form every resolver (Obsidian, project-db, this engine)
agrees on — and keeps the text the reader saw: `[[gap|co-op-billing]]` becomes
`[[clients/acme/gaps/co-op-billing|co-op-billing]]`.

| Written | Resolves by | Result |
|---|---|---|
| `[[co-op-billing]]` (one file) | name | ok |
| `[[co-op-billing]]` (feature + gap) | name | `link-ambiguous` — qualify it |
| `[[Budget Management]]` | page title | `link-noncanonical` → `[[budget-management\|Budget Management]]` |
| `[[gap\|budget-engine]]` | the label, because `gap` is a type word (inverted form) | `link-noncanonical` |
| `[[merchtank]]` (a folder with `overview.md`) | folder note | `link-noncanonical` → `[[platforms/merchtank/overview\|merchtank]]` |
| `[[nowhere]]` | — | `link-broken` (closest page names suggested on single-file checks) |

Links inside HTML comments, fenced code and inline code are not links (the same rule project-db applies).

## Parser determinism

Page frontmatter is read with the same subset parser as project-db (`test_ontology.py` pins the parity);
neither engine ever uses PyYAML. With PyYAML, `related: [[Page]]` parses as a nested list and the link
vanishes — the same vault would check differently on two machines.
