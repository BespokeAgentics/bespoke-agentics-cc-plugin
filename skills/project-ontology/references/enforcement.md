# Enforcement — rules, policy, the ratchet, hooks, CI, the database, lint

One function (`check_text` in `scripts/ontology.py`) decides what a violation is. The write hook, the
CLI, CI, project-db and wiki-lint all call it; none has its own copy of the rules.

## Rules

| Rule | Family | Fires when | Suggestion in the message |
|---|---|---|---|
| `type-unknown` | type | `type:` is not a registered type | approved types; `propose type.<name>` |
| `type-deprecated` | type | the type is deprecated | its replacement |
| `value-unknown` | vocab · entity · tag | a controlled value is not registered | approved values, closest first when similar; the exact `propose` command |
| `value-noncanonical` | vocab · entity · tag | alias, proposed alias, or spelling variant of a term | the canonical value; `apply` |
| `value-deprecated` | vocab · entity · tag | the term is deprecated | `replaced-by` value; `apply` |
| `value-proposed` | vocab · entity · tag | the term is registered but not approved | usable, a human approves — or, under `policy.proposed: strict`, blocked until approved |
| `link-broken` | link | `[[target]]` resolves to no page | closest page names (single-file checks) |
| `link-ambiguous` | link | several pages match | the qualified forms |
| `link-noncanonical` | link | resolves only by title, slug, inverted `[[type\|slug]]` label, or folder note | the canonical link; `apply` |
| `relation-broken` | relation | a relation field is not a `[[wikilink]]`, or its target is missing | how to write it |
| `relation-ambiguous` / `relation-noncanonical` | relation | as the link rules, inside a relation field | as above |
| `relation-range` | relation | the target page's type is outside the relation's `range` | the expected types |
| `id-duplicate` | id | two governed files derive the same page id (vault sweeps only) | rename one |

Structural types (`ids.ignore-types`: index, log, lint-report) get their `type` and links checked, not
their other fields. Links inside unbound frontmatter strings (`sources:` citations) are checked as links.

## Policy

Each violation's policy is the first match of `policy.overrides[<binding>]` → `overrides[<namespace>]`
→ `overrides[<family>]` → `policy.default`, where the binding is `gap.severity`, the namespace is the page
type for vocabularies (`gap`), the entity namespace for entities (`client`), and `tag` / `type` otherwise.
`value-proposed` is capped at `policy.proposed` (default `warn`) so proposing a term never blocks a page.

| Policy | Write hook | Banner / DB / lint / `check` |
|---|---|---|
| `strict` | blocks when the write **adds** it | listed; `check` exits 1; project-db gate `fail` exits 3 |
| `warn` | never blocks; PostToolUse context lists it | listed |
| `off` | not computed | not listed |

## The ratchet

The pre hook checks the file **before** and **after** the write and blocks only the difference:
violations keyed by `(rule, field, value)`, counted with multiplicity — adding a *second* copy of a
broken link the page already had is a new violation; editing a paragraph on a page that already has 30
problems is not. New files have an empty "before", so a new page must be clean of strict violations.
`check --changed-since <ref>` applies the same ratchet per file against the version at `<ref>`.

## Hooks

Installed into `.claude/settings.json` (merged; existing hooks kept):

```json
"PreToolUse":  [{"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ontology-guard.sh pre",  "timeout": 20}]},
                {"matcher": "Bash",                 "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ontology-guard.sh bash", "timeout": 10}]}],
"PostToolUse": [{"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ontology-guard.sh post", "timeout": 20}]}],
"SessionStart":[{"hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ontology-context.sh", "timeout": 30}]}]
```

`$CLAUDE_PROJECT_DIR` is quoted on purpose: unquoted, a project path containing a space makes the command
exit 127, which Claude Code treats as a non-blocking hook error — enforcement would silently stop.
Re-running `install` upgrades older unquoted entries in place.

Facts this relies on (Claude Code hook docs, verified 2026-09-17): PreToolUse exit code 2 blocks the
tool call and feeds stderr to Claude; `permissionDecision: "deny"` blocks in every permission mode and
`"ask"` shows the permission prompt; PreToolUse has no non-blocking context channel, so warnings go
through PostToolUse `hookSpecificOutput.additionalContext`; SessionStart stdout is added to context;
timeouts are seconds. Tool input field names differ across doc versions — the engine accepts
`file_path` or `path`, and `content` or `contents`.

### `pre` — Write / Edit / MultiEdit

1. Not a governed page and not `ontology.yaml` → exit 0.
2. Reconstruct the post-write text: `Write` content; `Edit` exact replacement (unique `old_string`, or
   `replace_all`); `MultiEdit` edits in sequence; `Edit` with an empty `old_string` on a missing file
   creates it. If the tool itself would fail (string not found, not unique), exit 0 and let the tool
   report its own error.
3. The ontology cannot be loaded (parse error) → **block** with the error: pages cannot be checked
   against a broken ontology (fail-closed). An engine crash inside the hook also blocks, with the error
   — never silently disables enforcement.
4. Check before and after; block (exit 2) with every new strict violation, its suggestion and fix; note
   how many pre-existing / non-blocking violations remain.

### `pre` on `ontology.yaml` itself

Blocked when the new text does not parse, adds validation errors, or — under `approval: human` (as the
file stood *before* the write) — makes a human-gate change: a term becomes approved or deprecated,
approved aliases are added, a non-proposed term is removed or re-spelled, a controlled field is removed,
or any policy value changes (including `approval` itself — flipping it to `agent` in the same write is
blocked). Adding or editing **proposed** terms is allowed.

### `post` — Write / Edit / MultiEdit

Non-blocking. For a governed page: `additionalContext` listing what still stands (pre-existing strict,
warn, proposed). For `ontology.yaml`: re-renders `ONTOLOGY.md`.

### `bash`

- `ontology.py approve …`, `deprecate …`, `init … --write` → `permissionDecision: "ask"`: the user
  confirms. (The skill confirms with `AskUserQuestion` first; that answer is the gate if a permission mode
  suppresses prompts.)
- A command that writes a governed page from the shell — `>`/`>>` redirection, `tee`, `sed -i` /
  `perl -i`, `cp`/`mv`/`install`/`rsync` destination — is blocked: use Write/Edit so the check runs, or
  `ontology.py apply` for mechanical rewrites. Reads (`cat`, `grep`, `sed -n`) pass.
- The guard script skips Python entirely unless the command mentions `ontology.py` or `.md`.

## Known limits (and what covers them)

| Gap | Covered by |
|---|---|
| Renaming or deleting a page breaks inbound links in other files | `check --all`, CI, project-db sync, the banner |
| Writes that are not Claude tool calls (humans in an editor, other tools, `python -c`) | the same vault-wide checks |
| A permission mode that auto-approves `"ask"` | the skill's `AskUserQuestion` confirmation; `approved-by` audit trail and `wiki/_log.md` |

## CI

```yaml
# .github/workflows/ontology.yml
on: pull_request
jobs:
  ontology:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - run: python3 .claude/ontology/ontology.py check --changed-since origin/${{ github.base_ref }}
```

Exit 1 only when the change introduced a strict violation. After a migration has cleared the vault,
`check --all` can replace it to hold the whole vault at zero.

## project-db

On every `db.py sync` (when `.claude/ontology/ontology.py` exists) project-db imports the engine and
calls `load_for_db(root)` — terms, aliases, bindings, page ids and violations — into:

| Table | Holds |
|---|---|
| `ontology_terms` | `id, kind, namespace, parent, value, label, definition, status, replaced_by, since, approved_by, approved_on, source, domain, range` |
| `ontology_aliases` | `alias, term_id, status` |
| `ontology_fields` | `binding, type, field, kind, namespace, relation` |
| `ontology_violations` | `page_id, path, line, rule, policy, family, field, value, message, suggestion, nearest` |
| `pages.ontology_id` | the derived page id (also on every typed view) |

Typed-view column docs name the binding and its approved values (`severity: → gap.severity:
critical|high|medium|low`), SCHEMA.md gets an Ontology section, the banner a line, `verify` two checks,
and `db.py search` expands aliases (searching `Acme Corp` also finds pages that wrote `acme-corp`).
`config.json` → `"ontology": {"gate": "warn" | "fail" | "off"}`: with `fail`, `db.py sync` exits 3 while
strict violations stand (the SessionStart banner sync never fails). A broken or incompatible vendored
engine is reported in the banner and SCHEMA.md; the sync itself still succeeds.

```sql
SELECT rule, policy, COUNT(*) FROM ontology_violations GROUP BY 1, 2 ORDER BY 3 DESC;
SELECT value, status FROM ontology_terms WHERE parent = 'gap.severity' ORDER BY rowid;
SELECT p.path, v.field, v.value, v.suggestion FROM ontology_violations v JOIN pages p ON p.id = v.page_id WHERE v.rule = 'value-noncanonical';
```

## wiki-lint

Check 8 runs `python3 .claude/ontology/ontology.py check --all --format lint` and folds the records into
the lint report (strict → HIGH, a strict broken link → CRITICAL, warn → LOW). Check 6 reads allowed
values from the ontology (else from template comments) instead of hard-coded lists.
