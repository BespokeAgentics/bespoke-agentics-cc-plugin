# Wiki integration

How the wiki subagent mines a vault, and how to satisfy a host repository's wiki-first mandate. Used in Phase 1 (the wiki agent reads this), Phase 2 (synthesis), and Phase 4 (apply).

## Detecting a wiki

A "wiki" here is any structured project knowledge base. Look for, in order:
- A `wiki/` directory with `_index.md` and/or `_schema/SCHEMA.md` (the Bespoke Agentics / Obsidian vault convention).
- A `docs/` tree that functions as a wiki (many cross-linked `.md` pages, an index).
- A `CLAUDE.md` that names a wiki location or declares a wiki-first rule.

If none exist, skip wiki handling entirely — don't manufacture one.

## What the wiki agent extracts

The goal is to pull *durable project intelligence* into the always-loaded context layer, with links back to the authoritative pages (never copying whole pages — link, don't duplicate). Return:

- **Project intelligence** — what the system is, who it's for, current phase/status — anything that orients an agent and belongs in the root `CLAUDE.md`.
- **Technical decisions** — architecture choices, platform constraints, decisions with status (e.g. the 🟢 OOTB / 🔵 Config / 🟡 Custom Dev / 🔴 Gap / ⚪ TBD / 🟣 3rd Party color system if the vault uses it). Surface the *decision*, link to the page.
- **Terminology** — domain/client-specific terms an agent must use correctly.
- **Per-subsystem hints** — any page that maps to a specific package/service, so its `CLAUDE.md` can link to it.
- **Wiki-links** — the `[[page]]` references worth embedding so a human (and Obsidian) can navigate from the memory file to the source.

Keep it factual and attributed. For every claim, note the wiki page it came from so synthesis can link it.

## Surfacing wiki content in memory files

- **Root `CLAUDE.md`** — if the repo has a wiki-first mandate, the managed block restates it briefly and points to `wiki/_index.md` as the entry point: query the wiki before answering project questions; update it after content-producing work. Include the 2–4 most load-bearing project facts with `[[wiki-links]]`.
- **Subsystem `CLAUDE.md`** — link the specific wiki pages relevant to that subsystem under a short "See also" line, rather than restating their content.

Linking instead of copying keeps the wiki the single source of truth (raw sources stay immutable) while making it discoverable from the context layer.

## Satisfying the wiki-first mandate (Phase 4)

If the host repo mandates wiki-first behavior (declared in its `CLAUDE.md`), this skill is a content-producing operation and must leave a trail. The wiki itself is fair to update; raw sources (transcripts, exports, pipeline outputs) are never edited.

1. **Log it.** Append an entry to `wiki/_log.md` recording the operation: date, `progressive-disclosure` map/refresh, the root scanned, and counts of files created/updated.

   ```
   ## 2026-05-30 — progressive-disclosure (map)
   Generated layered CLAUDE.md/AGENTS.md context across <root>.
   Files: <n> created, <m> updated. Settings: deny rules + SessionStart hook added.
   See .claude/disclosure-plan.md for the full manifest.
   ```

2. **Document it (if the vault schema warrants).** If the vault has a place for tooling/infra pages, add or update a page describing the context-layer setup — what files exist, what each subsystem's conventions are — and cross-link it from `_index.md`. Conform to `wiki/_schema/SCHEMA.md`: valid frontmatter, ISO dates, kebab-case filename, at least one `related:` back-reference, no orphan pages or broken links.

3. **Don't fight the host's own commands.** If the repo provides wiki commands (e.g. `/wiki:ingest-document`, `/wiki:lint`), prefer recommending them for deep wiki work rather than hand-editing many pages. This skill's job is the code context layer; the wiki tooling owns the wiki.
