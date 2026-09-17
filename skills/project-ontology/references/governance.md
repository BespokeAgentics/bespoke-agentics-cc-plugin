# Governance — lifecycle, gates, deprecation, rewrites

## Lifecycle

```
            propose (any agent, needs a definition)
   (none) ───────────────────────────────────────▶ proposed ──approve (human)──▶ approved
                                                      │                             │
                                                      └──deprecate (human)──▶ deprecated ◀──┘
                                                                                  │
                                                                     replaced-by ─┘ → apply rewrites pages
```

| Status | On a page | In the vocabulary |
|---|---|---|
| proposed | usable; flagged `value-proposed` (warn) until approved | listed as proposed in ONTOLOGY.md, `ontology_terms` |
| approved | fine | the legal values |
| deprecated | `value-deprecated` — blocked when newly written (strict) | listed with its replacement |

A rejected proposal is a **deprecation** — with `--replaced-by` when there is a right value to use
instead — so pages that already used it are flagged and `apply` can rewrite them. Terms are never deleted
by the engine; history stays in the file and in `wiki/_log.md`.

## Who may do what

| Action | Agent | Human | Enforced by |
|---|---|---|---|
| `propose` a term or an alias | ✓ | ✓ | — |
| edit a *proposed* term in `ontology.yaml` | ✓ | ✓ | write guard allows it |
| `approve` (term or its proposed aliases) | only when the user said so | ✓ | `AskUserQuestion` · Bash `ask` · write guard · `--by` required |
| `deprecate` | only when the user said so | ✓ | same |
| remove / re-spell a non-proposed term, change policy | ✗ | ✓ (edit the file) | write guard |
| `apply` rewrites | after the user confirms the dry run | ✓ | skill procedure · `wiki/_log.md` |
| `init --write` (declares approved terms) | after the interview | ✓ | Bash `ask` · decisions recorded with `--by` |

"Human" means a person, identified by name in `--by`. Hooks only see Claude's tool calls, so a human
editing `ontology.yaml` in their editor is never blocked — that is how a person changes policy.

## The approval procedure (what the agent does)

1. Show what is pending: `python3 .claude/ontology/ontology.py status` (pending ids) and
   `ls --status proposed`, grouped by parent, with page counts from `check --all --format json` or
   `SELECT value, COUNT(*) FROM ontology_violations WHERE rule = 'value-proposed' GROUP BY value`.
2. Ask with `AskUserQuestion`: one question per group (≤4 per call), each option carrying the definition
   and where the value is used. Options: approve · deprecate in favour of an approved value · leave
   proposed.
3. Run exactly what was chosen: `approve <id>… --by "<name>"` / `deprecate <id> --replaced-by <id>
   --reason "…" --by "<name>"`. Accept the permission prompt the Bash guard raises only if it matches.
4. If anything was deprecated with a replacement: `apply --dry-run`, show it, `apply` on a yes, then
   `/db:sync` when project-db is installed.
5. Report: terms moved, who approved, pages affected, violations remaining.

## Placing a value in a ranked vocabulary

Vocabulary order is ranking — ONTOLOGY.md, template comments and project-db column docs all list values
in file order. `propose gap.severity.urgent --before gap.severity.critical …` puts the new value where it
ranks; without `--before`/`--after` it goes after its last sibling. (Both eval agents that added `urgent`
had to hand-move it above `critical` before this option existed.)

## Globs

`approve 'tag.*' --by …` approves every matching term (useful after an interview decides all observed
tags are fine). Ids are matched with shell-style globs against the full id.

## Aliases

- `propose <id> --alias "Acme Corp"` adds a proposed alias to an existing term.
- `approve <id> --aliases-only --by …` approves a term's proposed aliases without touching its status.
- `init` records spelling variants it observes (e.g. `Boston Beer Company` for `boston-beer-company`) as
  proposed aliases, so search and `apply` know the mapping before anyone approves it.
- An alias is a spelling the vault tolerates while it migrates, and a search expansion. It is not a
  second legal value: writing an alias is `value-noncanonical`, and new writes are blocked under strict.

## `apply` — the only automated page edits

Rewrites exactly what has one right answer:

| Case | Before | After |
|---|---|---|
| approved alias / proposed alias / spelling variant | `client: Boston Beer Company` | `client: boston-beer-company` |
| deprecated value with a replacement | `severity: low` | `severity: medium` |
| title link | `[[Budget Management]]` | `[[budget-management\|Budget Management]]` |
| inverted label link | `[[gap\|co-op-billing]]` | `[[clients/acme/gaps/co-op-billing\|co-op-billing]]` |
| folder-note link | `[[merchtank]]` | `[[platforms/merchtank/overview\|merchtank]]` |

Values inside inline lists and block lists are rewritten in place; the original quoting style is kept.
Nothing else in the file changes (tests pin byte preservation). Unknown values, ambiguous links, broken
links and relation-range problems are judgment calls: they stay violations for a person.

Always `apply --dry-run` first, show the summary (and a sample of lines), and apply only after a yes.
The engine logs the run to `wiki/_log.md` with the remaining violation count.

## Log entries

Every governance change appends to `wiki/_log.md` (no wiki: `.claude/ontology/LOG.md`):
`## YYYY-MM-DD — ontology proposal — gap.severity.urgent`, `… — ontology approval — N term(s)`,
`… — ontology deprecation — <id>`, `… — ontology apply — canonical values`, `… — project-ontology init …`.
project-db loads the log into `log_entries`, so `SELECT * FROM log_entries WHERE title LIKE '%ontology%'`
is the governance history.
