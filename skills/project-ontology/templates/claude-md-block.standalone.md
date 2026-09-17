## Project Ontology (project-ontology) — the controlled vocabulary of this project's documents

Every controlled frontmatter value, tag and wikilink target in {{ROOTS}} is governed by `{{ONTOLOGY_FILE}}`: dot-notated terms (`adr.status.accepted`, `team.payments`, `tag.billing`, `rel.supersedes`) with a lifecycle — **proposed → approved → deprecated**. Documents keep plain values (`status: accepted`); the ontology decides which plain values are legal. Read `{{DOC_FILE}}` before writing frontmatter or links.

### Rules

1. **Write registered values only.** Copy the spelling from `{{DOC_FILE}}` exactly. Aliases and spelling variants are flagged; deprecated values name their replacement.
2. **A new concept is registered before it is used.** Run `{{ENGINE}} propose <id> --label … --definition …`. A proposed term is usable at once and stays flagged until a human approves it. Never invent a near-synonym of an existing value to avoid proposing.
3. **Approval and deprecation are human gates.** Do not edit a term's `status` to approved or deprecated yourself; ask the user, then run `/ontology:approve` or `/ontology:deprecate` with their name as `--by`.
4. **Links resolve to exactly one document:** `[[slug]]`, or the document's full path inside its root when two documents share a slug (`[[adr/0004-stripe-sync-job]]`).
5. **The write hook is the contract.** A Write/Edit that adds a strict violation is blocked with the approved values and the propose command in the message. Fix the value; do not route around the hook with Bash writes (those are blocked too). Violations that predate your edit do not block (ratchet) and are not yours to fix as a side effect of another task: mechanical ones go through `/ontology:apply` after the user confirms the dry run; the rest need a human's decision — list them for the user instead.
6. **Everything reads the same rules:** project-db's `ontology_violations`, `{{ENGINE}} check --all`, and `{{ENGINE}} check --changed-since <ref>` in CI.

### Commands

| Situation | Command |
|---|---|
| Which values are legal for a field | `{{DOC_FILE}}` or `{{ENGINE}} ls --prefix adr.status.` |
| Check a document / everything | `/ontology:check <path>` · `/ontology:check --all` |
| A value you need is not registered | `/ontology:propose <id> --label … --definition …` |
| Approve proposed terms (the user decides) | `/ontology:approve <id>…` |
| Retire a term, naming its replacement | `/ontology:deprecate <id> --replaced-by <id>` |
| Rewrite aliases, deprecated values, noncanonical links | `/ontology:apply --dry-run`, confirm, then `/ontology:apply` |
| Counts, open violations, pending approvals | `/ontology:status` |
