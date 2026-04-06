# Routing Command Template

For commands where the first argument selects which agent to dispatch.

## Template

```
---
description: {COMMAND_DESCRIPTION}
argument-hint: {ARGUMENT_FORMAT_WITH_CHOICES}
---

{BRIEF_CONTEXT}: $ARGUMENTS

Parse the {ROUTING_ARGUMENT_POSITION} argument to select the agent:
- "{VALUE_A}" → use Agent tool with subagent_type: "{AGENT_A}"
- "{VALUE_B}" → use Agent tool with subagent_type: "{AGENT_B}"
- "{VALUE_C}" → use Agent tool with subagent_type: "{AGENT_C}"

The remaining arguments are the task details. Dispatch the selected agent with:

"{DETAILED_PROMPT_USING_REMAINING_ARGS}"

Use model: "{MODEL}".
```

## Filling Instructions

- `{ROUTING_ARGUMENT_POSITION}`: "first", "second", etc.
- Each routing value must map to exactly one agent
- The routing table must cover ALL valid argument values
- Remaining arguments after routing are passed as task context
