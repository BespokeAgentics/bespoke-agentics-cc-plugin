# Isolated per-worktree test databases

## The goal
An agent working in a worktree should be able to run the app and be manually
tested **without any chance of touching the real dev database**. The way to
guarantee that: give each worktree its own *local* Postgres database and rewire
that worktree's env so the app, the migrator, and the test suite all point at it.

## Naming
Derived from the worktree directory name, sanitized, prefixed `cos_wt_`:

```
.../CUMULATIVE_OS-foundry-platform-port  ->  cos_wt_foundry_platform_port
```

Deterministic, so any script can recompute the same name from the path.
`wt-common.sh:wt_db_name` is the single source of truth — don't hardcode names.

## Local server
The isolated DBs live on a **local** Postgres, never the shared Azure server.
`wt-db.sh ensure-server` finds one at `WT_PG_BASE_URL`
(default `postgres://postgres:postgres@localhost:5432`) and, if absent, starts:
1. the repo's `infra/docker-compose.yml` if it defines a `postgres` service, else
2. a Homebrew `postgres` service, else
3. prints a `docker run … postgres:16` one-liner for the user.

Override the whole target with `WT_PG_BASE_URL` if the user runs Postgres
elsewhere (a different port, a container, etc.).

## Env wiring (the isolation guarantee)
`wt-db.sh provision` rewrites three keys in the worktree's `.env.local`:

| key                     | why |
|-------------------------|-----|
| `DATABASE_URL`          | the running app uses this — points at the isolated DB |
| `MIGRATION_DATABASE_URL`| `drizzle.config.ts` prefers this for migrate/generate |
| `TEST_DATABASE_URL`     | the repo's `db:test:reset` + test harness use this |

Because all three now resolve to `cos_wt_<slug>` on localhost, `bun run dev` in
that worktree physically cannot reach the Azure dev DB. That is the entire point.

> Guardrail: never rewrite these keys in the **primary** worktree, and never run
> a reset/drop whose resolved URL is the primary `DATABASE_URL`. See
> `guardrails.md`.

## Running the repo's own db scripts against the worktree DB
The repo already has good scripts; don't reimplement them — just force their DB
target via env on the command line:

```bash
# migrate the isolated DB
( cd apps/shell && MIGRATION_DATABASE_URL="$URL" DATABASE_URL="$URL" bunx drizzle-kit migrate )

# seed it
( cd apps/shell && DATABASE_URL="$URL" POSTGRES_SEED_ALLOWED=1 bun run db:seed )

# wipe it back to clean (uses TEST_DATABASE_URL path in db-reset.ts)
( cd apps/shell && TEST_DATABASE_URL="$URL" DATABASE_URL="$URL" POSTGRES_RESET_ALLOWED=1 bun run db:test:reset )
```

`wt-db.sh` wraps all three (`migrate` / `seed` / `reset`) so you get the env
forcing + guardrails for free.

## Lifecycle cheat-sheet
```bash
wt-db.sh ensure-server         # local Postgres reachable?
wt-db.sh provision <path>      # create db + wire .env.local   (idempotent)
wt-db.sh migrate   <path>      # drizzle-kit migrate onto it
wt-db.sh seed      <path>      # seed data
wt-db.sh reset     <path>      # wipe to clean test state
wt-db.sh url       <path>      # print connection string (psql / Studio / client)
wt-db.sh drop      <path>      # delete the db (refuses prod-looking names)
wt-db.sh status    <path>      # provisioned? name? url?
```

## Inspecting the data
```bash
psql "$(wt-db.sh url <path>)"                     # interactive
( cd apps/shell && DATABASE_URL="$(wt-db.sh url <path>)" bun run db:studio )   # Drizzle Studio
```
