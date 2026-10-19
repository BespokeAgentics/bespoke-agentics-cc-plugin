# Disposition rubric

Every ledger row receives exactly one of five dispositions. The rubric is applied in order; the
first rule that matches wins. Inputs are the ledger columns: **serves-core** (✅ / 🟡 / ❌),
**state** (`done` · `in-progress` · `stubbed` · `planned` · `abandoned`), **distance** (S/M/L/XL),
and **disable-cost** (`flag` · `route` · `nav` · `label` · `entangled`).

## The rules

| # | If | Then | Because |
|---|---|---|---|
| 1 | state `done` and serves ✅ | **Finish** (distance S — verify it, write the acceptance line) | It is the product. |
| 2 | state `done` and serves 🟡 | **Finish** (S) — but it is **contested**; ask | It costs nothing to keep and something to explain. The user decides whether it muddies the story. |
| 3 | state `done` and serves ❌ | **Disable** if disable-cost ≤ `nav`, else **Finish** (S) and mark contested | Finished work that distracts from the core is better hidden than deleted — unless hiding it is the expensive path. |
| 4 | state `planned` or `abandoned` and serves ❌ | **Cut** | It was never built and does not serve the product. Remove the promise. |
| 5 | state `planned` or `abandoned` and serves ✅ / 🟡 | **Defer** | It belongs on the roadmap, written now while the intent is fresh. |
| 6 | state `in-progress` or `stubbed`, serves ❌ | **Disable** if disable-cost ≤ `nav`; **Cut** if `entangled` and distance ≥ L | Half-built and off-core: hide it cheaply, or delete it if hiding costs more than the code is worth. |
| 7 | state `in-progress` or `stubbed`, serves ✅, distance S or M | **Finish** | Core and close. |
| 8 | state `in-progress` or `stubbed`, serves ✅, distance L | **Finish** if the arithmetic has room, else **Trim** — contested either way | Core but expensive; the calendar decides. |
| 9 | state `in-progress` or `stubbed`, serves ✅, distance XL | **Trim** — the shippable slice is Finish, the rest Defer | XL is by definition unplanned work; shipping all of it on a date is a guess. |
| 10 | state `in-progress` or `stubbed`, serves 🟡 | **Disable** — contested | Partially-serving half-built work is the classic scope creep; hide it, let the user argue it back in. |

Anything that falls through (it should not) is **contested** and asked about with all five options.

## What each disposition commits the plan to

**Finish.** An acceptance criterion a stranger could check ("exporting an invoice list downloads a
CSV with these columns"), a day budget, and the dependency on any other Finish row. S/M/L map to
0.5 / 1.5 / 4 days by default; override from evidence, never from hope.

**Trim.** Two named slices. The *ships* slice gets Finish's fields. The *deferred* slice gets
Defer's. The boundary between them is stated in product terms ("ships: export CSV; deferred:
scheduled exports and XLSX").

**Disable.** The mechanism — one of:
- `flag` — an existing feature flag, named, defaulting off; proof is the flag's default and the
  one place it is read.
- `route` — the route or endpoint removed from the router; proof is a 404 / absence in the route
  table.
- `nav` — the entry removed from navigation while the route remains reachable by URL; proof is
  the nav component. **Say that the URL still works.** This is the weakest Disable; prefer it only
  when the route is harmless if found.
- `label` — the feature stays visible, marked "experimental"/"preview" in the UI and the docs;
  proof is the label. This is for things that work but are not polished, never for stubs.
- `entangled` — no clean mechanism exists. Either an S task adds a flag, or the row becomes Cut.

Every Disable also produces one line for the README's **Known limitations** and one for
**Roadmap** (if Defer-worthy) — the docs tell the truth the ledger established.

**Cut.** The code paths removed (or left for `dead-code-sweep`, named as such), and the list of
documents that currently promise the feature — plan sections, README lines, wiki pages — each of
which gets a one-line edit in the plan. A cut is complete when nothing still promises it.

**Defer.** A roadmap entry: the feature, the acceptance criterion already written, and the reason
it waited ("did not fit the <date> pencils down"). No date is attached to a deferred item unless
the user gives one.

## Arithmetic

```
finish_days = Σ Finish.day_budget + Σ Trim.ships_slice.day_budget
capacity    = working_days(today → pencils_down) × people × fraction
tolerance   = 0.20
```

If `finish_days > capacity × (1 + tolerance)`: the plan is not written. Return to the ledger and,
in this order, propose moving to Defer or Disable:

1. Finish rows that serve 🟡 (contested already).
2. Finish rows with distance L, lowest evidence confidence first.
3. Trim rows — shrink the *ships* slice further.
4. Finish rows with distance M that no other Finish depends on.

Never touch a Finish row with distance S, and never touch one the value-proposition sentence names
directly. If the sum still does not fit after those four passes, the date is wrong: say so, and
offer the date that fits.

Record every move under the plan's **Cut to fit the date** with the days it saved.

## Working-day count

Monday–Friday between today (exclusive) and pencils down (inclusive). Do not subtract holidays
unless the user names them; do note in Assumptions that none were subtracted.
