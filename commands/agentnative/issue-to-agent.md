---
name: "agentnative:issue-to-agent"
description: "Trigger coding agents automatically from issue-triage labels: generates GitHub Actions workflows around anthropics/claude-code-action v1 so a new issue gets auto-triaged, an `agent:repro` label produces a failing test on a claude/ branch plus repro steps commented on the issue, and an `agent:poc` label produces a spike branch with design notes — least-privilege permissions, scoped allowedTools, turn budgets, prompt-injection-aware prompts, zizmor-verified. The engineer picks up the issue with the ground already prepared."
argument-hint: "[mode: plan|implement] [labels: 'needs-repro:repro,spike:poc']"
allowed-tools: Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
disable-model-invocation: true
---

> **How this command loads its skill.** `issue-to-agent` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/issue-to-agent/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Issue → Agent

Follow the `issue-to-agent` skill (loaded as described above): design the label taxonomy, generate the dispatch workflows, and
verify the handoff end-to-end.

## Arguments

Parse from `$ARGUMENTS`:

```
[mode: plan|implement] [labels]
```

- `mode` (optional, default `implement`) — `plan` writes the full workflow set + taxonomy
  rationale to `./plans/issue-to-agent.md` without touching `.github/`; `implement` interviews,
  then writes the workflows.
- `labels` (optional) — label→behavior overrides, e.g. `'needs-repro:repro,spike:poc'`.

## Process

Follow the `issue-to-agent` skill (loaded as described above) and forward `$ARGUMENTS`. The skill will:

1. Detect existing labels, automation, test conventions, and auth posture
2. Propose a minimal dispatch taxonomy (triage on open; `agent:repro`, `agent:poc` on label)
3. Interview: which behaviors, auth method, mandate boundaries, who may apply dispatch labels
4. Generate workflows from the reference templates with the handoff contract baked into every
   prompt (what was tried, exact repro steps, quoted failing output, branch link, unverified
   items marked)
5. Verify: zizmor-clean, `workflow_dispatch` dry-run against a sandbox issue, one real handoff
   walked with the user

Every workflow treats issue bodies as untrusted input and ends its mandate at the handoff —
repros and spikes, never unsupervised fixes.
