---
name: "bespokeagentics:reimagine"
description: "Point it at an existing component or page and get a live, code-grounded HTML variant gallery: the Current design recreated from source as an honest baseline, plus reimagined versions spanning Restyle (same structure, new treatment), Restructure (same content, new layout/IA), and Rethink (new interaction model) — every variant brand-faithful to THIS repo's real tokens/typography/labels, cited to paths. Directions are pitched and picked BEFORE anything is built; the gallery is ONE self-contained HTML file (variant switcher, grid/split comparison, shared axes hitting every pane at once, in-page measurement, browser comments) served locally; an interview (reaction → critique → hybridize → winner) settles a direction, and the spec lands with a divergence-from-current inventory. The upstream sibling of interactive-wireframe: reimagine explores WHICH design, interactive-wireframe settles THE design, wireframe-parity checks the build. For 'reimagine X', 'redesign this page', 'bolder takes', 'what else could this look like', 'modernize this component'. Writes no production code."
argument-hint: "'<surface>' [--slug <name>] [--tiers restyle,restructure,rethink] [--variants N] [--rounds N] [--baseline-url <url>] [--port N] [--out <dir>] [--spec <path>] [--fresh] [--ttl <days>] [--no-verify] [--no-serve]"
allowed-tools: Skill(reimagine), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep, Agent
---

# Reimagine

Run the `reimagine` skill: recreate an existing surface from this repo's real
source as an honest baseline, pitch redesign directions across three ambition
tiers, build the picked ones into a self-contained variant gallery, interview
against it, verify the winner by measurement, and write a spec whose core is
the divergence-from-current inventory. **No production code is written** — the
output is a gallery plus a spec.

## Arguments

Parse from `$ARGUMENTS`:

```
'<surface>' [--slug <name>] [--tiers restyle,restructure,rethink] [--variants N]
            [--rounds N] [--baseline-url <url>] [--port N] [--out <dir>] [--spec <path>]
            [--fresh] [--ttl <days>] [--no-verify] [--no-serve]
```

- `<surface>` (required) — the existing component or page to reimagine: a
  component name, a route, a file path, or a description ("the orders table",
  "our settings page"). Ambiguous targets are clarified before grounding.
- `--slug <name>` (default: derived from the surface) — names
  `wireframes/<slug>/` and the spec.
- `--tiers <list>` (default `restyle,restructure,rethink`) — which ambition
  tiers get pitched and built. Each tier is a contract: Restyle preserves the
  DOM and changes only treatment; Restructure preserves content and changes
  layout/IA; Rethink preserves the task and changes the interaction model.
- `--variants N` (default: one per active tier) — total reimagined panes;
  allocation across tiers is settled in the directions round.
- `--rounds N` (default: as many as the surface needs) — cap the interview.
- `--baseline-url <url>` — a running instance of the app for the baseline
  cross-check (wf-probe diff of bands/contrast/labels against the recreation).
  Never boots the app. Omitted → offered once; declined → the Current pane's
  fidelity chip says `code-grounded, not pixel-checked`.
- `--port N` / `--out <dir>` / `--spec <path>` / `--fresh` / `--ttl <days>` /
  `--no-verify` / `--no-serve` — identical semantics to
  `/bespokeagentics:interactive-wireframe` (same serve script, same reuse
  library, same out dir default `./wireframes`, **8787 never auto-probed**).

## Process

Invoke the `reimagine` skill and forward `$ARGUMENTS`. The skill will:

1. **Scope** — pin down exactly which surface and what disappoints about it.
2. **Ground + recreate Current** — extract real tokens, typography, labels,
   roles, and the target's own structure (element tree, bands, landmark order)
   to `wireframes/<slug>/grounding.md` with a Baseline fidelity section; the
   Current pane is a transcription of source, never a memory. Library
   cache-first with TTL labelling; optional wf-probe cross-check against a
   running app.
3. **Pitch directions** — two briefs per active tier (thesis, changes,
   preserves, grounding citations, risk, ASCII preview), then ONE
   AskUserQuestion round picks one per tier **before anything is built** —
   ledger-first when settled verdicts touch this surface. Unbuilt briefs feed
   the spec's Rejected Directions and the ledger.
4. **Build the gallery** — `wireframes/<slug>/reimagine-v1.html`: one
   self-contained file, Current + the picked variants as real sibling panes,
   variant switcher with single/grid/split views, shared axes that hit every
   pane at once (flip "empty" and all variants answer), per-pane tier-proxy
   checks, browser comments tagged with their pane.
5. **Serve** — the parent skill's `serve-wireframe.sh`, reused in place
   (8791→8799, comments POST to `/__feedback`, channel push when registered).
6. **Interview** — reaction (gut ranking, kills) → per-variant critique
   (works / breaks / what to steal, shared-axis flips, cross-variant
   contradiction hunting) → hybridization (a chosen hybrid is **rebuilt as a
   real pane** in `reimagine-v2.html`, then confirmed) → winner (per-loser
   rejection reasons drafted from critique evidence).
7. **Verify the winner** — full measurement battery in single view: bands,
   contrast sweep, markup, focusables, behavioural `seq` for Rethink
   interactions; hidden-tab caveats honoured; unmeasured ⇒ "not verified".
8. **Spec + harvest** — chosen direction & rationale, rejected directions,
   decisions, the winner's contract, the **divergence-from-current inventory**
   (Δ rows: Current at `path:line` → becomes → change class), two verification
   tables (the winner's in wireframe-parity-consumable format), baseline
   fidelity, risks, open questions, out of scope. Wiki if a vault exists, else
   `./plans/<slug>.md`. Winner's chrome harvests into the shared
   `wireframes/_library/`; rejected variants' styles never do; the `_index.md`
   run row is typed `reimagine`. Ends by **offering** the
   `interactive-wireframe` handoff (fine-grained settlement of the winner) and
   the orchestrate handoff (build) — never auto-running either.

## Output

- `wireframes/<slug>/reimagine-v1.html` (and `reimagine-v2.html` after
  hybridization) — self-contained; any pane+state is a shareable
  `#rv=…&view=…` link.
- `wireframes/<slug>/grounding.md` — every value with its source path, plus
  Baseline fidelity (approximations listed, cross-check deltas if run).
- `wireframes/_index.md` + `wireframes/_library/` — the reuse library shared
  with interactive-wireframe (one ledger, runs typed).
- The spec at `--spec`, the wiki, or `./plans/<slug>.md`.

Ends with the gallery URL, the winner and its rationale, the Δ-inventory count,
what the verification pass measured, and anything left open — then offers the
handoffs. It does not write production code.
