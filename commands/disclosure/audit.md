---
name: "disclosure:audit"
description: "Read-only health check of an existing CLAUDE.md / AGENTS.md / .claude/settings.json context layer. Flags missing per-subsystem files, stale commands, broken AGENTS.md pointers, drifted or missing managed sentinels, settings gaps (deny rules, additionalDirectories), and uninstalled code-intelligence recommendations. Writes nothing; recommends /disclosure:map to fix."
argument-hint: "[<root>] [--depth subsystem|diverge|deep]"
allowed-tools: Skill(progressive-disclosure), Agent, Bash, Read, Glob, Grep
---

# Progressive Disclosure — Audit

Assess the health of a repo's context layer **without writing anything**. Useful before a
big change, during onboarding, or on a cadence to catch drift between the code and its
memory files.

## Arguments

```
[<root>] [--depth subsystem|diverge|deep]
```

- `<root>` (optional) — defaults to git root, else CWD.
- `--depth` (optional) — the granularity to judge coverage against (default `subsystem`).

## Process

Invoke the `progressive-disclosure` skill with `mode: audit` and forward `$ARGUMENTS`. The
skill runs Phases 0–2 only (inventory + parallel scan + synthesis) and then reports instead
of planning writes. It checks:

- **Coverage** — does every subsystem that should have a `CLAUDE.md` (per `--depth`) have one? Any orphan files for subsystems that no longer exist?
- **Freshness** — do documented build/test/lint commands still match the manifests? Any referenced paths that have moved?
- **Pointers** — does every `AGENTS.md` resolve to a real sibling `CLAUDE.md`?
- **Sentinels** — is the `progressive-disclosure:managed` block present and balanced in each managed file?
- **Settings** — are there checked-in generated/vendored paths with no `Read` deny rule? Cross-package imports with no `additionalDirectories`? A registered SessionStart hook?
- **Code intelligence** — languages present with no recommended LSP plugin noted.

## Output

A severity-tagged report (🔴 broken / 🟡 drifted / 🟢 healthy) grouped by area, ending with
the single recommended next step — usually `/disclosure:map` (full fix) or `/disclosure:refresh`
(managed-section update only).

## Examples

```bash
/disclosure:audit
/disclosure:audit /Users/me/Projects/acme-monorepo --depth diverge
```

This command **writes nothing** — always safe to run.
