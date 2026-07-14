---
name: "agentnative:hermetic-deploy"
description: "Make the app deployable locally, hermetically, and several at a time: audits the repo against the H* hermeticity catalog (fixed host ports, host-shared state, missing healthchecks, unseeded databases, live external dependencies), then builds the isolation layer — Docker Compose project-name namespacing, ephemeral ports discovered via compose port, per-instance volumes, up --wait healthchecks, in-stack mocks for externals, and the scripts/dev-stack.sh contract (up <id> prints a healthy seeded URL; down <id> removes it without a trace). Verification actually runs N instances side by side and proves isolation, teardown, and cold-start time."
argument-hint: "[mode: audit|implement] [instances: N]"
allowed-tools: Skill(hermetic-deploy), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Hermetic Deploy

Run the `hermetic-deploy` skill: give every agent its own one-command, seeded, isolated instance
of the app.

## Arguments

Parse from `$ARGUMENTS`:

```
[mode: audit|implement] [instances]
```

- `mode` (optional, default `implement`) — `audit` writes the read-only hermeticity report;
  `implement` interviews, then builds the isolation layer.
- `instances` (optional, default `2`) — how many simultaneous instances the verification step
  must prove.

## Process

Invoke the `hermetic-deploy` skill and forward `$ARGUMENTS`. The skill will:

1. Detect containerization state, service inventory (declared vs host-assumed vs external),
   config surface, and seed/migration hooks
2. Audit against the `H*` catalog, `file:line`-cited, each finding phrased as the collision or
   leak it causes
3. Interview: per-external mock/sandbox/accept decisions, resource budget, seed policy, and the
   no-Docker fallback
4. Implement: compose fixes (project `name:`, ephemeral ports, healthchecks, env'd secrets),
   `scripts/dev-stack.sh` (up/url/logs/list/down), and the seed hook that delegates to sim-data
5. Verify for real: N instances up simultaneously, cross-instance isolation proven with a
   write, exact teardown, measured cold-start — numbers in the report

The deliverable is the contract: `up <id>` → healthy seeded URL, every time, N at a time.
