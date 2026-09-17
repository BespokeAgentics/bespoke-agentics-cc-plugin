---
name: "db:query"
description: "Answer a question about the project with SQL against the project database — read the schema, run one guarded read-only SELECT (row cap, timeout, CSV), open the source pages for context, cite them. Accepts raw SQL or a natural-language question."
argument-hint: "'<question or SELECT …>' [--format csv|json|md] [--limit <n>] [--remote] [--explain]"
allowed-tools: Skill(project-db), Bash, Read, Glob, Grep
---

# Project DB — Query

Invoke the `project-db` skill with `mode: query` and forward:

```
$ARGUMENTS
```

If the argument is SQL, run it as-is through `python3 .claude/db/db.py query "<sql>"`. If it is a
question, first read `.claude/db/SCHEMA.md`, pick the typed or curated view that matches, write ONE
statement, run it, and open the page(s) at `pages.path` for narrative context before answering.
Errors from the guardrails (one statement, SELECT only, timeout, TRUNCATED) are corrections: narrow
the query; never disable the caps.

Answer with: the result (aggregated, never hundreds of rows), the query in one fenced block, and the
pages to open. If the same multi-table query has now come up more than once, propose adding it to
`.claude/db/views.sql`.

Full-text shortcut: `python3 .claude/db/db.py search "<terms>" [--type gap] [--raw]`.
See `skills/project-db/SKILL.md` § query.
