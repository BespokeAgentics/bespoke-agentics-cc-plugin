# Reuse library — cache, fragments, decisions

Read when `<out>/_index.md` exists (Phase 1), and again before harvest (Phase 6).
The job: stop re-deriving what a previous run of this skill already grounded,
built, and settled — without ever weakening the "never invent, always cite" rule.

## Why this exists

Measured on a real project with two runs: the two `grounding.md` files carried a
byte-identical token table (the second one hand-wrote "reused verbatim — see
<other-slug>/grounding.md" because no mechanism existed); ~17% of each wireframe
file was project chrome rebuilt from scratch (token `:root`, app-shell header
stack, button/pill primitives); and the second run consumed the first run's
settled verdicts as fixed context, carried by hand. The generic harness (~38%)
is already reused via the scaffold. This library formalises the rest.

## Layout

The library lives **inside the output directory** — per project, per `--out`:

```
<out>/                            # default ./wireframes
├─ _index.md                      # run registry + fragment catalog + quick-reuse steps
├─ _library/
│  ├─ grounding-cache.md          # tokens · typography · roles · anchors, per-section verified dates
│  ├─ decisions.md                # append-only ledger; reopened rows marked superseded
│  └─ fragments/                  # tokens-root.css, app-shell-header.html, …
└─ <slug>/…                       # per-run output, unchanged
```

Rules:

- **Per-out-dir, never global.** Tokens do not transfer between products. When
  `--out` is overridden, that directory's library is the one consulted and fed.
- **Slugs must not start with `_`** — the underscore prefix is reserved for the
  library and sorts it first.
- **Git is the version store.** Wireframes are committed by default; the library
  is too. No `-v2` fragment files, no checksums, no JSON.

## The three layers

### 1. Grounding cache — `_library/grounding-cache.md`

The run-independent slice of grounding: tokens, typography, roles/permissions,
stack line, surface anchors. Each **section** carries its own `verified` date so
partial staleness is representable; each **row** keeps its `path:line` citation.

```markdown
# Grounding cache — <project>

**Stack:** Next.js 15 · React 18 · Tailwind v4 — verified 2026-07-22

## Tokens · verified 2026-07-22 · `packages/ui/src/styles/tokens.css`
| Token | Value | Line |
|---|---|---|
| `--paper` | `#fcfcfc` | 53 |

## Typography · verified 2026-07-22
## Roles / permissions · verified 2026-07-22
## Surface anchors · verified 2026-07-22
```

### 2. Fragment library — `_library/fragments/`

One file per fragment: a named CSS+markup block that feeds the scaffold's
REPLACE regions. Self-describing header; `▼ css` / `▲ css` and `▼ markup` /
`▲ markup` payload sections so one fragment feeds REPLACE 2 and 3 atomically.

```html
<!-- ═══ FRAGMENT: app-shell-header ═══════════════════════════════════════════
  origin:    <slug> · v1.html
  harvested: 2026-07-22        verified: 2026-07-22
  sources:   apps/shell/src/…/FeatureStickyHeader.tsx:41-88 ·
             packages/ui/src/styles/tokens.css:53-84
  tokens:    --paper --ink --rule --accent --font-display --tracking-caps
  feeds:     css → REPLACE 2 · markup → REPLACE 3
  notes:     welded sticky stack; static context in most runs
  ═══════════════════════════════════════════════════════════════════════════ -->
<!-- ▼ css -->
…
<!-- ▲ css -->
<!-- ▼ markup -->
…
<!-- ▲ markup -->
```

- `tokens:` is generated mechanically — grep `var(--…)` in the payload — and is
  validated against the current run's REPLACE 1 before injection. A missing
  dependency blocks injection until the token is grounded.
- Pure-CSS fragments (`tokens-root.css`) use the same header in `/* */` form,
  `feeds: REPLACE 1`, plus `canonical: ../grounding-cache.md (token table)` —
  verification lives in the cache table; the fragment is its render-ready form.

### 3. Decisions ledger — `_library/decisions.md`

Append-only. Never delete a row; a reopened decision gets a new row and the old
one is marked `superseded by <slug>/Dn`.

```markdown
| ID | Decision | Verdict | Settled | Spec | Status |
|---|---|---|---|---|---|
| <slug>/D3 | Rail structure | flat outline, no accordions | 2026-07-18 · wireframe | plans/<slug>.md | settled |
```

## TTL — when to trust the cache

Default **14 days**, overridable with `--ttl <days>`. Three states, and the
label in `grounding.md` must match what actually happened — **labels never lie**:

| Cache age | What you do | Label in grounding.md |
|---|---|---|
| Within TTL | Reuse without re-checking | `cached — verified <date>` |
| Past TTL, anchors match | Grep the cited `path:line` anchors; refresh the date | `cached — re-verified <today>` |
| Past TTL, anchors drifted | Re-derive that entry, update the cache | fresh citation + drift noted in **Gaps** |

Drift is a **finding**, not an embarrassment — record what changed in the Gaps
section; it often becomes an interview question. `--fresh` skips consumption
entirely (everything grounded fresh) but the run still harvests at the end: a
fresh run just re-derived everything, so its output heals the library.

## Consumption, per phase

### Phase 1 — cache first

If `<out>/_index.md` exists, start grounding from `grounding-cache.md` (TTL
rules above) and ground **only surface-specific values** fresh: the enums this
surface displays, its data extremes, its behavioural constants. The per-run
`grounding.md` still carries **full tables** — it stays a self-contained audit
trail — with cache provenance in the section heading:

```markdown
## Tokens (cached — verified 2026-07-22 · `_library/grounding-cache.md`)
```

### Phase 2 — inject fragments

After copying the scaffold, seed the REPLACE regions from applicable fragments
before authoring anything new. Validate each fragment's `tokens:` list against
this run's `:root`, then wrap the payloads in markers — same ▼/▲ language as the
REPLACE banners:

```css
/* ▼ FRAGMENT app-shell-header · from _library · origin <slug> · verified 2026-07-22 */
…
/* ▲ /FRAGMENT app-shell-header */
```

(HTML payloads use `<!-- -->` comments with identical text.) Editing inside
markers during rounds is allowed and expected — the marker-bounded region is
what harvest diffs against the library payload. Only inject fragments that fit
the surface; a fragment forced in to save typing costs more than it saves.

### Phase 4 — decisions as fixed context

Open round 1 by listing the ledger rows that touch this surface as **fixed
context**, with one cheap "reopen any of these?" affordance — never silently
re-asked (rude), never silently dropped (dishonest). Reopening is fine: the new
verdict gets a new ledger row and the old one is marked superseded. Carried
decisions land in the spec's table as `Settled by: carried (<slug>/Dn)`.

## Harvest — Phase 6, automatic

After the spec is written, before the final report:

1. **Diff each `▼ FRAGMENT` region** against its library payload.
   - Unchanged → refresh `verified:` (Phase 5 just re-proved it on screen).
   - Changed → judge: a surface-specific tweak stays out of the library (note
     it); an improvement or drift fix updates the fragment **in place** with
     `updated: <date> by <slug>`. A genuinely coexisting variant gets a new
     name (`app-shell-header--compact`) — never a `-v2` file.
2. **Harvest new fragments** by the settled-context heuristic: *harvest what
   you rendered as settled context, not what you interviewed about.* The
   surface under discussion is by definition undecided and run-specific; the
   chrome and primitives rendered around it so the geometry is real are the
   candidates. Cap **5 per harvest**.
3. **Merge run-independent grounding rows** into the cache with today's date.
4. **Append the spec's full decision table** to the ledger — relevance
   filtering happens at consumption time, where the next surface is in view.
   Mark any reopened rows' predecessors superseded.
5. **Update `_index.md`**: add the run row, refresh the fragment catalog.
6. **End the final report with a "Harvested" list** — paths, so the user sees
   the library grow.

## `_index.md`

```markdown
# Wireframe index — <project>

## Runs
| Slug | Surface | Type | Date | Spec | Decisions |
|---|---|---|---|---|---|

## Library
**Grounding cache** — `_library/grounding-cache.md` · TTL 14d
**Decisions ledger** — `_library/decisions.md` · N settled · M superseded

| Fragment | Feeds | Origin | Verified | Token deps |
|---|---|---|---|---|

## Quick reuse — read first on a new run
1. Phase 1: start from the cache; ground only surface-specific values fresh.
2. Phase 2: inject applicable fragments with `▼ FRAGMENT` markers.
3. Phase 4 round 1: present the ledger as fixed context, one reopen affordance.
```

`Type` distinguishes run kinds sharing this library: `wireframe` (this skill)
or `reimagine` (the variant-gallery sibling). Blank in legacy rows means
`wireframe`.

## Backfill — when runs exist but no library does

If `<out>/` contains slug directories but no `_index.md`, **offer a one-time
backfill** (default yes): extract the cache from the most recent `grounding.md`,
lift fragment candidates from existing `vN.html` files, and seed the ledger from
the specs' decision tables. One honesty rule governs it: a backfilled cache
entry earns a `verified:` date **only after its `path:line` anchors pass the
grep** — old grounding may already be stale, and a backfilled label that claims
verification which never happened is exactly the lie this file forbids.

## Honesty rules

- **Labels never lie.** `cached — verified <date>` means nobody checked today;
  `re-verified` means the anchors were grepped today. Never blur them.
- **A stale entry beats an invented one.** If re-derivation fails, keep the old
  value, label its age, and put the failure in Gaps.
- **Drift is a finding.** Report what changed; do not quietly paper over it.
- **The library is a cache, not an authority.** Source wins every conflict; the
  library is only ever as good as its last verification.
