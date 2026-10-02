# Orchestration Command Template

For commands that coordinate multiple sub-agents. The command body runs in the main session,
which holds the Agent tool; the `{ORCHESTRATOR_NAME}` agent plans and validates but cannot
dispatch (a subagent has no Agent tool).

## Template

```
---
description: {COMMAND_DESCRIPTION}
argument-hint: {ARGUMENT_FORMAT}
---

{BRIEF_CONTEXT}: $ARGUMENTS

You are running this orchestration from the main session.

Phase → Agent mapping:
{PHASE_AGENT_TABLE}

Execution protocol:
1. Use the Agent tool to dispatch the `{ORCHESTRATOR_NAME}` agent (subagent_type: "{ORCHESTRATOR_NAME}", model: "opus") with: "{ORCHESTRATION_PROMPT}". It checks prerequisites and the dependency graph and returns a dispatch plan (phase, agent, task, acceptance criteria), or what is blocking.
2. Dispatch the implementation agents in that plan with the Agent tool — in parallel where the plan marks them independent. Use subagent_type matching each agent name and model '{IMPL_MODEL}'.
3. When implementation completes, dispatch the validators in parallel (model '{VAL_MODEL}').
4. Synthesize results: what was built, what passed validation, what failed.
5. Report final status with recommended next steps.
```

## Filling Instructions

- `{ORCHESTRATOR_NAME}`: The orchestrator agent from `.claude/agents/`
- `{PHASE_AGENT_TABLE}`: Complete phase-to-agent mapping so the orchestrator can execute without reading external files
- Model assignments for sub-agents must be included in the prompt
