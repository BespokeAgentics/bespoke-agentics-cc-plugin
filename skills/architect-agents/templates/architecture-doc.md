# Architecture Doc Template

Skeleton for the `_architecture.md` file generated alongside agents.

## Template

```markdown
# Agent Architecture

**Generated:** {DATE}
**Project:** {PROJECT_NAME}
**Generator:** /architect-agents

## Decision Log

| Decision | Choice | Rationale |
|---|---|---|
| Team purpose | {builders/validators/both} | {why — from elicitation} |
| Grouping strategy | {1:1 / layer-grouped / platform-grouped / minimal} | {why} |
| Model allocation | {Opus validation + Sonnet impl / all Sonnet / etc.} | {why} |
| Existing agents | {kept alongside / replaced / none existed} | {why} |
| Validation concerns | {list of concerns} | {derived from spec or user input} |

## Agent Roster

### Implementation Agents ({MODEL})

| Agent | Scope | Owned Paths |
|---|---|---|
| `{name}` | {one-line scope} | {paths} |

### Validation Agents ({MODEL})

| Agent | Audits | Key Checks |
|---|---|---|
| `{name}` | {audit domain} | {what it checks} |

### Orchestrator ({MODEL})

| Agent | Coordinates | Key Responsibilities |
|---|---|---|
| `{name}` | {scope} | {responsibilities} |

## Dependency Graph

` ` `
{TEXT_DIAGRAM}
` ` `

## Phase Mapping

| Phase | Implementation Agents | Validators |
|---|---|---|
| {N}: {name} | {agents} | {validators} |

_(Omit this section if project has no phased roadmap)_

## Command Reference

| Command | Type | Dispatches |
|---|---|---|
| `/{ns}:{name}` | {dispatch/routing/orchestration} | {agent(s)} |

_(Omit this section if no commands were generated)_

## When to Regenerate

Re-run `/architect-agents` when:
- New packages or services are added to the project
- Technology stack changes significantly (new framework, language, or platform)
- Team structure or validation requirements change
- Agent prompts have drifted from actual codebase patterns (file structures, commands, conventions no longer match)
- A major refactor changes package boundaries or dependency graph
```

## Filling Instructions

- `{DATE}`: ISO date when generated
- `{PROJECT_NAME}`: From root package.json `name` field, or directory name
- Decision log: One row per decision from Phase 2 elicitation
- Agent roster: From Phase 3 approved roster
- Dependency graph: Text diagram from domain map
- Phase mapping: From spec phases, or omit if no phases
- Command reference: From Phase 6, or omit if no commands generated
