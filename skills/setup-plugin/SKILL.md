---
name: setup-plugin
description: "Scaffold, optimize, and package a Claude Code plugin from a project folder. Use this skill whenever someone wants to create a new plugin, convert a .claude/ directory into a distributable plugin, audit and optimize existing plugin components (commands, skills, hooks, agents), generate a README, or organize a folder as a well-formed Claude Code plugin. Also trigger when the user mentions 'new plugin', 'plugin setup', 'package plugin', 'plugin scaffold', or wants to clean up and optimize their .claude/ directory for distribution."
---

# Setup Plugin

Convert a project folder into a well-formed, distributable Claude Code plugin. This skill handles the full lifecycle: scanning existing content, restructuring directories, optimizing every component, generating metadata files, and producing a comprehensive README.

## When to Use

- Converting a `.claude/` directory into a plugin
- Scaffolding a brand-new plugin from scratch
- Auditing and optimizing an existing plugin's commands, skills, hooks, and agents
- Generating or regenerating a plugin's README, plugin.json, or marketplace.json

## Input

The user provides a folder path. The folder may contain:
- A `.claude/` directory with commands, skills, hooks, agents (pre-plugin state)
- An already-structured plugin with `commands/`, `skills/`, `agents/`, `hooks/` at root level
- A mix of both
- Nothing yet (scaffold from scratch)

## Phase 1: Discovery & Inventory

Scan the provided folder to understand its current state. Build a complete inventory.

### 1a. Detect Structure Type

Check for these indicators:

| Indicator | Meaning |
|-----------|---------|
| `.claude-plugin/plugin.json` exists | Already a plugin — audit and optimize mode |
| `.claude/` directory exists with skills/commands/agents | Pre-plugin — needs conversion |
| Neither exists | Fresh scaffold — needs everything |

### 1b. Inventory All Components

For each component type, scan and catalog:

**Skills** — check both `.claude/skills/` and `skills/`:
- List each skill directory and its SKILL.md
- Note whether it has `references/`, `templates/`, `scripts/` subdirectories
- Extract frontmatter (name, description)

**Commands** — check both `.claude/commands/` (including subdirectories) and `commands/`:
- List each command .md file
- Extract frontmatter (name, description, argument-hint, allowed-tools)
- Note the dispatch pattern (single skill, routing, orchestration)

**Agents** — check both `.claude/agents/` and `agents/`:
- List each agent .md file
- Extract frontmatter (name, description, tools, model)

**Hooks** — check for `hooks/hooks.json` or `.claude/hooks.json` or `.claude/settings.json`:
- List each hook type and its matchers
- Note any scripts referenced

**Scripts** — check `scripts/` and `.claude/scripts/`:
- List executable files
- Note which hooks or skills reference them

### 1c. Present Inventory to User

Show the user what was found and ask:
- Plugin name (suggest based on folder name, kebab-case)
- Author name
- Brief description of the plugin's purpose
- Any components to exclude or add
- The namespace prefix for commands (e.g., `verndale`, `bespokeagentics`)

## Phase 2: Restructure

Move components from `.claude/` layout into the canonical plugin directory structure.

### Target Structure

```
plugin-root/
├── .claude-plugin/
│   └── plugin.json
├── marketplace.json
├── README.md
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── references/     (optional)
│       ├── templates/       (optional)
│       └── scripts/         (optional)
├── commands/
│   └── <command-name>.md
├── agents/
│   └── <agent-name>.md
├── hooks/
│   └── hooks.json
└── scripts/
    └── <script-name>.sh|.py
```

### Restructuring Rules

1. **Skills**: Move from `.claude/skills/<name>/` → `skills/<name>/`. Preserve internal structure (references/, templates/, scripts/).
2. **Commands**: Flatten from `.claude/commands/<namespace>/` → `commands/`. Remove subdirectory nesting. Rename files to drop namespace prefix from filename since it will be in the frontmatter `name` field.
3. **Agents**: Move from `.claude/agents/` → `agents/`.
4. **Hooks**: Convert `.claude/settings.json` hook entries or `.claude/hooks.json` → `hooks/hooks.json` using the plugin hooks format.
5. **Scripts**: Move from `.claude/scripts/` → `scripts/`. Update any references in hooks or skills.
6. **Preserve**: Do not delete the original `.claude/` directory until the user confirms the migration is correct. Instead, create the new structure alongside it.

If the plugin already has the correct structure, skip this phase.

## Phase 3: Optimize Components

Audit and optimize each component type against best practices. Read `references/plugin-structure.md` for the canonical formats.

### 3a. Optimize Commands

For each command file:

1. **Add `name` field** — Must be `<namespace>:<command-name>` (e.g., `verndale:migration-pipeline`). The namespace is the plugin name or a short prefix agreed with the user.
2. **Description must start with a verb** — "Audit...", "Analyze...", "Run...", "Transform...", "Generate...". Not "End-to-end..." or "Quick...".
3. **Fix YAML frontmatter** — No blank lines inside `---` fences. All required fields present: `description`, `argument-hint`.
4. **Validate `allowed-tools`** — Only include if restricting beyond the agent's own tool set. Simple dispatch commands that only call `Skill()` should restrict to just that skill.
5. **Validate dispatch pattern** — Body must reference a real skill or agent name. `$ARGUMENTS` must be present.
6. **Check body quality** — Dispatch prompts should be specific enough for the agent/skill to know exactly what to do.

### 3b. Optimize Skills

For each SKILL.md:

1. **Frontmatter** — Must have `name` and `description`. Description should be detailed enough to trigger correctly — include both what it does AND when to use it.
2. **Body length** — Ideal is under 500 lines. If longer, check if content should move to `references/`.
3. **Reference files** — Must be clearly pointed to from SKILL.md with guidance on when to read them.
4. **Scripts** — Any bundled scripts should be executable and referenced from the skill body.

### 3c. Optimize Agents

For each agent .md file:

1. **Frontmatter** — Must have `name`, `description`, `tools`, `model`.
2. **Description** — Should include trigger phrases like "Use proactively for any [domain] work".
3. **Tools** — Implementation agents get Read, Write, Edit, Bash, Grep, Glob. Validation/read-only agents get Read, Bash, Grep, Glob (no Write/Edit).
4. **Model** — Default to `sonnet` for implementation, `opus` for validation/orchestration.

### 3d. Optimize Hooks

For `hooks/hooks.json`:

1. **Structure** — Must follow the plugin hooks format with `hooks` → `<HookType>` → array of matchers.
2. **Script references** — Must use `${CLAUDE_PLUGIN_ROOT}/scripts/` prefix for portability.
3. **Timeouts** — Every command hook should have a reasonable `timeout` (default 10000ms).

## Phase 4: Generate Metadata Files

### 4a. plugin.json

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "description": "<user-provided or generated description>",
  "author": {
    "name": "<author-name>"
  },
  "keywords": [<derived from skill/command names>]
}
```

### 4b. marketplace.json

Create `marketplace.json` at root:

```json
{
  "name": "<plugin-name>-marketplace",
  "plugins": [
    {
      "name": "<plugin-name>",
      "version": "1.0.0",
      "description": "<same as plugin.json>",
      "source": "."
    }
  ]
}
```

### 4c. README.md

Generate a comprehensive README following this structure:

```markdown
# <plugin-name>

<One-line description>

## Installation

<Installation instructions with marketplace add and local dev commands>

## Skills

### Primary Skills

<Table: Skill | Command | Description>

### Variant/Utility Skills (if applicable)

<Table: Command | Description>

## Agents

<Table: Agent | Description>

## Hooks

<Description of automated behaviors>

## Prerequisites

<External tools, API keys, dependencies needed>

## License

MIT
```

Derive the content from the actual components — do not invent capabilities. List only skills that have corresponding commands. Group related commands (like ux-audit variants) into subsections.

## Phase 5: Verification

After all changes:

1. **Grep all command files** for `name: <namespace>:` to confirm naming.
2. **Check no blank lines** inside YAML frontmatter fences.
3. **Verify all referenced skills/agents exist** — every `Skill()` or agent dispatch in commands must point to a real file.
4. **Verify all hook script paths exist** — every script referenced in hooks.json must be present.
5. **Validate JSON files** — plugin.json and marketplace.json must be valid JSON.
6. **Present summary** — Show the user what was created, moved, and optimized with a before/after comparison.

## Important Notes

- Always ask the user for the namespace prefix before optimizing commands. Different plugins use different prefixes.
- Preserve all existing functionality — this is a restructuring and optimization pass, not a rewrite.
- If a `.claude/` directory existed alongside the new plugin structure, remind the user they can safely remove it after verifying the migration.
- When optimizing descriptions, keep the original intent — just improve the phrasing to follow best practices (verb-first, concise, specific).
