---
name: "wiki:init"
description: "Initialize a brand-new Karpathy-style LLM wiki vault. Scans the repo, interviews the user, then creates an Obsidian vault tailored to the project."
argument-hint: "[--wiki-dir '<path>']"
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
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
WIKI_DIR            = --wiki-dir value or ./wiki
TODAY               = current date (YYYY-MM-DD)
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

Using AskUserQuestion, ask 5 targeted questions based on what you discovered:

1. **Project Context** — Present findings, ask user to confirm or correct
2. **Wiki Scope** — What should the wiki track? (adapt options to repo)
3. **Organizational Structure** — How to organize top-level? (by client, project, team, domain)
4. **Platforms/Technologies** — Which deserve shared knowledge pages? (only list what's in the repo)
5. **Organization Name** — What to call the internal/team section? (derive from repo, or skip)

See the wiki-init skill (`skills/wiki-init/SKILL.md`) for the full interview question templates.

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

Launch the skill with the interview answers as context. The skill handles:

- Creating the vault directory structure (adapted to org model)
- Writing all 5 `.obsidian/` config files (graph colors match actual folders)
- Writing `_schema/SCHEMA.md` tailored to this project
- Creating all 7 page templates in `_schema/templates/`
- Creating `_index.md` and `_log.md`
- Creating platform stub pages (only those confirmed by user)
- Creating org process stubs (only if not skipped)

Wait for skill completion.

### Phase 5: Report Summary

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
- User was interviewed with project-specific questions
- No hardcoded platform or company names in the output
- All `.obsidian/` config files present and valid JSON
- `_schema/SCHEMA.md` reflects this specific project
- All 7 templates created
- `_index.md` and `_log.md` initialized
- Only user-confirmed platform stubs created
- Summary printed with actual file counts and next steps
