---
name: "bespokeagentics:worktree-ops"
description: "Full-lifecycle git worktree operator. Inventory every worktree (branch, base divergence, dirty/unpushed, isolated test-DB status, migration range, cross-worktree migration collisions), create a worktree that's immediately testable in isolation (its own local per-worktree Postgres so the agent can run the app without touching your dev DB), reserve collision-free Drizzle migration numbers via a shared ledger, compute safe merge order, and safely tear worktrees down. Default mode is read-only `status`."
argument-hint: "[mode: status|new|db|migrations|merge|clean] [args...]"
allowed-tools: Skill(worktree-ops), Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# Worktree Ops

Run the `worktree-ops` skill to manage git worktrees end to end: situational
awareness, isolated per-worktree test databases, and migration-collision-free
merge ordering.

## Arguments
- **mode** (optional, default `status`): `status` | `new` | `db` | `migrations` | `merge` | `clean`
- Remaining args pass through to the mode (e.g. a slug for `new`, an action for `db`, a path for `clean`).

## Behavior
Invoke the `worktree-ops` skill with the given mode. If no mode is provided,
run `status` (read-only inventory) and synthesize what's in flight, what's
stale/mergeable, and any migration collisions. Follow the skill's guardrails:
read-only inspection runs freely; mutating actions run full-auto only once their
safety checks pass, and never cross the hard stops (no destructive ops against
the primary `DATABASE_URL`; no deleting worktrees with uncommitted/unpushed work).

## Examples
- `/bespokeagentics:worktree-ops` — inventory all worktrees + collision report
- `/bespokeagentics:worktree-ops new invoice-export` — create an isolated, testable worktree
- `/bespokeagentics:worktree-ops db reset` — wipe this worktree's test DB to clean state
- `/bespokeagentics:worktree-ops migrations audit` — safe merge order + collision check
- `/bespokeagentics:worktree-ops clean ../CUMULATIVE_OS-old-experiment` — guarded teardown
