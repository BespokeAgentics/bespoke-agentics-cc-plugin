---
name: "funcspec-plan"
description: "Validate funcspec findings with the user and generate the implementation plan. Runs the Stage-2 validation interview (confirm features, resolve ambiguities, set priorities), then writes the functional spec, implementation plan, backlog-ready epics/stories, gap register, and traceability matrix. Ingests into the wiki when present and offers Jira/Confluence/Linear push when MCPs are connected. Runs funcspec-evaluate first if no profiles exist."
argument-hint: "[<workspace>] [--out <dir>] [--push ask|none]"
allowed-tools: Skill(funcspec), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Funcspec — Plan

Run Phases 5–7 of the `funcspec` skill: Stage-2 validation interview → deliverables →
wiki ingestion + integration offers. If `<out>/profiles/` is missing or empty, run the
full pipeline (Phases 0–4 first).

## Arguments

Parse from `$ARGUMENTS`:

```
[<workspace>] [--out <dir>] [--push ask|none]
```

- `<workspace>` (optional) — Storybook workspace root; defaults to auto-detection in CWD.
- `--out` — funcspec state directory. Default `<workspace>/docs/funcspec`.
- `--push` — `ask` (default) offers push to connected Jira/Confluence/Linear MCPs;
  `none` writes files only.

## Process

Invoke the `funcspec` skill in **plan** mode and forward `$ARGUMENTS`.

The skill will:

1. **Load state** — `synthesis.json` + profiles from `--out`; run evaluate phases first
   if absent.
2. **Interview (Stage-2)** — AskUserQuestion batches: confirm/correct/cut features per
   domain, resolve every blocking ambiguity (defer non-blocking to ⚪), capture
   P0/P1/P2 priorities and phasing constraints. Nothing unvalidated enters the plan.
3. **Generate deliverables (ultracode)** — four parallel `deliverable-writer` agents
   draft `functional-spec.md`, `implementation-plan.md`, `backlog.md`, and
   `gap-register.md` (🟢🔵🟡🔴⚪🟣) simultaneously from the validated synthesis;
   `traceability.md` is generated main-thread, followed by a cross-document
   consistency check (id joins, priority agreement, writer flags).
4. **Wiki + push** — ingest into `wiki/` per the wiki-first mandate when a vault exists;
   detect connected Atlassian/Linear MCPs and offer (never auto) pushing epics/stories
   and the plan page.
5. **Verify** — every story traces to an affordance, blocking ambiguities resolved,
   deferred ones in the gap register, schema-valid profiles, all features prioritized.
   Failures reported honestly; an unverified plan is labeled a draft.

## Output

Five deliverables in `<out>/`, wiki pages when applicable, optional Jira/Confluence
artifacts, and a closing summary (features confirmed/cut, ambiguities resolved/deferred,
paths, push actions).
