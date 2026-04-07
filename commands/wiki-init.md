---
name: "wiki:init"
description: "Initialize a Karpathy-style LLM wiki vault — scans the repo, interviews the user, and creates an Obsidian vault tailored to the project."
argument-hint: "[--wiki-dir <path>]"
allowed-tools: Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Wiki Init

You are the Wiki Init Orchestrator. You create a brand-new Karpathy-style LLM wiki vault tailored to the current project.

## Arguments

Parse from `$ARGUMENTS`:

```
[--wiki-dir '<path>']
```

- `--wiki-dir` (optional): Path to create the wiki (default: `./wiki`)

If `$ARGUMENTS` is empty, use all defaults.

Usage:
```
/wiki:init
/wiki:init --wiki-dir './knowledge-base'
```

## Derived Variables

```
WIKI_DIR            = --wiki-dir value, or value from interview prompt, or ./wiki
TODAY               = !`date +%Y-%m-%d`
```

## Process

### Phase 1: Repo Discovery

Before asking the user anything, silently scan the repository:

1. `ls` the project root — understand the folder structure
2. Read any `CLAUDE.md`, `README.md`, `INDEX.md` at root or one level deep
3. Check `.claude/` for existing skills, commands, agents
4. Look for content types: documents, transcripts, code, data
5. Check for `package.json`, `pyproject.toml`, etc. to identify tech stack
6. Check if a wiki or Obsidian vault already exists

Build a mental model of what this project is about — domains, platforms, content types, stakeholders. Do NOT make assumptions about anything not evidenced in the repo.

### Phase 2: Interview the User

Using AskUserQuestion, ask 6 targeted questions based on what you discovered:

0. **Wiki Directory** — If `--wiki-dir` was NOT provided in `$ARGUMENTS`, ask:
   ```
   Where should the wiki vault be created?
   ```
   Present the default `./wiki` as the pre-selected option. Offer alternatives based on the repo structure (e.g., `./docs/wiki`, `./knowledge-base`). Include "Other: {let me specify}".
   Assign the user's answer to `WIKI_DIR`. If `--wiki-dir` was provided via arguments, skip this question and use that value.

1. **Project Context** — Present findings, ask user to confirm or correct
2. **Wiki Scope** — What should the wiki track? (adapt options to repo)
3. **Organizational Structure** — How to organize top-level? (by client, project, team, domain)
4. **Platforms/Technologies** — Which deserve shared knowledge pages? (only list what's in the repo)
5. **Organization Name** — What to call the internal/team section? (derive from repo, or skip)

The wiki-init skill contains full interview question templates for Questions 1-5. The skill is invoked in Phase 4 — you only need to collect the answers here.

### Phase 3: Pre-flight Validation

1. **Check vault does NOT exist**: If `{WIKI_DIR}` already exists, abort:
   "Wiki already exists at {WIKI_DIR}. Use /wiki:new-client to add a client, or delete the directory to start fresh."

2. **Check parent directory exists**: Ensure writable.

Report pre-flight status using interview answers:
```
=== Wiki Init ===
Wiki directory:    {WIKI_DIR}
Project:           {description from interview}
Wiki scope:        {selected items}
Organization:      {structure chosen}
Platform stubs:    {confirmed platforms, or "none"}
Team section:      {org name, or "skipped"}
Status:            ✓ Ready to initialize
```

### Phase 4: Invoke wiki-init Skill

Launch the skill:

```
Skill: wiki-init
Parameters:
  wiki_dir: {WIKI_DIR}
  today: {TODAY}
  project_description: {description from Question 1}
  wiki_scope: {selected items from Question 2}
  org_structure: {structure from Question 3}
  platforms: {confirmed platforms from Question 4, or "none"}
  org_name: {org name from Question 5, or "skipped"}
```

The skill handles:

- Creating the vault directory structure (adapted to org model)
- Writing all 5 `.obsidian/` config files (graph colors match actual folders)
- Writing `_schema/SCHEMA.md` tailored to this project
- Creating all 7 page templates in `_schema/templates/`
- Creating `_index.md` and `_log.md`
- Creating platform stub pages (only those confirmed by user)
- Creating org process stubs (only if not skipped)

Wait for skill completion.

### Phase 5: Update Project CLAUDE.md

After the wiki vault is created, ensure the project's `CLAUDE.md` includes instructions for agents to use the wiki as the primary knowledge layer.

1. **Check if `CLAUDE.md` exists** at the project root.
   - If it does not exist, create it.

2. **Check if wiki instructions already exist** by searching for the string `wiki` (case-insensitive) in the file. Look for existing wiki-related sections such as "Wiki-First Mandate", "Wiki Usage", or references to `/wiki:query`.
   - If wiki instructions already exist, skip this phase and report: `CLAUDE.md: Already configured — no changes made.`

3. **Append the wiki-first mandate block** to the end of `CLAUDE.md`:

   ````markdown

   ## Wiki Knowledge System

   This project uses a Karpathy-style LLM wiki at `{WIKI_DIR}/` as the single source of truth for project intelligence, technical decisions, and business capabilities.

   ### Core Rules

   1. **Query the wiki before answering project questions.** Run `/wiki:query '<question>'` or read wiki pages directly before relying on general knowledge.
   2. **Update the wiki after content-producing operations.** When meetings are analyzed, documents ingested, or decisions made, route results into the wiki via `/wiki:ingest-meeting` or `/wiki:ingest-document`.
   3. **Never modify raw sources.** Raw pipeline outputs and transcripts are immutable. The wiki references them but never edits them.
   4. **Maintain cross-references.** Every wiki page links to related pages via `[[wiki-links]]` and `related:` frontmatter.

   ### Quick Reference

   | Task | Command |
   |------|---------|
   | Search wiki knowledge | `/wiki:query '<question>'` |
   | Ingest a meeting | `/wiki:ingest-meeting '<name>' '<dir>' '<label>'` |
   | Ingest a document | `/wiki:ingest-document '<name>' '<path>' '<type>'` |
   | Check wiki health | `/wiki:lint --scope full` |
   | View wiki status | `/wiki:status` |
   ````

4. **Report the result**:
   - If created: `CLAUDE.md: Created with wiki-first mandate.`
   - If appended: `CLAUDE.md: Updated with wiki-first mandate.`
   - If already configured: `CLAUDE.md: Already configured — no changes made.`

### Phase 6: Report Summary

After skill completes, print a summary tailored to what was actually created:

```
================================================================
  Wiki Initialized Successfully
================================================================

Vault:            {WIKI_DIR}
Project:          {description}
Obsidian:         .obsidian/ (5 config files)
Schema:           _schema/SCHEMA.md + 7 templates
Global files:     _index.md, _log.md
Structure:        {actual folders created}
Platform stubs:   {list, or "none"}
Process stubs:    {list, or "none"}

CLAUDE.md:        {Created with wiki-first mandate / Updated with wiki-first mandate / Already configured}

Total files created: {count}

Next Steps:
  1. Open the vault in Obsidian
  2. Add your first {client/project/entry}:
     /wiki:new-client '<name>' '<platform>'
  3. Ingest content:
     /wiki:ingest-meeting '<name>' '<dir>' '<label>'
     /wiki:ingest-document '<name>' '<path>' '<type>'
  4. Check health:
     /wiki:lint --scope full
================================================================
```

## Error Handling

- If wiki directory already exists, abort with clear message
- If parent directory doesn't exist, attempt to create it
- If skill fails, log error but report what was created
- If interview is interrupted, use reasonable defaults from repo discovery

## Success Criteria

- Repo was scanned before any questions were asked
- User was prompted for wiki directory name (unless `--wiki-dir` was provided)
- User was interviewed with project-specific questions
- No hardcoded platform or company names in the output
- Skill received structured parameters (not prose context)
- All `.obsidian/` config files present and valid JSON
- `_schema/SCHEMA.md` reflects this specific project
- All 7 templates created
- `_index.md` and `_log.md` initialized
- Only user-confirmed platform stubs created
- Project `CLAUDE.md` checked and updated with wiki-first mandate if needed
- Summary printed with actual file counts, CLAUDE.md status, and next steps
