---
name: "agentnative:fast-ci"
description: "Make CI blazing fast so coding agents can verify their work in seconds: audit the repo's toolchain against the native-rewrite catalog (TypeScript 7 native tsc, oxlint/oxfmt, uv, ruff, Biome, bun test), measure baseline timings, then — gated behind an interview — swap tools with official migrators and restructure the pipeline into a <3-minute fast lane (pull_request + merge_group) with integration/E2E tests moved to the merge queue or post-merge with a failure playbook. Before/after timings prove the win."
argument-hint: "[mode: audit|implement|audit-and-implement] [path]"
allowed-tools: Skill(fast-ci), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Fast CI

Run the `fast-ci` skill: measure the verification loop, swap slow tools for their Rust/Zig/Go-
native replacements, and split the pipeline into fast pre-merge and heavy post-merge lanes.

## Arguments

Parse from `$ARGUMENTS`:

```
[mode: audit|implement|audit-and-implement] [path]
```

- `mode` (optional, default `audit-and-implement`) — `audit` writes the read-only report only;
  `implement` applies swaps from an existing `./fast-ci-audit.md`; `audit-and-implement` audits,
  interviews, then implements.
- `path` (optional) — scope to a workflow file, package, or subtree.

## Process

Invoke the `fast-ci` skill and forward `$ARGUMENTS`. The skill will:

1. Detect languages, tools, CI provider, and blockers (Volar/TS7, plugin gaps)
2. Measure baseline timings from CI history and local runs — no unmeasured optimization
3. Audit against the `TC*` swap catalog and `LN*` lane rules, `file:line`-cited
4. Interview: appetite (swaps / lanes / both), per-swap confirmation, post-merge failure policy
5. Implement smallest-reversible-diff-first; reformats committed separately with
   `.git-blame-ignore-revs`
6. Verify with before/after timings, double-format stability check, and `zizmor` on touched
   workflows

The prize is one number: `git push` → green check. The report must show it before and after.
