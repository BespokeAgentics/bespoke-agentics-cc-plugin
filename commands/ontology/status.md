---
name: "ontology:status"
description: "Ontology health at a glance: terms by kind and status, policy and overrides, open violations by rule (strict vs warn), proposed terms and aliases awaiting human approval, whether the write hook is installed, and any errors in ontology.yaml."
argument-hint: "[--banner]"
allowed-tools: Skill(project-ontology), Bash, Read
---

# Project Ontology — Status

Invoke the `project-ontology` skill with `mode: status` and forward:

```
$ARGUMENTS
```

Runs `python3 .claude/ontology/ontology.py status` (`--banner` prints what the SessionStart hook shows).
Report in five lines: terms (approved / proposed / deprecated), policy, open violations by rule, what
awaits approval (suggest `/ontology:approve` for the most-used proposed values), and any ontology errors
or a missing hook.
