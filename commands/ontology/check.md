---
name: "ontology:check"
description: "Check pages against the ontology with the same rules the write hook runs: unregistered, misspelled, deprecated or proposed values; broken, ambiguous or noncanonical [[links]]; relation range. One page, the whole vault (--all), or only what changed since a git ref (--changed-since, the CI ratchet). Exit 1 on strict violations."
argument-hint: "[<path>...] [--all] [--changed-since <ref>] [--format text|json|lint] [--strict-only]"
allowed-tools: Skill(project-ontology), Bash, Read
---

# Project Ontology — Check

Invoke the `project-ontology` skill with `mode: check` and forward:

```
$ARGUMENTS
```

Runs `python3 .claude/ontology/ontology.py check …`. Report the counts by rule (strict / warn), then at
most ten violations that matter with their suggestions. Do not "fix" values you are not sure of — an
unregistered value is a question for the user or a `/ontology:propose`, not a guess. Mechanical cases
(aliases, spelling variants, deprecated values with a replacement, noncanonical links) go to
`/ontology:apply --dry-run`.
