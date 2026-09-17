## Project Ontology (project-ontology) — the controlled vocabulary of this wiki

Every controlled frontmatter value, tag and wikilink target under {{ROOTS}} is governed by `{{ONTOLOGY_FILE}}`: dot-notated terms (`gap.severity.critical`, `client.acme-corp`, `tag.budget-management`, `rel.related-feature`) with a lifecycle — **proposed → approved → deprecated**. Pages keep plain values (`severity: critical`); the ontology decides which plain values are legal. Read `{{DOC_FILE}}` before writing frontmatter or links.

### Rules

1. **Write registered values only.** Copy the spelling from `{{DOC_FILE}}` exactly (`P1`, not `p1`; `acme-corp`, not `Acme Corp`). Aliases and spelling variants are flagged; deprecated values name their replacement.
2. **A new concept is registered before it is used.** Run `{{ENGINE}} propose <id> --label … --definition …` (vocabulary `<type>.<field>.<value>`, entity `<namespace>.<slug>`, tag `tag.<path>`). A proposed term is usable at once and stays flagged until a human approves it. Never invent a near-synonym of an existing value to avoid proposing.
3. **Approval and deprecation are human gates.** Do not edit a term's `status` to approved or deprecated yourself; ask the user, then run `/ontology:approve` or `/ontology:deprecate` with their name as `--by`.
4. **Links resolve to exactly one page:** `[[slug]]`, or the page's full path inside the vault when two pages share a slug (`[[clients/acme/gaps/co-op-billing]]` — the form Obsidian, project-db and the hook all agree on). `[[type|slug]]` and title-only links are noncanonical.
5. **The write hook is the contract.** A Write/Edit that adds a strict violation is blocked, and the message names the approved values and the propose command. Fix the value; do not route around the hook with Bash writes (those are blocked too). Violations already on a page before your edit do not block (ratchet) and are not yours to fix as a side effect of another task: mechanical ones (aliases, spelling variants, noncanonical links) go through `/ontology:apply` after the user confirms the dry run; the rest need a human's decision — list them for the user instead.
6. **The database, lint and CI read the same rules.** `ontology_violations` in project-db, Check 8 in `/wiki:lint`, and `{{ENGINE}} check --changed-since <ref>` in CI all run this engine.

### Commands

| Situation | Command |
|---|---|
| Which values are legal for a field | `{{DOC_FILE}}` or `{{ENGINE}} ls --prefix gap.severity.` |
| Check a page / the whole vault | `/ontology:check <path>` · `/ontology:check --all` |
| A value you need is not registered | `/ontology:propose <id> --label … --definition …` |
| Approve proposed terms (the user decides) | `/ontology:approve <id>…` |
| Retire a term, naming its replacement | `/ontology:deprecate <id> --replaced-by <id>` |
| Rewrite aliases, deprecated values, noncanonical links | `/ontology:apply --dry-run`, confirm, then `/ontology:apply` |
| Counts, open violations, pending approvals | `/ontology:status` |
