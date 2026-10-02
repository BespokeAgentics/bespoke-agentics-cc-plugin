# Command File Format Reference

Quality rules and format requirements for generated `.claude/commands/*.md` files.

## YAML Frontmatter (required)

```yaml
---
description: {short description shown in command list and autocomplete}
argument-hint: {argument format shown to user, e.g. [name] [target]}
---
```

**Field rules:**
- `description`: One line, starts with a verb. Shown in `/` autocomplete. Example: "Build a Lit 3 web component with React wrapper, tests, and Storybook story"
- `argument-hint`: Shows the expected argument format. Use `[brackets]` for required args, `[optional]` for optional. Use `|` for choices: `[target: a|b|c]`

## Body Patterns

The body instructs Claude how to dispatch agents. Use `$ARGUMENTS` to reference user input.

### Dispatch Command (single agent)

For commands that always dispatch one specific agent:

```markdown
{Brief task context}: $ARGUMENTS

Use the Agent tool to dispatch the `{agent-name}` agent with this task:

"{Detailed prompt describing what the agent should do with $ARGUMENTS}"

Use subagent_type: "{agent-name}" and model: "{model}".
```

### Routing Command (multiple agents by argument)

For commands where the first argument selects the agent:

```markdown
{Brief task context}: $ARGUMENTS

Parse the {first/second} argument to select the agent:
- "{value-a}" → use Agent tool with subagent_type: "{agent-a}"
- "{value-b}" → use Agent tool with subagent_type: "{agent-b}"
- "{value-c}" → use Agent tool with subagent_type: "{agent-c}"

The remaining arguments are the task details. Dispatch the selected agent with:

"{Detailed prompt using remaining arguments}"

Use model: "{model}".
```

### Orchestration Command (multi-agent coordination)

For commands that coordinate several agents. The command body runs in the main session, which
holds the Agent tool; the orchestrator agent returns a dispatch plan, because a subagent cannot
dispatch other agents:

```markdown
{Brief task context}: $ARGUMENTS

Phase/agent mapping: {table}

1. Use the Agent tool to dispatch the `{orchestrator-name}` agent (subagent_type:
   "{orchestrator-name}", model: "opus") to check prerequisites and return a dispatch plan.
2. Dispatch the implementation agents in the plan (parallel where independent), with their
   model assignments.
3. Dispatch the validators, then synthesize results and report status + next steps.
```

## Naming Conventions

- Namespace: `{project}:` prefix groups related commands
- Verbs: `build-`, `validate`, `run-`, `migrate`, `status`
- Use kebab-case for multi-word names
- File name matches command name: `b2b:build-component.md` → `/b2b:build-component`

## Quality Rules

- Every command must reference a real agent name from `.claude/agents/`
- The dispatch prompt should be specific enough that the agent knows exactly what to do
- Routing commands must cover all valid argument values
- Orchestration commands must include the phase-agent mapping so the orchestrator can execute without reading external files
- Never include `allowed-tools` in frontmatter unless you need to restrict tools beyond the agent's own restrictions
