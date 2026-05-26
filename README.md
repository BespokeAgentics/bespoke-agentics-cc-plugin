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

### Primary Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **AI Transparency** | `/bespokeagentics:ai-transparency` | Audit and fix AI operations lacking UI state coverage (loading, streaming, logs, errors). Enforces the "No Black Boxes" policy. |
| **Architect Agents** | `/bespokeagentics:architect-agents` | Analyze a project and generate a complete `.claude/agents/` and `.claude/commands/` architecture with documentation. |
| **UX Audit** | `/bespokeagentics:ux-audit` | Comprehensive UX evaluation using Nielsen's 10 Heuristics and Norman's 6 Design Principles. |
| **Video to Deliverables** | `/bespokeagentics:video-to-deliverables` | End-to-end video analysis pipeline. Transforms recordings into workflow docs, migration analysis, meeting summaries, or training guides. |
| **Workflow Analyzer** | `/bespokeagentics:workflow-analyzer` | Client workflow analysis from video recordings. Produces application inventory, challenge mapping, and AI automation recommendations. |
| **Setup Plugin** | `/bespokeagentics:setup-plugin` | Scaffold, optimize, and package a folder as a well-formed Claude Code plugin. Converts `.claude/` directories into distributable plugins. |
| **Pi Assistant** | `/bespokeagentics:pi-assistant` | Understand the pi.dev coding agent, customize its harness, build Pi skills/extensions/packages, and search for or install Pi packages. |
| **Spec Elicitation** | `/bespokeagentics:spec-elicitation` | Interview-driven spec development that turns vague ideas into complete implementation specifications. |

## Spec Interviewer UI

The interactive web interface lives in `apps/spec-interviewer/`. It loads `commands/spec-elicitation.md` as the source of truth, starts a Claude Agent SDK session, renders `AskUserQuestion` calls as structured form cards, and writes the final Markdown spec inside this repository.

```bash
cd apps/spec-interviewer
npm install
npm run dev
```

Open `http://127.0.0.1:4177`.

The Agent SDK can use your local Claude Code OAuth login automatically. `ANTHROPIC_API_KEY` is optional if you prefer key-based auth.

### Pi Assistant Commands

| Command | Description |
|---------|-------------|
| `/bespokeagentics:pi-assistant` | General Pi harness and package workflow entry point |
| `/bespokeagentics:pi-customize-harness` | Customize settings, context files, skills, prompt templates, extensions, or packages |
| `/bespokeagentics:pi-build-extension` | Build or update a Pi TypeScript extension and its slash commands |
| `/bespokeagentics:pi-build-skill` | Build or update a Pi skill with bundled references or helper scripts |
| `/bespokeagentics:pi-build-package` | Build or update a shareable Pi package using conventional resource directories |
| `/bespokeagentics:pi-search-packages` | Search npm packages tagged `pi-package` and recommend the best matches |
| `/bespokeagentics:pi-install-package` | Install a Pi package with the correct source syntax and scope |
| `/bespokeagentics:pi-review-setup` | Audit a local Pi setup and recommend targeted improvements |

### UX Audit Variants

| Command | Description |
|---------|-------------|
| `/bespokeagentics:ux-audit-code` | Code-only audit against UX anti-pattern library |
| `/bespokeagentics:ux-audit-visual` | Visual analysis of screenshots, GIFs, or video |
| `/bespokeagentics:ux-audit-quick` | Quick heuristic spot-check on a single component |
| `/bespokeagentics:ux-audit-a11y` | Accessibility-focused audit (ARIA, keyboard nav, color) |

### Wiki Skills

A Karpathy-style LLM wiki system that serves as the single source of truth for project intelligence, technical decisions, and business capabilities. Built on Obsidian-compatible Markdown with YAML frontmatter, cross-referenced `[[wiki-links]]`, and schema-enforced page types.

| Skill | Command | Description |
|-------|---------|-------------|
| **Wiki Init** | `/wiki:init` | Initialize a new Obsidian wiki vault. Scans the repo for context, asks clarifying questions, then creates the vault structure, schema, page templates, and global indexes. |
| **Wiki Scaffold Client** | `/wiki:new-client` | Create a new client workspace from a template. Derives folder structure, creates entity pages, ingests initial context documents, and populates a README with project overview. |
| **Wiki Ingest Meeting** | `/wiki:ingest-meeting` | Ingest a meeting transcript or analysis pipeline output. Creates or updates feature, gap, question, and decision pages, then links all entities to the new meeting summary. |
| **Wiki Ingest Document** | `/wiki:ingest-document` | Ingest a lightweight document (email, PDF, spec, Slack message). Updates affected feature, gap, decision, and question pages with new information. |
| **Wiki Query** | `/wiki:query` | Natural language search across wiki pages. Synthesizes answers with citations and optionally promotes substantive answers to new wiki pages. |
| **Wiki Lint** | `/wiki:lint` | Run a 7-dimension health check: broken links, orphaned pages, contradictions, stale content, missing cross-references, schema violations, and frontmatter errors. Optionally auto-fixes. |
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
