---
name: "agentnative:sim-data"
description: "Give agents realistic production-simulation data: mines the real shape of production via safe read-only aggregates (cardinality skew incl. the whale account, categorical frequencies, null rates, charset/text-length reality, temporal patterns, orphans/soft-deletes), then builds deterministic seed scenarios (default/demo/edge/load) — anonymized-subset pipelines via Greenmask or PostgreSQL Anonymizer with a named-human masking review gate where prod access exists, synthetic generators on @snaplet/copycat + seeded faker where it doesn't — wired into hermetic-deploy's seed hook, with double-seed determinism proofs and fidelity checks against the mined profile."
argument-hint: "[mode: plan|implement] [scenario: default|demo|edge|load|<custom>]"
allowed-tools: Skill(sim-data), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Sim Data

Run the `sim-data` skill: make the local instance's data statistically honest, deterministic,
and scenario-shaped.

## Arguments

Parse from `$ARGUMENTS`:

```
[mode: plan|implement] [scenario]
```

- `mode` (optional, default `implement`) — `plan` writes the data-shape profile + pipeline
  proposal to `./plans/`; `implement` interviews, then builds the seeds.
- `scenario` (optional) — build/rebuild a single scenario (`default`, `demo`, `edge`, `load`,
  or custom). Defaults to the set chosen in the interview.

## Process

Invoke the `sim-data` skill and forward `$ARGUMENTS`. The skill will:

1. Detect the data layer, existing fixtures and their lies, prod-access reality, and the
   PII/sensitivity map
2. Mine shapes with read-only aggregate queries — statistics cross the boundary, values don't;
   every shape marked `measured` (query shown) or `asserted` (source named)
3. Interview: pipeline (anonymized subset vs synthetic vs hybrid — with the named human
   reviewer for masking rules), scenario set, size budget, fidelity priorities
4. Build deterministic generators (copycat identities, seeded faker, distribution helpers
   implementing the profile) or the Greenmask/anon pipeline with deny-by-default column rules;
   wire `scripts/seed.sh` scenarios with manifests
5. Verify: double-seed byte-identical diff, distribution fidelity table vs the profile,
   app smoke on every scenario, anonymization post-scan with zero real-space hits

Avoid the corpses: Neosync is dead, @snaplet/seed is a zombie — the reference has the table.
