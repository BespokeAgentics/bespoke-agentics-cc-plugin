---
name: "agentnative:proof-of-work"
description: "Give coding agents the means to prove their work: installs agent-browser (accessibility-tree snapshots, annotated screenshots, console/network checks, baseline pixel/structural diffs) or wires Playwright's screenshot/trace CLIs where Playwright is incumbent, establishes an evidence/ directory convention with a machine-readable manifest, sets up storage (S3/R2 presigned URLs for inline PR images, Actions artifacts v4 for traces), and a create-or-update PR evidence comment — so every UI claim ships with before/after pixels, a mechanical check, and a repro command."
argument-hint: "[mode: plan|implement] [scope: local|ci|both]"
allowed-tools: Skill(proof-of-work), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Proof of Work

Run the `proof-of-work` skill: build the evidence chain from capture to PR comment, then prove
it end-to-end once.

## Arguments

Parse from `$ARGUMENTS`:

```
[mode: plan|implement] [scope: local|ci|both]
```

- `mode` (optional, default `implement`) — `plan` writes the evidence-stack proposal to
  `./plans/proof-of-work.md`; `implement` interviews, installs, and wires it.
- `scope` (optional, default `both`) — `local` = agent-side tooling + conventions only; `ci` =
  CI capture, storage, and PR comments only.

## Process

Invoke the `proof-of-work` skill and forward `$ARGUMENTS`. The skill will:

1. Detect the UI stack, existing capture tooling (reuse Playwright/Chromatic rather than
   duplicate), storage availability, and where agents run
2. Interview: storage target, evidence classes, baseline policy (CI-captured from main vs
   committed goldens), and the privacy line for uploaded pixels
3. Install capture tooling and write `scripts/evidence.sh` + the `evidence/` convention with
   manifest; document it in CLAUDE.md/AGENTS.md so agents discover it
4. Wire CI: bucket upload with presigned URLs, artifact upload for traces, a single
   create-or-update evidence comment per PR, baseline job on main
5. Verify the whole chain once for real: capture → upload → inline render in a throwaway PR,
   plus a determinism check (unchanged app diffs clean)

The evidence contract: every claim ships the artifact, the mechanical check's quoted output, and
the command a human runs to see it live.
