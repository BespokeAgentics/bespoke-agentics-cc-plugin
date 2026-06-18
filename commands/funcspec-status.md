---
name: "bespokeagentics:funcspec-status"
description: "Show the state of a funcspec run: pages inventoried vs. profiled vs. visually verified, open/resolved/deferred ambiguities (blocking flagged), synthesis freshness, and which deliverables exist. Read-only."
argument-hint: "[<workspace>] [--out <dir>]"
allowed-tools: Bash, Read, Glob, Grep
---

# Funcspec — Status

Read-only report on funcspec state. No skill invocation needed — inspect the state
directory directly.

## Arguments

Parse from `$ARGUMENTS`:

```
[<workspace>] [--out <dir>]
```

Default `--out` is `<workspace>/docs/funcspec` (workspace auto-detected from CWD).

## Process

1. If `<out>/` is missing, report "no funcspec run found" and point to
   `/bespokeagentics:funcspec-evaluate`.
2. Read `page-inventory.json`, `profiles/*.json`, `synthesis.json`, and list which of
   the five deliverables exist (`functional-spec.md`, `implementation-plan.md`,
   `backlog.md`, `gap-register.md`, `traceability.md`).
3. Report:

```
FUNCSPEC STATUS — <workspace>
Inventory:     <n> pages, <m> composites (fast path: yes/no)
Profiled:      <x>/<n+m>   visually verified: <v>
Ambiguities:   <open> open (<blocking> blocking) · <resolved> resolved · <deferred> deferred
Synthesis:     <present + mtime | missing>  <stale warning if any profile is newer>
Deliverables:  <list with ✓/✗>
Next step:     <funcspec-evaluate | funcspec-plan | re-run plan after resolving blockers>
```

4. If any profile fails a quick schema sanity check (missing required keys), flag it.
