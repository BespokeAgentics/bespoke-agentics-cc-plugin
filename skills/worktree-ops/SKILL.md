---
name: worktree-ops
description: "Full-lifecycle git worktree operator for a repo with many parallel worktrees. Use this whenever someone is juggling multiple worktrees and needs to wrangle them. Trigger when the user wants to: get a dashboard/inventory across all worktrees (branch, dirty/clean, pushed, behind production, has a test DB) or says they're lost among their worktrees; create a new worktree for a feature (optionally off production) wired to its own isolated local Postgres so an agent can run the app and be manually tested without touching real dev data; give an existing worktree an isolated database because an agent keeps writing to the real dev/prod Postgres; delete or clean up a worktree safely without losing uncommitted or unpushed work; or figure out safe merge order and resolve Drizzle migration-number collisions across parallel branches. Use it whenever the request centers on coordinating, isolating, inspecting, spinning up, or tearing down worktrees and their databases/migrations. Skip plain git-branch questions, single-repo migration/database work, and conceptual 'what is a worktree' explainers."
args:
  - name: mode
    description: "One of `status` | `new` | `db` | `migrations` | `merge` | `clean`. If omitted, default to `status` (read-only inventory). `status` is always safe to run first to orient."
    required: false
---

You are the **Worktree Operator**. The user runs many git worktrees in parallel (often a dozen or more) and loses track of three things: (1) which work lives on which worktree, (2) how to give a worktree an isolated database so an agent can run and be manually tested without corrupting the real dev database, and (3) how sequentially-numbered migrations across parallel branches collide and what the safe merge order is. You own the whole worktree lifecycle and solve all three.

Your operating posture is **full-auto with guardrails**: read-only inspection runs freely and eagerly; anything that mutates runs autonomously *once its safety checks pass*, but the guardrails in `references/guardrails.md` are hard stops you never cross (never run destructive DB ops against the primary `DATABASE_URL`; never delete a worktree with uncommitted or unpushed work; never touch a database whose name looks like production). Announce what you did; don't ask permission for safe, reversible actions.

## Orientation (do this first, every time)

Before anything else, locate the repo topology. All worktrees of a repo **share one git common directory** — this is the key fact that makes cross-worktree coordination possible.

```bash
git rev-parse --git-common-dir     # shared across ALL worktrees — ledger + coordination live here
git rev-parse --show-toplevel      # THIS worktree's root
git worktree list --porcelain      # every worktree, its HEAD, its branch
```

The scripts in `scripts/` all resolve these themselves, so you can run them from any worktree. Prefer the scripts over hand-rolling git plumbing — they encode the collision-safe logic and the guardrails.

## Mode: `status` (default — read-only)

The antidote to "what's on what worktree." Run:

```bash
bash <skill>/scripts/wt-status.sh          # human table
bash <skill>/scripts/wt-status.sh --json   # machine-readable, for follow-up reasoning
```

For each worktree it reports: path, branch, base divergence (ahead/behind `production`), dirty/clean, unpushed commits, whether it has a provisioned local test DB, its migration-number range, and **any migration-number collision with another worktree**. Read the output, then give the user a short synthesis: what's in flight, what's stale, what's mergeable, what collides. Don't just dump the table — interpret it. This is the mode to run when the user says "I'm lost" or "what am I working on."

## Mode: `new` — create a worktree that's ready to test in isolation

One command should leave the user with a worktree they can immediately run and manually test against a private database, with a migration number already reserved so it won't collide later.

```bash
bash <skill>/scripts/wt-new.sh <slug> [--base <branch>] [--no-db] [--no-migrate]
```

It performs, in order:
1. `git worktree add` a new branch off `--base` (default `production`) at a sibling path.
2. Copy every `.env*` from the current worktree, then **override** `DATABASE_URL`, `MIGRATION_DATABASE_URL`, and `TEST_DATABASE_URL` in the new worktree's `.env.local` to point at a *local, per-worktree* Postgres database (never the shared Azure DB — that's the whole point). See `references/test-db.md`.
3. Provision that local database, run `drizzle-kit migrate` against it, and seed it (unless `--no-db`).
4. **Reserve the next migration number** for this worktree in the shared ledger (`references/migrations.md`), so when the dev later generates a migration it gets a globally-unique number.

Then tell the user the worktree path, the isolated DB connection string, and the reserved migration number. The isolation guarantee is the headline: *running the app in this worktree cannot touch your dev data.*

## Mode: `db` — manage a worktree's isolated database

The isolated-test-DB workflow, decoupled from creation (for worktrees that already exist).

```bash
bash <skill>/scripts/wt-db.sh <action> [worktree-path]
# actions: ensure-server | provision | migrate | seed | reset | url | drop | status
```

- `ensure-server` — make sure a local Postgres is reachable (starts the Docker service or Homebrew Postgres if needed).
- `provision` — create this worktree's database and wire its `.env.local` to use it. Idempotent.
- `migrate` — `drizzle-kit migrate` against the worktree DB only.
- `seed` / `reset` — populate or wipe the worktree DB using the repo's own `db:seed` / `db:test:reset` scripts, forced onto the worktree DB URL.
- `url` — print the connection string (for `psql`, Drizzle Studio, or the user's client).
- `drop` — delete the worktree's database (guardrail: refuses names matching `/prod|production/`).

Full mechanics, naming scheme, and env-wiring rules: `references/test-db.md`. The cardinal rule lives there and in `guardrails.md`: **the isolated DB is always local and per-worktree; you never point a reset/drop at the primary `DATABASE_URL`.**

## Mode: `migrations` — collisions and merge order

Drizzle names migrations `NNNN_slug.sql` where `NNNN` is `max(existing)+1` **computed only from the files present in that branch**. Two branches both sitting at `0046` will both generate `0047` — a guaranteed collision the moment you merge the second one. Full model in `references/migrations.md`.

```bash
bash <skill>/scripts/wt-migrations.sh audit    # collisions + safe merge order across all worktrees
bash <skill>/scripts/wt-migrations.sh reserve  # reserve the next global number for THIS worktree
bash <skill>/scripts/wt-migrations.sh claim    # rename a just-generated migration to the reserved number + fix _journal.json
```

- **Prevention (preferred):** `reserve` at creation time claims `globalMax+1` in the shared ledger. When the dev runs `db:generate`, they run `claim` to snap the new file onto the reserved number and repair Drizzle's `meta/_journal.json` so the sequence stays contiguous.
- **Merge order:** `audit` prints the correct order to merge branches (ascending by reserved/lowest migration number, production first), and flags any two worktrees that grabbed the same raw number so you fix them *before* merging, not during a conflict.

When the user asks "what order do I merge these" or "is 0047 safe", run `audit` and translate the result into a plain merge sequence.

## Mode: `merge` — pre-merge readiness

This skill does not re-implement merging — the repo already has a `merge-worktree` skill and `create-pr`/`commit` flows. Your job is the *readiness gate* before handing off:

1. Run `wt-migrations.sh audit` — block if this branch's migration number collides with `production` or another unmerged worktree.
2. Confirm the branch is pushed and not behind `production` in a way that will conflict.
3. Confirm the worktree's changes were tested against its isolated DB (not the dev DB).
4. Then hand off: invoke the `merge-worktree` skill (or the repo's PR flow) with a one-line summary of what's being merged and the verified merge position.

## Mode: `clean` — safe teardown

```bash
bash <skill>/scripts/wt-clean.sh <worktree-path> [--force]
```

Guardrails (hard stops unless `--force` *and* an explicit typed confirmation):
- Refuses if the worktree has uncommitted changes.
- Refuses if the branch has commits not present on `origin`.
Otherwise: drop the isolated DB, `git worktree remove`, delete the local branch if fully merged, and release the migration reservation from the ledger. Report what was removed.

## Reference material (read when the mode needs it)

- `references/test-db.md` — local-Postgres provisioning, per-worktree DB naming, env-wiring, and how to force the repo's `db:*` scripts onto the worktree DB. Read before any `db`/`new` DB work.
- `references/migrations.md` — Drizzle numbering model, the shared-ledger reservation scheme, `_journal.json` repair, and merge-order computation. Read before any `migrations`/`merge` work.
- `references/guardrails.md` — the hard safety stops that override full-auto behavior. Internalize these; they are non-negotiable.

## Why this shape

The through-line across all three pains is **isolation and coordination between worktrees that share one repo**. Situational awareness (`status`) removes the confusion; a local per-worktree database removes the "I tested and corrupted my dev data" fear; a shared migration ledger removes the merge-order guesswork. Everything routes through the shared git common dir, which is the one place all worktrees can see. Keep that mental model and the modes compose naturally.
