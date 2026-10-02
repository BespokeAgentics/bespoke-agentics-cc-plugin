---
name: "ontology:status"
description: "Ontology health at a glance: terms by kind and status, policy and overrides, open violations by rule (strict vs warn), proposed terms and aliases awaiting human approval, whether the write hook is installed, and any errors in ontology.yaml."
argument-hint: "[--banner]"
allowed-tools: Bash, Read
disable-model-invocation: true
---

> **How this command loads its skill.** `project-ontology` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/project-ontology/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Project Ontology — Status

Follow the `project-ontology` skill (loaded as described above) with `mode: status` and forward:

```
$ARGUMENTS
```

Runs `python3 .claude/ontology/ontology.py status` (`--banner` prints what the SessionStart hook shows).
Report in five lines: terms (approved / proposed / deprecated), policy, open violations by rule, what
awaits approval (suggest `/ontology:approve` for the most-used proposed values), and any ontology errors
or a missing hook.
