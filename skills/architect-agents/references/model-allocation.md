# Model Allocation Reference

Rules for assigning Opus vs Sonnet to agents.

## Default Allocation

| Role | Default Model | Rationale |
|---|---|---|
| Implementation agent | Sonnet | Well-scoped code generation within defined boundaries |
| Validation agent | Opus | Cross-cutting reasoning about contracts and compliance |
| Orchestrator | Opus | Architectural reasoning, dependency analysis, agent coordination |

## When to Override Defaults

### Upgrade Sonnet → Opus

- Agent must make **architectural decisions** across multiple packages
- Agent works with **complex type systems** (advanced generics, conditional types)
- Agent coordinates with **external APIs** that require careful reasoning about contracts
- Agent handles **security-sensitive code** (auth, encryption, access control)

### Downgrade Opus → Sonnet

- Validator only checks **mechanical properties** (file exists, field present, name matches)
- Orchestrator manages a **simple linear pipeline** (no parallel dispatch, no dependency graph)
- Cost is a primary concern and the team is large (>10 agents)

## User Preference Options

Present these three options during elicitation:

**A) Opus validation + Sonnet implementation (recommended)**
- Best quality for cross-cutting validation
- Cost-effective for implementation work
- Recommended for projects with compliance/quality requirements

**B) All Sonnet**
- Lowest cost
- Relies on thorough agent prompts to compensate for model capability
- Suitable for well-understood domains with simple validation needs

**C) Opus orchestrator only + Sonnet everything else**
- Middle ground: orchestrator gets best reasoning
- Validators and builders both use Sonnet
- Suitable when orchestration complexity is the main challenge

## Cost Awareness

- Opus costs ~5x more than Sonnet per token
- A team of 10 agents with 5 Opus validators will cost significantly more than all-Sonnet
- For budget-sensitive projects, recommend starting all-Sonnet and upgrading individual agents that underperform
