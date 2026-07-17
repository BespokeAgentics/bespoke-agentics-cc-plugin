# Guardrails (hard stops — these override full-auto behavior)

Full-auto means you don't ask permission for safe, reversible actions. It does
**not** mean these lines can be crossed. Each is enforced in the scripts; keep
them enforced if you ever act by hand.

## 1. Never run destructive DB ops against the primary database
The isolated test DB is always **local** and **per-worktree**
(`cos_wt_<slug>` on `WT_PG_BASE_URL`). Before any `reset`/`drop`, the resolved
URL is checked against the primary `DATABASE_URL`; if they match, refuse.
Never point `db:reset` / `db:test:reset` / `DROP DATABASE` at the shared Azure
`DATABASE_URL`. If you can't prove a DB URL is the local per-worktree one, stop.

## 2. Never delete a worktree with unsaved work
`wt-clean.sh` refuses when the worktree has:
- uncommitted changes (`git status --porcelain` non-empty), or
- commits not present on any remote (or no upstream at all).

Overriding requires **both** `--force` and a typed `--confirm <basename>`.
A single flag is never enough — losing an agent's unpushed work is unrecoverable.

## 3. Never touch anything that looks like production
Any database name or URL matching `/prod|production/i` is refused for
create/reset/drop. This repo currently has no separate prod DB, so this is
future-proofing — keep it.

## 4. Never delete an unmerged branch non-interactively
Branch deletion in `wt-clean.sh` only runs `git branch -d` (safe delete, merged
only). It never runs `-D`. If a branch isn't merged into base, it's kept and
reported.

## 5. Coordination state is shared, not per-worktree
The migration ledger lives in the git **common dir** so every worktree sees it.
Don't copy it into a single worktree or `.gitignore`-tracked path — that would
silently break collision prevention for the other worktrees.

## 6. Read before you write
`status` and `audit` are always safe and should be run first to orient. Mutating
actions assume you've already looked. If the state surprises you (e.g. a worktree
you didn't expect is dirty), surface it to the user instead of steamrolling.
