# bespoke-agentics

A Claude Code plugin with AI transparency auditing, agent architecture generation, UX evaluation, video-to-deliverables pipelines, and workflow analysis.

## Installation

Add this repository as a marketplace, then install the plugin:

```bash
# Add the marketplace
claude plugin install bespoke-agentics@<your-github-url>

# Or test locally during development
claude --plugin-dir ./bespoke-agentics-plugin
```

## Skills

### Primary Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **AI Transparency** | `/bespoke-agentics:ai-transparency` | Audit and fix AI operations lacking UI state coverage (loading, streaming, logs, errors). Enforces the "No Black Boxes" policy. |
| **Architect Agents** | `/bespoke-agentics:architect-agents` | Analyze a project and generate a complete `.claude/agents/` and `.claude/commands/` architecture with documentation. |
| **UX Audit** | `/bespoke-agentics:ux-audit` | Comprehensive UX evaluation using Nielsen's 10 Heuristics and Norman's 6 Design Principles. |
| **Video to Deliverables** | `/bespoke-agentics:video-to-deliverables` | End-to-end video analysis pipeline. Transforms recordings into workflow docs, migration analysis, meeting summaries, or training guides. |
| **Workflow Analyzer** | `/bespoke-agentics:workflow-analyzer` | Client workflow analysis from video recordings. Produces application inventory, challenge mapping, and AI automation recommendations. |
| **Setup Plugin** | `/bespoke-agentics:setup-plugin` | Scaffold, optimize, and package a folder as a well-formed Claude Code plugin. Converts `.claude/` directories into distributable plugins. |

### UX Audit Variants

| Command | Description |
|---------|-------------|
| `/bespoke-agentics:ux-audit-code` | Code-only audit against UX anti-pattern library |
| `/bespoke-agentics:ux-audit-visual` | Visual analysis of screenshots, GIFs, or video |
| `/bespoke-agentics:ux-audit-quick` | Quick heuristic spot-check on a single component |
| `/bespoke-agentics:ux-audit-a11y` | Accessibility-focused audit (ARIA, keyboard nav, color) |

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
