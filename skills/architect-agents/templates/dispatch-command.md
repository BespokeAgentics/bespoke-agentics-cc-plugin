# Dispatch Command Template

For commands that dispatch a single, specific agent.

## Template

```
---
description: {COMMAND_DESCRIPTION — starts with a verb}
argument-hint: {ARGUMENT_FORMAT}
---

{BRIEF_CONTEXT}: $ARGUMENTS

Use the Agent tool to dispatch the `{AGENT_NAME}` agent with this task:

"{DETAILED_PROMPT}

Requirements:
{NUMBERED_REQUIREMENTS}

$ARGUMENTS"

Use subagent_type: "{AGENT_NAME}" and model: "{MODEL}".
```

## Filling Instructions

- `{COMMAND_DESCRIPTION}`: One line starting with a verb. Shown in autocomplete.
- `{ARGUMENT_FORMAT}`: Use `[brackets]` for args, `|` for choices
- `{AGENT_NAME}`: Must match a file in `.claude/agents/` (without `.md`)
- `{DETAILED_PROMPT}`: Specific enough that the agent knows exactly what to do
- `{NUMBERED_REQUIREMENTS}`: Key constraints the agent must follow for this task
- `{MODEL}`: Usually matches the agent's model field
