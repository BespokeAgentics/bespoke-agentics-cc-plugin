---
name: "ontology:approve"
description: "Approve proposed ontology terms (and their proposed aliases) — a human gate. Lists what is pending with definitions and page counts, confirms each group with you, then records who approved it. Globs allowed ('tag.*')."
argument-hint: "[<id|glob>...] [--aliases-only]"
allowed-tools: Skill(project-ontology), AskUserQuestion, Bash, Read
---

# Project Ontology — Approve

Invoke the `project-ontology` skill with `mode: approve` and forward:

```
$ARGUMENTS
```

Approval is yours, not the agent's. The skill lists pending terms (`status`, `ls --status proposed`) with
definitions and usage counts, asks you with `AskUserQuestion` (approve · deprecate in favour of an
approved value · leave proposed), then runs `approve <ids> --by "<your name>"` — the Bash guard raises a
permission prompt as a second check. Deprecations chosen here continue with `/ontology:deprecate`, and
`/ontology:apply` when pages need rewriting. See `skills/project-ontology/references/governance.md`.
