# Orchestration Command Template

For commands that dispatch an orchestrator which coordinates multiple sub-agents.

## Template

```
---
description: {COMMAND_DESCRIPTION}
argument-hint: {ARGUMENT_FORMAT}
---

{BRIEF_CONTEXT}: $ARGUMENTS

Use the Agent tool to dispatch the `{ORCHESTRATOR_NAME}` agent with this orchestration task:

"{ORCHESTRATION_PROMPT}

Phase → Agent mapping:
{PHASE_AGENT_TABLE}

Execution protocol:
1. Check prerequisites — are dependent phases complete? If not, report what's blocking.
2. Dispatch implementation agents (parallel where independent) using the Agent tool
3. When implementation completes, dispatch validators in parallel using the Agent tool
4. Synthesize results: what was built, what passed validation, what failed
5. Report final status with recommended next steps

Use subagent_type matching each agent name. Implementation agents use model '{IMPL_MODEL}'. Validators use model '{VAL_MODEL}'."

Use subagent_type: "{ORCHESTRATOR_NAME}" and model: "opus".
```

## Filling Instructions

- `{ORCHESTRATOR_NAME}`: The orchestrator agent from `.claude/agents/`
- `{PHASE_AGENT_TABLE}`: Complete phase-to-agent mapping so the orchestrator can execute without reading external files
- Model assignments for sub-agents must be included in the prompt
