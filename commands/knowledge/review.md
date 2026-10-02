---
name: "knowledge:review"
description: "Before starting a task: load the confirmed rules (which apply by default) and the testable hypotheses for the relevant domain, so the work that follows is informed and can confirm or contradict open hypotheses."
argument-hint: "[<task description>] [--domain <slug>]"
allowed-tools: Read, Glob, Grep, AskUserQuestion
---

> **How this command loads its skill.** `knowledge-loop` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/knowledge-loop/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Knowledge Loop — Review (before a task)

Orient before doing work. Surfaces what the project already knows about this domain so you apply
confirmed rules by default and know which hypotheses today's task could close out.

## Arguments

Parse from `$ARGUMENTS`:

```
[<task description>] [--domain <slug>]
```

- `<task description>` — free text about what you're about to do; used to infer the domain and to
  match hypotheses' `applies-when` triggers.
- `--domain <slug>` — operate on a specific domain instead of inferring.

## Process

Follow the `knowledge-loop` skill (loaded as described above) with `mode: review`. The skill:

1. Resolves the domain(s) from `--domain` or by inferring from the task and matching `INDEX.md`.
2. Reads that domain's `rules.md` and `hypotheses.md` and prints two short lists:
   - **Rules in effect** — apply these by default to the work that follows.
   - **Testable today** — hypotheses whose `applies-when` matches this task, so the work can add a
     confirmation (or a contradiction).
3. Flags any rule that appears to conflict with the task's intent (a demotion candidate).

Keep it brief — this is orientation at the *start* of work, not a report.

## Examples

```bash
/knowledge:review "drafting a 30% discount approval for Acme"   # infers the pricing domain
/knowledge:review --domain onboarding
```
