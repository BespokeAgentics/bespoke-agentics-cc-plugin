---
name: "ontology:deprecate"
description: "Retire an ontology term — a human gate. Names the replacement (same kind, same parent) and the reason; pages still using the term are flagged value-deprecated, and /ontology:apply rewrites them to the replacement. Also how a rejected proposal is recorded."
argument-hint: "<id> [--replaced-by <id>] --reason '<why>'"
allowed-tools: Skill(project-ontology), AskUserQuestion, Bash, Read
---

# Project Ontology — Deprecate

Invoke the `project-ontology` skill with `mode: deprecate` and forward:

```
$ARGUMENTS
```

Confirms with you first (`AskUserQuestion`: the term, its definition, how many pages use it, the
proposed replacement), then runs `deprecate <id> --replaced-by <id> --reason "…" --by "<your name>"`
(permission prompt from the Bash guard). If pages use the term and a replacement exists, it offers
`/ontology:apply --dry-run`. Terms are never deleted — the history stays in `ontology.yaml` and
`wiki/_log.md`.
