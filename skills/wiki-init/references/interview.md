# Repo discovery + interview

## Step 0 — Repo discovery (silent)

Before asking anything, silently scan the current repo. Goal: ground the interview in evidence, not assumptions.

1. `ls` the top-level directory and one level deep.
2. Read any `CLAUDE.md`, `README.md`, or `INDEX.md` at root or one level deep — these describe the project.
3. Inspect `.claude/` (skills, commands, agents already present).
4. Inspect documents, transcripts, recordings, code, and data files — they reveal what the project deals with.
5. Read `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc. — they reveal the tech stack.
6. Note any existing Obsidian vaults or markdown collections to avoid duplicating them.

Build a mental model of:
- What this project **does** (product, service, consulting engagement, internal tool, etc.)
- What **domains** it covers (ecommerce, healthcare, fintech, devtools, etc.)
- What **platforms / technologies** are involved (only those actually referenced)
- What **content types** exist (meetings, documents, code, data, …)
- Who the **stakeholders** are (clients, internal teams, OSS community, …)

## Step 1 — Interview (`AskUserQuestion`)

Present discovery findings and confirm/correct via the five core questions below. Adapt option lists to what discovery revealed; never offer platforms or org names that aren't grounded in evidence.

### Q1 — Project context confirmation

```
Based on scanning this repo, here's what I found:
- [summary of what you discovered]

Is this accurate? Anything to add or correct about what this project is?
```

Options: include what you found plus `Other / Let me explain`.

### Q2 — Wiki scope (multi-select)

```
What should this wiki track? (select all that apply)
```

Options (adapt to repo):
- Client/customer engagements and intelligence
- Technical architecture and decisions
- Meeting notes and action items
- Product features and roadmap
- Research and analysis findings
- Process documentation and runbooks
- Integration and API documentation
- Other: {let me specify}

### Q3 — Organizational structure

```
How should the wiki be organized at the top level?
```

Options:
- By client/customer (multi-client engagement model)
- By project/product (single product with multiple workstreams)
- By team/department (internal knowledge base)
- By domain/topic (research or reference wiki)
- Custom: {let me describe}

### Q4 — Platforms and technologies (multi-select)

```
Which platforms or technologies should have shared knowledge pages?
(Only create stubs for things actually relevant to this project)
```

Options: derived from repo discovery — list only platforms/technologies you actually found. Always include `None — I'll add these later` and `Other: {specify}`.

### Q5 — Organization name

```
What name should be used for the internal/team knowledge section?
(This becomes the top-level folder for your team's processes, playbooks, and methodology)
```

Options: derive from repo (org name in `package.json`, git remote, folder names). Always include `Skip — don't create an internal section` and `Other: {specify}`.

## Step 2 — Pre-flight validation

1. Resolve `WIKI_DIR` (default `./wiki`).
2. If `{WIKI_DIR}` already exists: STOP and report

```
✗ Wiki already exists at {WIKI_DIR}
  Use /wiki:new-client to add a client, or delete the directory first.
```

3. Print a pre-flight summary incorporating the interview answers:

```
=== Wiki Init ===
Wiki directory:    {WIKI_DIR}
Project:           {project description}
Wiki scope:        {selected scope items}
Organization:      {top-level org structure}
Platform stubs:    {platforms to create, or "none"}
Team section:      {org name, or "skipped"}
Status:            ✓ Ready to initialize
```
