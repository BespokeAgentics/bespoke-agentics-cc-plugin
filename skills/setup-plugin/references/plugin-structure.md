# Claude Code Plugin Structure Reference

Canonical formats and conventions for all plugin component types.

## Table of Contents

- [Directory Layout](#directory-layout)
- [plugin.json Format](#pluginjson-format)
- [marketplace.json Format](#marketplacejson-format)
- [Command File Format](#command-file-format)
- [Skill File Format](#skill-file-format)
- [Agent File Format](#agent-file-format)
- [Hooks Format](#hooks-format)
- [Naming Conventions](#naming-conventions)

---

## Directory Layout

```
plugin-root/
├── .claude-plugin/
│   └── plugin.json              # Required: plugin metadata
├── marketplace.json             # Required: plugin catalog
├── README.md                    # Required: installation + usage docs
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md             # Required: skill definition
│       ├── references/          # Optional: domain docs loaded on demand
│       ├── templates/           # Optional: output templates
│       └── scripts/             # Optional: executable helpers
├── commands/
│   └── <command-name>.md        # Slash command definitions
├── agents/
│   └── <agent-name>.md          # Subagent definitions
├── hooks/
│   └── hooks.json               # Automated behaviors
└── scripts/
    └── <script-name>.sh|.py     # Shared scripts (referenced by hooks/skills)
```

---

## plugin.json Format

Location: `.claude-plugin/plugin.json`

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "One-line description of what the plugin provides",
  "author": {
    "name": "Author Name"
  },
  "keywords": ["keyword-1", "keyword-2"]
}
```

**Rules:**

- `name`: kebab-case, matches the repository/folder name
- `version`: semver format
- `description`: concise, lists the main capabilities
- `keywords`: derived from skill and command names, used for discovery

---

## marketplace.json Format

Location: root of plugin directory

```json
{
  "name": "<plugin-name>-marketplace",
  "plugins": [
    {
      "name": "<plugin-name>",
      "version": "1.0.0",
      "description": "<same as plugin.json description>",
      "source": "."
    }
  ]
}
```

**Rules:**

- `name`: `<plugin-name>-marketplace` by convention
- `source`: `"."` for single-plugin repos, or relative path for multi-plugin marketplaces

---

## Command File Format

Location: `commands/<command-name>.md`

### YAML Frontmatter

```yaml
---
name: <namespace>:<command-name>
description: <verb-first one-line description>
argument-hint: <argument format shown to user>
allowed-tools: <comma-separated tool list> # only if restricting
---
```

**Field rules:**

- `name`: `<namespace>:<kebab-case-name>`. Namespace is the plugin name or agreed short prefix.
- `description`: Starts with a verb (Audit, Analyze, Run, Transform, Generate, Scan, Check). Shown in autocomplete.
- `argument-hint`: Use `<brackets>` for required args, `[brackets]` for optional. Use `|` for choices.
- `allowed-tools`: Only include if you need to restrict tools. Simple Skill() dispatches should restrict to just the skill.

### Body Patterns

**Dispatch** (single skill/agent):

```markdown
Invoke the <skill-name> skill for: $ARGUMENTS
```

**Routing** (argument selects agent):

```markdown
Parse the first argument to select the agent:

- "value-a" → dispatch agent-a
- "value-b" → dispatch agent-b

Remaining arguments are the task: $ARGUMENTS
```

**Orchestration** (multi-agent):

```markdown
Use the Agent tool to dispatch the orchestrator with:

- Phase mapping
- Execution protocol
- Model assignments
```

### Quality Checklist

- [ ] `name` starts with `<namespace>:`
- [ ] `description` starts with a verb
- [ ] No blank lines inside `---` fences
- [ ] `$ARGUMENTS` is present in body
- [ ] Every `Skill()` or agent name references a real file
- [ ] `allowed-tools` only present when restricting beyond defaults

---

## Skill File Format

Location: `skills/<skill-name>/SKILL.md`

### YAML Frontmatter

```yaml
---
name: <skill-name>
description: "<What it does AND when to use it. Include trigger phrases.>"
---
```

**Field rules:**

- `name`: kebab-case, matches the directory name
- `description`: Detailed enough to trigger correctly. Include both capabilities and trigger contexts. Be slightly "pushy" to combat under-triggering.

### Body Guidelines

- Keep under 500 lines — move detailed reference material to `references/` subdirectory
- Use imperative form for instructions
- Include examples where helpful
- Reference files clearly with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

### Progressive Disclosure

1. **Metadata** (name + description) — always in context (~100 words)
2. **SKILL.md body** — loaded when skill triggers (<500 lines ideal)
3. **Bundled resources** — loaded as needed (unlimited size)

---

## Agent File Format

Location: `agents/<agent-name>.md`

### YAML Frontmatter

```yaml
---
name: <agent-name>
description: "<what the agent does — include 'Use proactively for...' trigger phrase>"
tools: <comma-separated tool list>
model: <sonnet|opus>
---
```

**Field rules:**

- `name`: kebab-case, matches the filename without extension
- `description`: Include trigger phrases. Example: "Use proactively for any [domain] work"
- `tools`: Implementation agents → `Read, Write, Edit, Bash, Grep, Glob`. Read-only/validation agents → `Read, Bash, Grep, Glob`
- `model`: Default `sonnet` for implementation, `opus` for validation/orchestration

### Body Structure

Agent bodies typically use XML sections:

- `<role>` — What the agent is and does
- `<constraints>` — Minimum 5 constraints, ALWAYS/NEVER formatting
- `<architecture>` — How the agent fits into the system
- `<testing>` — Validation commands
- `<output_format>` — Expected output structure

---

## Hooks Format

Location: `hooks/hooks.json`

```json
{
  "hooks": {
    "<HookType>": [
      {
        "matcher": "<tool-name-pattern>",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/scripts/<script-name>\"",
            "timeout": 10000
          }
        ]
      }
    ]
  }
}
```

**Hook types:** `PreToolUse`, `PostToolUse`, `Notification`, `Stop`

**Rules:**

- Script paths must use `${CLAUDE_PLUGIN_ROOT}/scripts/` for portability
- Every command hook needs a `timeout` (default: 10000ms)
- `matcher` uses `|` for multiple tool names (e.g., `"Edit|Write|MultiEdit"`)

---

## Naming Conventions

| Component       | Convention                        | Example                            |
| --------------- | --------------------------------- | ---------------------------------- |
| Plugin name     | kebab-case                        | `verndale-agentics`                |
| Skill directory | kebab-case                        | `skills/ux-audit/`                 |
| Command file    | kebab-case                        | `commands/ux-audit-quick.md`       |
| Command `name`  | kebab-case, matching the filename | `migration-pipeline`               |
| Agent file      | kebab-case                        | `agents/workflow-analyzer.md`      |
| Script file     | kebab-case                        | `scripts/ai-transparency-check.sh` |
| Keywords        | kebab-case                        | `"ai-transparency"`                |

### Namespace Selection

**Never put the plugin name in a command's `name`.** Claude Code prefixes it
automatically, so a command named `bespokeagentics:dead-code-sweep` inside the
`bespoke-agentics` plugin is invoked as
`/bespoke-agentics:bespokeagentics:dead-code-sweep`. This stutter is a real bug
that shipped in this plugin through v1.27.1 and had to be reverted.

The rule:

- A command at `commands/<leaf>.md` gets `name: <leaf>` and is invoked as
  `/<plugin>:<leaf>`.
- A command grouped in a subdirectory, `commands/<group>/<leaf>.md`, gets
  `name: <group>:<leaf>` and is invoked as `/<plugin>:<group>:<leaf>`. The
  namespace names the **group**, never the plugin — `wiki:query`, `bun:add`,
  `agentnative:fast-ci`.

Do not ask the user to choose a namespace prefix; it is determined by where the
file sits.

### Commands vs. skills: do not ship both

A capability belongs in `skills/<name>/` **or** `commands/<name>.md`, not both.
Publishing both puts two entries with the same purpose in the slash picker. If a
capability needs an argument contract, document it in the skill body — that is
the surviving entry point.
