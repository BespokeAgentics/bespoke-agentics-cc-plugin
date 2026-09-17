# bespoke-agentics

A Claude Code plugin with AI transparency auditing, agent architecture generation, Pi harness customization, UX evaluation, video-to-deliverables pipelines, workflow analysis, and a Karpathy-style LLM wiki knowledge system.

## Installation

Add this repository as a marketplace, then install the plugin:

```bash
# Add the marketplace
claude plugin install bespoke-agentics@https://github.com/BespokeAgentics/bespoke-agentics-cc-plugin

# Or test locally during development
claude --plugin-dir ./bespoke-agentics-plugin
```

## Skills

> Most primary skills are invoked directly by the Skill tool (or by Claude when it recognizes the trigger) — no slash command needed. Slash commands are kept only for skills that benefit from `argument-hint`-style invocation (the `wiki:*` and `ux-audit-*` families below).

### Primary Skills

| Skill | Description |
|-------|-------------|
| **ai-transparency** | Audit and fix AI operations lacking UI state coverage (loading, streaming, logs, errors). Enforces the "No Black Boxes" policy. |
| **architect-agents** | Analyze a project and generate a complete `.claude/agents/` and `.claude/commands/` architecture with documentation. |
| **ux-audit** | Comprehensive UX evaluation using Nielsen's 10 Heuristics and Norman's 6 Design Principles. See ux-audit-* variants below for narrower scopes. |
| **video-to-deliverables** | End-to-end video analysis pipeline. Transforms recordings into workflow docs, migration analysis, meeting summaries, or training guides. |
| **workflow-analyzer** | Client workflow analysis from video recordings. Produces application inventory, challenge mapping, and AI automation recommendations. |
| **setup-plugin** | Scaffold, optimize, and package a folder as a well-formed Claude Code plugin. Converts `.claude/` directories into distributable plugins. |
| **pi-assistant** | Understand the pi.dev coding agent, customize its harness, build Pi skills/extensions/packages, and search for or install Pi packages. |
| **spec-elicitation** | Interview-driven spec development that turns vague ideas into complete implementation specifications. Also available as `/bespoke-agentics:spec-elicitation`. |
| **biome-guardrails** | Install Biome.js + sidecar ESLint as strict AI-code guardrails in a JS/TS project — or audit an existing codebase for weak-typing debt (`--audit`) and install ratchet enforcement that blocks new `any` and oversized files without breaking the build (`--ratchet`). |
| **bun-workspace** | Convert sibling Node/Bun repos into a Bun workspace monorepo, audit one, or add a package. |
| **git-submodules** | Add/convert/init/audit Git submodules safely. |
| **session-hooks** | Design Claude Code SessionStart/SessionEnd/Stop hooks via interview. |
| **mcp-server-scaffold** | Scaffold a safe-by-default HTTPS MCP server in Bun or Go, add tools to one, or audit one. |
| **glean-agent-toolkit** | Scaffold/extend Glean Agent Toolkit (Python) projects across OpenAI SDK / LangChain / Google ADK. |
| **ai-waiting-ux** | Audit/scaffold real-time AI waiting UX in Next.js + claude-agent-sdk projects. |
| **codex-prompt-builder** | Convert session context, bug reports, or feature notes into a Codex prompt. |

## Spec Interviewer UI

The interactive web interface lives in `apps/spec-interviewer/`. It loads `skills/spec-elicitation/SKILL.md` as the source of truth, starts a Claude Agent SDK session, renders `AskUserQuestion` calls as structured form cards, and writes the final Markdown spec inside this repository.

```bash
cd apps/spec-interviewer
npm install
npm run dev
```

Open `http://127.0.0.1:4177`.

The Agent SDK can use your local Claude Code OAuth login automatically. `ANTHROPIC_API_KEY` is optional if you prefer key-based auth.

### Pi Assistant

All Pi tasks route through the `pi-assistant` skill. Describe the task in natural language ("build a Pi extension that…", "search Pi packages for browser automation", "review my local Pi setup", "install Pi package X globally") and the skill routes to the right surface — harness customization, extension/skill/package authoring, package search, install, or setup review. See `skills/pi-assistant/SKILL.md` and its `references/` for surface-by-surface guidance.

### UX Audit Variants

| Command | Description |
|---------|-------------|
| `/bespoke-agentics:ux-audit-code` | Code-only audit against UX anti-pattern library |
| `/bespoke-agentics:ux-audit-visual` | Visual analysis of screenshots, GIFs, or video |
| `/bespoke-agentics:ux-audit-quick` | Quick heuristic spot-check on a single component |
| `/bespoke-agentics:ux-audit-a11y` | Accessibility-focused audit (ARIA, keyboard nav, color) |

### Wiki Skills

A Karpathy-style LLM wiki system that serves as the single source of truth for project intelligence, technical decisions, and business capabilities. Built on Obsidian-compatible Markdown with YAML frontmatter, cross-referenced `[[wiki-links]]`, and schema-enforced page types.

| Skill | Command | Description |
|-------|---------|-------------|
| **Wiki Init** | `/wiki:init` | Initialize a new Obsidian wiki vault. Scans the repo for context, asks clarifying questions, then creates the vault structure, schema, page templates, and global indexes. |
| **Wiki Scaffold Client** | `/wiki:new-client` | Create a new client workspace from a template. Derives folder structure, creates entity pages, ingests initial context documents, and populates a README with project overview. |
| **Wiki Ingest Meeting** | `/wiki:ingest-meeting` | Ingest a meeting transcript or analysis pipeline output. Creates or updates feature, gap, question, and decision pages, then links all entities to the new meeting summary. |
| **Wiki Ingest Document** | `/wiki:ingest-document` | Ingest a lightweight document (email, PDF, spec, Slack message). Updates affected feature, gap, decision, and question pages with new information. |
| **Wiki Query** | `/wiki:query` | Natural language search across wiki pages. Synthesizes answers with citations and optionally promotes substantive answers to new wiki pages. |
| **Wiki Lint** | `/wiki:lint` | Run an 8-dimension health check: broken links, orphaned pages, contradictions, stale content, missing cross-references, frontmatter errors (against the vault's own vocabulary), decision drift, and — with project-ontology installed — ontology violations. Optionally auto-fixes. |
| **Wiki Confluence Reconcile** | Skill only | Detect drift between the wiki and Confluence exports, generate reconciliation reports, and optionally sync changes bidirectionally. |

**Wiki slash commands** provide quick access to common operations:

| Command | Description |
|---------|-------------|
| `/wiki:init` | Initialize a new wiki vault |
| `/wiki:new-client '<name>' '<platform>'` | Scaffold a client workspace |
| `/wiki:ingest-meeting '<name>' '<dir>' '<label>'` | Ingest meeting outputs |
| `/wiki:ingest-document '<name>' '<path>' '<type>'` | Ingest a document |
| `/wiki:query '<question>'` | Search and synthesize wiki knowledge |
| `/wiki:lint --scope full` | Run full health check |
| `/wiki:status` | Display wiki health dashboard |

### Project DB — SQL for agents

Gives agents **one tool, SQL, over everything the project knows**, with the guardrails a data team puts in front of a read replica. With a wiki present, the schema is built *from* the wiki: base tables (pages, frontmatter fields, wikilinks, tags, sources, sections, cited raw documents, FTS5) plus one typed view per page type whose column docs come from the page templates, and curated cross-type views (`open_gaps`, `pending_decisions`, `backlinks`, `broken_links`…). Without a wiki it interviews you, scans the codebase, designs the schema, and installs a DB-first mandate. Same schema on SQLite locally and Cloudflare D1 remotely.

| Command | Description |
|---------|-------------|
| `/db:init [--mode local\|d1\|both]` | Build the database, vendor the engine into `.claude/db/`, install the guarded query CLI, SessionStart sync hook, local MCP server, and the CLAUDE.md mandate |
| `/db:query '<question or SELECT>'` | Answer a structured question with one read-only SELECT (row cap, timeout, CSV, audit log), then cite the source pages |
| `/db:sync [--full]` | Incremental refresh by content hash; regenerates typed views, re-applies `views.sql`, rebuilds FTS, rewrites `SCHEMA.md` |
| `/db:publish` | Export to D1, dry-run on local D1, push with wrangler, deploy the read-only MCP Worker, smoke-test, log |

Guardrails: read-only connection + SQLite authorizer, one statement per call, 200-row cap, 5 s timeout, cells truncated at 400 chars, every query audited (`python3 .claude/db/db.py audit --top` shows which repeated queries deserve a view). Requires `python3`; `uv` for the local MCP server; `wrangler` for D1.

### Project Ontology — an enforced, dot-notated vocabulary

A vocabulary written in a schema document drifts the week it is written: this plugin's own sample wiki had four disagreeing value lists and one client spelled two ways across 50 pages. `/ontology:init` mines what the vault already declares and uses — page types, template `key: # a|b|c` comments, SCHEMA.md value lists, observed values, scope folders, tags, link fields — into one file, `wiki/_schema/ontology.yaml`, of dot-notated terms (`gap.severity.critical`, `client.acme-corp`, `tag.budget-management`, `rel.related-feature`) with a proposed → approved → deprecated lifecycle. Pages keep plain values; page ids are derived from paths (`client.acme.gap.co-op-billing`). Declared values are approved, observed-only values are proposed — nothing is silently approved — and an interview settles the conflicts.

One engine enforces it everywhere: a **PreToolUse hook** blocks any write that *adds* a strict violation (unregistered or misspelled value, deprecated term, broken/ambiguous/noncanonical `[[link]]`, wrong relation target) and names the approved values and the propose command — violations already on a page never block (ratchet), so an existing vault adopts it on day one; a **PostToolUse hook** reports what still stands; a **Bash guard** turns approvals into a permission prompt and blocks shell writes into pages; a **SessionStart banner** keeps the vocabulary in context; CI runs `check --changed-since`; **project-db** loads `ontology_terms` / `ontology_violations`; **wiki-lint** reports it as Check 8.

| Command | Description |
|---------|-------------|
| `/ontology:init` | Scan the vault, interview on conflicts and outside values, write `ontology.yaml` + `ONTOLOGY.md`, sync template comments, install hooks, banner and CLAUDE.md block |
| `/ontology:check [<path>\|--all\|--changed-since <ref>]` | The write hook's rules on demand; exit 1 on strict violations; `--format lint\|json` |
| `/ontology:propose <id> --label … --definition …` | Register a value the vocabulary lacks (usable at once, flagged until approved) |
| `/ontology:approve <id>…` | Human gate: confirm pending terms and record who approved them |
| `/ontology:deprecate <id> --replaced-by <id>` | Human gate: retire a term; pages using it are flagged and `apply` rewrites them |
| `/ontology:apply [--dry-run]` | Rewrite aliases, spelling variants, deprecated values and noncanonical links to canonical form — nothing else |
| `/ontology:status` | Terms by status, policy, open violations by rule, pending approvals |

Requires `python3` only (stdlib; never PyYAML, so every machine checks the same way).

### Utility Skills

These are shared across the video and workflow pipelines:

| Skill | Description |
|-------|-------------|
| **extract-video-frames** | Extract frames and audio segments from video files using FFmpeg |
| **dedupe-frames** | Remove near-duplicate frames using perceptual hashing |
| **elevenlabs-transcribe** | Transcribe audio/video using ElevenLabs Scribe v2 API |

## Agents

| Agent | Description |
|-------|-------------|
| `ai-transparency` | Read-only scanner that reports AI transparency violations with file:line references |
| `video-to-deliverables` | Video analysis subagent for producing configurable deliverables |
| `workflow-analyzer` | Workflow analysis subagent for documentation and automation recommendations |
| `wiki-pipeline` | Orchestrator for complex multi-step wiki operations: Full Meeting Ingest, Bulk Bootstrap, and Weekly Maintenance workflows |

## Hooks

The plugin includes a **PostToolUse** hook that automatically checks files after edits for AI transparency violations. When you edit a file that contains AI/LLM SDK calls, the hook warns about missing:

- Progress/activity logging
- Status tracking fields
- UI status subscriptions
- Error handling states

The hook is framework-agnostic and detects Anthropic, OpenAI, Vercel AI SDK, LangChain, Cohere, and Google AI patterns.

## Prerequisites

Some skills require external tools:

- **FFmpeg**: Required for `extract-video-frames` (frame extraction and audio splitting)
- **Python 3.10+**: Required for `dedupe-frames` (with `imagehash` and `Pillow` packages)
- **uv**: Required for `elevenlabs-transcribe` (auto-installs dependencies via PEP 723)
- **ElevenLabs API key**: Set `ELEVENLABS_API_KEY` environment variable for transcription

## License

MIT
