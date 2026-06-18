---
name: "disclosure:refresh"
description: "Re-run progressive disclosure to update only the managed sections of an existing context layer. Rewrites content inside the progressive-disclosure:managed sentinels (refreshed commands, stack, conventions) and adds files for newly-discovered subsystems, while leaving hand-written sections and unmanaged files untouched. Use to keep CLAUDE.md/AGENTS.md current as the code evolves."
argument-hint: "[<root>] [--depth subsystem|diverge|deep] [--no-wiki]"
allowed-tools: Skill(progressive-disclosure), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Progressive Disclosure — Refresh

Keep an existing context layer current after the code has moved on. Same scan-and-synthesize
pipeline as `/disclosure:map`, but the apply step is surgical: it only rewrites content
**inside** the `progressive-disclosure:managed` sentinels and creates files for subsystems
that didn't exist last time. Hand-written prose outside the sentinels — and any file the
skill doesn't manage — is left exactly as is.

## Arguments

```
[<root>] [--depth subsystem|diverge|deep] [--no-wiki]
```

Same meanings as `/disclosure:map`.

## Process

Invoke the `progressive-disclosure` skill with `mode: refresh` and forward `$ARGUMENTS`. The
skill scans (parallel subagents), diffs the freshly-synthesized managed blocks against the
current ones, and presents a plan limited to:

- **UPDATE** — managed blocks whose content changed (stale command, new dependency, moved path).
- **CREATE** — `CLAUDE.md`/`AGENTS.md` for subsystems added since the last run.
- **SKIP** — everything already current, and all unmanaged content.

It then applies on approval and re-verifies. Files with no managed sentinel are reported but
**not** rewritten (use `/disclosure:map` to bring them under management).

## When to use which

- `/disclosure:map` — first-time setup, or a structural overhaul.
- `/disclosure:refresh` — routine upkeep; safest re-run.
- `/disclosure:audit` — check health without writing.

## Examples

```bash
/disclosure:refresh
/disclosure:refresh --depth subsystem
```
