# Migration numbering, collisions, and merge order

## Why parallel branches collide
Drizzle names each migration `NNNN_slug.sql`, where `NNNN` is
`max(existing numbers on THIS branch) + 1`. drizzle-kit only sees the files
present in the current branch, so:

- production is at `0046`.
- Worktree A branches off, runs `db:generate` → makes `0047_a.sql`.
- Worktree B *also* branched off `0046`, runs `db:generate` → also makes `0047_b.sql`.

Both claim `0047`. Nothing complains until you merge the second branch, and then
you get a duplicate-number collision plus a corrupted `meta/_journal.json`
sequence. The fix is to make the *second* branch use `0048` — but you only know
that if you can see across worktrees.

## The shared ledger (prevention, preferred)
Every worktree of a repo shares one git **common dir**
(`git rev-parse --git-common-dir`). We keep a ledger there:

```
<common-dir>/worktree-ops/migration-ledger.tsv
  reserved_number <TAB> worktree_path <TAB> branch
```

Because it's in the shared dir, every worktree reads the same reservations.

- **`wt-migrations.sh reserve`** (run automatically by `wt-new.sh`) claims
  `global_high + 1`, where `global_high` = the max number found on disk in *any*
  worktree **or** already reserved in the ledger. So two worktrees created back
  to back get `0047` and `0048`, not two `0047`s.
- **`wt-migrations.sh claim`** — after the dev runs `db:generate` and drizzle
  emits (say) `0047_myslug.sql`, `claim` renames it to the reserved number
  (`0048_myslug.sql`) and patches `meta/_journal.json` (the `tag` and `idx`).
  Run `claim` immediately after every `db:generate` in a worktree.

  > Caveat worth surfacing to the user: drizzle also writes a snapshot JSON in
  > `meta/` keyed by index (e.g. `0047_snapshot.json`). `claim` patches the
  > journal's tag/idx; verify the snapshot filename/`idx` too and rename if
  > drizzle keyed it numerically. Always eyeball `git diff meta/_journal.json`.

## Auditing + merge order
`wt-migrations.sh audit` prints:
1. Every worktree's highest migration number, **ascending** — that ascending
   order is your safe merge order (lowest-numbered branch merges first, right
   after production).
2. **Collisions**: any two worktrees sharing the same max number. Resolve these
   (reserve + claim, or manual renumber) *before* merging, never during.
3. Current ledger reservations.

## Merge sequence, practically
1. `wt-migrations.sh audit` → read the ascending list.
2. Merge production-adjacent branches first, in ascending migration order.
3. After each merge, the next branch's reserved number is already higher, so it
   applies cleanly on top.
4. If two branches truly must both land and share a number, renumber the later
   one (`reserve` a fresh number for it, `claim`) before opening its PR.

## Manual renumber (no scripts)
If you ever need to do it by hand:
```bash
git mv apps/shell/drizzle/0047_foo.sql apps/shell/drizzle/0048_foo.sql
# edit apps/shell/drizzle/meta/_journal.json: bump that entry's "idx" 47 -> 48
#   and its "tag" 0047_foo -> 0048_foo
# rename the matching meta/0047_snapshot.json if present
```
Then `db:migrate` against a fresh isolated DB to confirm the chain applies.
