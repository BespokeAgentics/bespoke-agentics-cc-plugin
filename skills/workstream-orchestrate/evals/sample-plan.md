# Plan: Archived projects are hidden from the default list

<!-- Eval fixture for workstream-orchestrate. A small, structured plan (3 workstreams, locked
     decisions, one server-authoritative hard gate) so a `--dry-run` can exercise Phase A end to end. -->

status: ready

## Context

Projects can be archived, but the default project list still shows them, cluttering the view. We add
an `archived_at` timestamp, exclude archived projects from the default server-side list, and prove a
client cannot bypass the exclusion. Archiving is reversible — un-archiving restores the project with
its data intact.

## Locked decisions

- **D1** — `archived_at timestamptz null` column on `projects` (a timestamp, not a boolean, so we
  keep *when* it was archived). Postgres only.
- **D2** — The default `listProjects()` excludes archived projects **server-side**. `includeArchived`
  is honored only for an authorized caller (admin/owner scope).
- **D3** — Archiving never deletes rows. Un-archiving (`archived_at = null`) restores the project and
  all related data unchanged.

## Gates

- `bun run typecheck`
- focused tests for the touched files (e.g. `bun test src/lib/projects/list.test.ts`)
- `bun run build`
- WS-1 (schema): `bun run db:generate` + `bun run db:migrate` against an **isolated/disposable** DB
  only, then reseed.

## Guardrails

- Postgres only; new schema in `src/lib/persistence/schema.ts`.
- Root lockfile is the only lockfile; never add a child lockfile.
- Conventional Commits — one per validated workstream.

## Workstreams

- **WS-0 — Drift fix.** Remove the dead `showArchived` client-only filter flag.
  Seam: `src/lib/projects/ProjectList.tsx`.
- **WS-1 — Schema + migration.** Add `archived_at` to `projects`; generate + run the migration
  against a disposable DB; backfill existing rows to `null`.
  Seams: `src/lib/persistence/schema.ts`, `drizzle/`.
- **WS-2 — Server-side resolution + hard gate.** `listProjects()` excludes archived unless an
  authorized `includeArchived` is passed; enforce at the query, not the client.
  Seam: `src/lib/projects/list.ts`.

## Hard gates

- **HG-1** — A crafted client request with `includeArchived=true` from an **unauthorized** user
  cannot surface archived projects. Enforced at `src/lib/projects/list.ts::listProjects` (the query
  builder), not client filtering. Proof: call `listProjects({ includeArchived: true, scope: 'member' })`
  directly and assert archived rows are absent from the result.

## Verification (Definition of done)

- All three workstreams committed and green.
- HG-1 proved with an artifact (a focused test against `listProjects`).
- **Hide → restore round-trip:** archiving a project removes it from the default list without
  deleting the row; un-archiving restores it with related data intact.
