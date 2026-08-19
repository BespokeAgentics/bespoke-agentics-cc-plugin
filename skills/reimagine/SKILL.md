---
name: reimagine
description: "Point it at an existing component or page and get a live, code-grounded HTML variant gallery — the Current design recreated as a baseline plus reimagined versions spanning Restyle (same structure, new treatment), Restructure (same content, new layout/IA), and Rethink (new interaction model) — explored in a browser, settled via interview, ending in a spec with a divergence-from-current inventory. Use this whenever someone says 'reimagine X', 'redesign this page', 'explore some bolder takes', 'what else could this screen look like', 'give me a few directions for the dashboard', 'this component looks dated', 'modernize this table', 'show me alternatives to our current layout', or 'rethink this flow' — even when they never say 'reimagine'. All variants are brand-faithful: built from THIS repo's real tokens, typography, and labels, each cited to a path — reimagined, not off-brand. Emits ONE self-contained HTML file (inline CSS + JS, no build step) with a variant switcher, grid/split comparison views, shared state axes that hit every variant at once, in-page measurement, and browser commenting. The upstream sibling of interactive-wireframe: reimagine explores WHICH design, interactive-wireframe settles THE design, wireframe-parity checks the build. Not for settling an already-chosen change (use interactive-wireframe), not for auditing an existing UI (use a UX audit), and it writes NO production code (unlike impeccable/design-taste skills)."
---

# Reimagine

Point it at something that already exists; get back what it could become.

The premise: **asking "how should we redesign this?" in prose gets adjectives;
showing four rendered alternatives gets a decision.** And the alternatives are
only comparable if the thing they are being compared against — the Current
design — is standing right next to them, recreated honestly from source.

Three properties do the work:

1. **Brand-faithful grounding.** Every variant is built from the repo's real
   tokens, typography, enums and labels, cited to paths. Reimagined ≠ invented:
   a variant the design system cannot express is a pitch to _change the
   system_, and must say so out loud.
2. **The Current baseline is a transcription, not a memory.** The existing
   component is recreated from its real source into the gallery, so every
   "better" claim has an honest denominator.
3. **Tiers are contracts.** Restyle, Restructure and Rethink each promise what
   they preserve and what they change, with mechanical proxies — so the gallery
   spans the ambition range instead of showing the same idea three ways.

It ends with a spec whose core is the **divergence-from-current inventory** —
the implementer's worklist for moving the real component to the winning design.
**No production code is written.**

## When to use

A surface that exists and disappoints: dated, cluttered, outgrown its layout,
or simply never designed. Use it when the question is _"what could this be?"_ —
before anyone has committed to a direction.

**Skip it** when a direction is already chosen (that is `interactive-wireframe`
— settle the chosen design's details), when the question is "what's wrong with
this UI" (that is a UX audit), or when the surface doesn't exist yet (nothing
to reimagine — wireframe it).

## The loop

```
   ground + recreate Current
            ↓
   pitch directions ──→ user picks (nothing built yet)
            ↓
   build gallery ──→ serve ──→ measure
      ↑                          ↓
      └──── interview round ←────┘    reaction → critique → hybridize → winner
            ↓
   verify winner → emit spec (Δ inventory) → harvest
```

Calibrate to the surface: a single component might be three variants and two
rounds; a whole page might drop a tier in the directions round and spend the
budget on two Restructures instead. The tier defaults are a starting spread,
not a quota.

## Arguments

```
'<surface>' [--slug <name>] [--tiers restyle,restructure,rethink] [--variants N]
            [--rounds N] [--baseline-url <url>] [--port N] [--out <dir>] [--spec <path>]
            [--fresh] [--ttl <days>] [--no-verify] [--no-serve]
```

- `<surface>` (required) — the existing component or page to reimagine: a
  component name, a route, a file path, or a description ("the orders table",
  "our settings page"). Ambiguous targets are clarified in Phase 0 before
  grounding.
- `--slug <name>` (default: derived from the surface) — names
  `wireframes/<slug>/` and the spec.
- `--tiers <list>` (default `restyle,restructure,rethink`) — which ambition
  tiers get pitched and built.
- `--variants N` (default: one per active tier) — total reimagined panes;
  allocation across tiers is settled in the directions round.
- `--rounds N` (default: as many as the surface needs) — cap the interview.
- `--baseline-url <url>` — a running instance of the app for the Phase 1
  baseline cross-check. Never boots the app. Omitted → offered once; declined →
  the Current pane's fidelity chip says `code-grounded, not pixel-checked`.
- `--port N` / `--out <dir>` / `--spec <path>` / `--fresh` / `--ttl <days>` /
  `--no-verify` / `--no-serve` — identical semantics to
  `/bespoke-agentics:interactive-wireframe` (same serve script, same reuse
  library, same out dir default `./wireframes`, **8787 never auto-probed**).

## Phase 0 — Scope the target

Establish exactly which component or page, and what disappoints about it today.
One short exchange. If the target is ambiguous ("the dashboard" — which
route?), ask before grounding. Pick a slug — it names `wireframes/<slug>/` and
the spec. Slugs must not start with `_`.

## Phase 1 — Ground, and recreate Current

**Read `references/baseline.md`**, and the parent skill's
`references/grounding.md` in place for the per-ecosystem extraction recipe.

Extract from source: design tokens, typography, the real labels/enums the
surface displays, roles, behavioural constants, data extremes — plus the
target's own **structure**: element tree, landmark order, bands. Write it all
to `wireframes/<slug>/grounding.md` with a **Baseline fidelity** section
(`path:line` per structural claim, approximations listed).

**Check the library first.** Same rules as the parent
(`references/reuse-library.md`, read in place): cache entries within TTL
(default 14 days, `--ttl`) are reused and labelled `cached — verified <date>`;
`--fresh` skips consumption; a shared `grounding.md` from a prior run in the
same slug dir is a warm cache to extend, not replace.

If the app is running, offer the **baseline cross-check** once
(`--baseline-url <url>`, never boot it): inject wireframe-parity's
`wf-probe.js` (reused in place) into the live page and diff bands/contrast/
labels against the recreation. The Current pane's fidelity chip then says
`cross-checked <date>`; otherwise `code-grounded, not pixel-checked`. Labels
never lie.

## Phase 2 — Pitch directions, then get them picked

**Read `references/directions.md`.** Two briefs per active tier (default
tiers: restyle, restructure, rethink — `--tiers` to narrow), each with a
thesis, what changes, what's preserved, grounding citations, a risk, and an
ASCII preview from real labels. Then ONE `AskUserQuestion` round selects one
per tier **before any pane is built** — opened ledger-first when
`_library/decisions.md` has verdicts touching this surface.

Unbuilt briefs are kept: they feed the spec's Rejected Directions table and
the ledger. Nothing about a rejected pitch is wasted except the pane you
didn't build.

## Phase 3 — Build the gallery

```sh
mkdir -p wireframes/<slug>
cp "$SKILL_DIR/assets/reimagine-gallery.html" wireframes/<slug>/reimagine-v1.html
```

**Read `references/gallery.md`.** Edit the four marked REPLACE regions: one
shared token block, per-variant styles scoped `.rv-<id>`, one real sibling pane
per variant (Current first), and the manifest + shared axes. Library fragments
seed the `rv-current` block where applicable (`▼ FRAGMENT` markers, validated
against this run's `:root`).

Every variant carries the populated (longest-case) and empty states; loading/
error/responsive are out of scope by default and the spec says so. Check each
pane against its **tier proxy** before the interview opens — a Rethink that is
secretly a restyle gets demoted or rebuilt, not shipped.

The `reimagine-` filename prefix is the run-type marker: it keeps
wireframe-parity's `vN.html` discovery from ever grabbing a gallery.

## Phase 4 — Serve it

```sh
"$SKILL_DIR/../interactive-wireframe/scripts/serve-wireframe.sh" start wireframes/<slug>
```

The parent's serve script, reused in place — never forked. All its behaviour
carries: HTTP required (`file://` fails under automation), 8791→8799 with
**8787 never auto-probed**, `no-store`, browser comments via `/__feedback`,
`feedback` / `await-feedback` / `reply` subcommands, and the optional
`wireframe-feedback` channel (offer setup once; when live, comments push
instead of polling).

## Phase 5 — Interview against the gallery

**Read `references/interview.md`** (and the parent's, in place, for round
mechanics, previews, and contradiction shapes). The arc:

1. **First reaction** — URL over, grid view + comment mode invited, gut
   ranking, immediate kills.
2. **Per-variant critique** — works / breaks / **what to steal**; shared-axis
   flips as round material ("all four, empty"); cross-variant contradiction
   hunting.
3. **Hybridization** — 2–3 recipes as previews; a chosen hybrid is **rebuilt as
   a real pane** in `reimagine-v2.html` (killed variants → `retired` in the
   manifest), then confirmed against the render.
4. **Winner** — confirm the winner and a per-loser rejection reason drafted
   from critique evidence; offer the `interactive-wireframe` handoff.

Browser comments arrive tagged with their pane (`variant` in the payload) —
trust the tag, not the current switcher state. Gallery checks (markup, per-pane
contrast, focusables, tier proxies) run during rounds, and defects are named in
the round — users pick differently when they know which option carries one.

## Phase 6 — Verify the winner

The parent's full battery on the winning pane, in **single view** (grid/split
are for looking, not measuring — `references/gallery.md`): `__wf.env()` first,
then bands at rest and scrolled, full contrast sweep, markup, focusables, and
behavioural `seq` for any Rethink interaction. All hidden-tab caveats from the
parent's `references/browser-verification.md` apply. `--no-verify`, or no
automation available: everything unmeasured is labelled **"not verified"** in
the spec.

## Phase 7 — Emit the spec, then harvest

**Read `references/spec-template.md`.** Chosen direction & rationale, rejected
directions (brief vs gallery), decisions, the winner's contract, the
**divergence-from-current inventory** (one Δ row per region: Current at
`path:line` → becomes → change class), states, behaviour (mandatory for a
Rethink winner), the two verification tables (winner battery in the parent's
parity-consumable format + per-variant gallery checks), baseline fidelity,
risks, open questions, out of scope, handoff.

Path resolution as the parent: wiki → `./plans/<slug>.md` → ask once and record
in `CLAUDE.md`.

**Harvest into the shared library** (parent's `references/reuse-library.md`):
the winner's chrome and refreshed grounding rows harvest normally; **rejected
variants' styles never harvest** — their record is the spec and the ledger, not
fragments. Decision rows AND rejected-direction rows append to
`_library/decisions.md`; the `_index.md` run row is typed `reimagine`.

Close by offering — never auto-running — the handoffs: `interactive-wireframe`
for fine-grained settlement of the winner, orchestrate/workstream-orchestrate
for the build.

## Artifacts

```
<repo>/
├─ wireframes/
│  ├─ _index.md               shared with interactive-wireframe (runs typed
│  ├─ _library/               wireframe|reimagine); one library, one ledger
│  └─ <slug>/
│     ├─ grounding.md         incl. Baseline fidelity section
│     ├─ reimagine-v1.html    the gallery — self-contained, no build step
│     ├─ reimagine-v2.html    after hybridization/retirements
│     └─ .serve.* / .feedback.* / .replies.jsonl   runtime — gitignore
└─ plans/<slug>.md            the spec (or the wiki, if the project has one)
```

Committed by default, same gitignore lines as the parent.

## Reference files

| File                                        | Read when                                                                                          |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `references/baseline.md`                    | Phase 1 — recreating Current honestly; fidelity chip; wf-probe cross-check                         |
| `references/directions.md`                  | Phase 2 — tiers + honesty proxies, brief format, the directions round                              |
| `references/gallery.md`                     | Phase 3 — REPLACE regions, `.rv-<id>` scoping, `__rv` API, measure-in-single-view, sync obligation |
| `references/interview.md`                   | Phase 5 — reaction/critique/hybridize/winner, hybrid-rebuild-as-v2, per-pane comment routing       |
| `references/spec-template.md`               | Phase 7 — the output shape, Δ inventory, where it goes                                             |
| `assets/reimagine-gallery.html`             | Phase 3 — copy this; four REPLACE regions                                                          |
| parent `references/grounding.md`            | Phase 1 — per-ecosystem extraction (read in place)                                                 |
| parent `references/reuse-library.md`        | Phases 1/3/7 — TTL, fragments, ledger, harvest (read in place)                                     |
| parent `references/browser-verification.md` | Phase 6 — hidden-tab checklist (read in place)                                                     |
| parent `scripts/serve-wireframe.sh`         | Phase 4 — reused in place, never forked                                                            |
