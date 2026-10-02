---
name: "glean:doctor"
description: "Triage a Glean agent project — checks Python version, installed extras, env vars, project structure, and framework consistency. Reports only; never auto-installs."
argument-hint: "[--probe]"
allowed-tools: Bash, Read, Grep, Glob
disable-model-invocation: true
---

> **How this command loads its skill.** `glean-agent-toolkit` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/glean-agent-toolkit/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Glean Doctor

Diagnose a Glean Agent Toolkit project. **Reports only — never auto-installs.** All fixes are printed as exact commands the user can run.

## Arguments

Parse from `$ARGUMENTS`:

```
[--probe]
```

- `--probe` — additionally run a live API ping against Glean (consumes API quota; off by default)

## Process

Follow the `glean-agent-toolkit` skill (loaded as described above) with `mode: doctor` and forward `$ARGUMENTS`.

The skill will check, in order:

1. Python version ≥ 3.10
2. `glean-agent-toolkit` installed; report version
3. Framework extras importable (`openai_agents`, `langchain_core`, `google.adk`)
4. `GLEAN_API_TOKEN` set
5. `GLEAN_SERVER_URL` or `GLEAN_INSTANCE` set
6. `pyproject.toml` exists at CWD
7. At least one `agent_*.py` exists in `src/`
8. Framework consistency (extras declared but no matching agent file → warn)

If `--probe`, additionally:

9. Live `GleanContext().get_client()` call to verify creds + connectivity

Output is a green/yellow/red checklist. Each red includes a fix recipe pointing to `references/troubleshooting.md`.

If a `wiki/` directory exists at the repo root, append a single-line entry to `wiki/_log.md`.

## Examples

```
/glean:doctor
/glean:doctor --probe
```
