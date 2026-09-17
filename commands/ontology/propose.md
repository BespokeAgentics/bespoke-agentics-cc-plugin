---
name: "ontology:propose"
description: "Register a new ontology term (status: proposed) — a vocabulary value (<type>.<field>.<value>), entity (<namespace>.<slug>), tag (tag.<path>), relation (rel.<name>) or type (type.<name>) — or propose aliases for an existing term. A definition is required. Proposed terms are usable immediately and flagged until a human approves them."
argument-hint: "<id> --label '<label>' --definition '<meaning>' [--value <exact spelling>] [--alias <spelling>]... [--before <id>|--after <id>] [--bind] [--source <page>]"
allowed-tools: Skill(project-ontology), Bash, Read
---

# Project Ontology — Propose

Invoke the `project-ontology` skill with `mode: propose` and forward:

```
$ARGUMENTS
```

Runs `python3 .claude/ontology/ontology.py propose …`, re-renders `ONTOLOGY.md` and logs to
`wiki/_log.md`. Use this when a page genuinely needs a value the vocabulary lacks — never pick a
near-synonym of an approved value to get past the write hook. `--value` carries the exact page spelling
when it differs from the id leaf (`P0`, `🟡`); `--before`/`--after <sibling-id>` places it in a ranked vocabulary (`urgent` before `critical`); `--bind` is required to put a not-yet-controlled field
under control (say so to the user). Report the id, kind and status, and remind the user it awaits their
approval (`/ontology:approve`).
