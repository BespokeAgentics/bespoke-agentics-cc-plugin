---
name: "bespokeagentics:wireframe-parity"
description: "Confirm the implemented UI matches the wireframe a spec settled. Resolves the interactive-wireframe spec + wireframe HTML + decisions ledger, grounds every settled decision/state/label in the implementation (file:line), then drives BOTH the wireframe and the running app in a browser, injects the same measurement kit into each, and diffs band geometry / contrast / markup / focusables / rendered labels against the spec's frozen Verification numbers — per state. Spec Decisions are the parity contract; an AskUserQuestion interview separates real regression from intended evolution. Writes a READ-ONLY, color-coded parity report to ./reviews/ — never modifying the implementation. Distinct from plan-review (audits a document before build) and ux-audit (audits a UI against heuristics): this audits a BUILT UI against the wireframe that specified it. Composes with interactive-wireframe."
argument-hint: "'<spec-or-slug>' --app <url> [--wireframe <path>] [--depth quick|standard|deep] [--out <dir>] [--no-browser] [--force]"
allowed-tools: Skill(wireframe-parity), Agent, AskUserQuestion, Bash, Read, Write, Glob, Grep
---

# Wireframe Parity

Run the `wireframe-parity` skill: take a wireframe spec that has been implemented, confirm the built
UI matches what the wireframe settled, and write a read-only parity report. **The implementation is
never modified.**

## Arguments

Parse from `$ARGUMENTS`:

```
'<spec-or-slug>' --app <url> [--wireframe <path>] [--depth quick|standard|deep] [--out <dir>] [--no-browser] [--force]
```

- `<spec-or-slug>` (required) — the wireframe spec path (`./plans/<slug>.md` or a wiki page) or a slug.
  A slug resolves the spec, `wireframes/<slug>/` (highest `vN.html`), and `wireframes/_library/`. If
  omitted, the skill discovers the most recent spec that has a matching wireframe and confirms it.
- `--app <url>` — the running implemented UI (a route on a live dev server). Driven **read-only**; the
  reviewer injects the probe but never submits forms or mutates data. If omitted, the skill asks (or
  offers `--no-browser` for a structural-only pass).
- `--wireframe <path>` — override the wireframe HTML (default: highest `vN.html` in `wireframes/<slug>/`).
- `--depth quick|standard|deep` (default `standard`) — `quick` = structural parity + headline
  divergences, no adversarial pass; `standard` = structural + measured across every reachable state;
  `deep` = wider grounding + each divergence adversarially verified (measurement artifact vs. intended
  evolution vs. real regression) before it survives.
- `--out <dir>` (default `./reviews`) — where the parity report is written.
- `--no-browser` — skip the measured pass; structural (code-grounded) parity only. Every
  geometry/contrast finding is then labelled "not measured".
- `--force` — re-run all phases even if outputs exist.

## Process

Invoke the `wireframe-parity` skill and forward `$ARGUMENTS`. The skill will:

1. **Resolve & parse** — read the spec + decisions ledger + grounding cache, and build the *intended
   model*: decisions, contract invariants (+ their `__wf` numbers), states (each mapped to the
   wireframe URL that reproduces it), the frozen Verification snapshot, and the real labels/enums →
   `intended-model.md`.
2. **Ground** — parallel `Explore` agents map each settled decision / state / label to the real
   implementation `file:line`, marking honored / drifted / missing and surfacing what the build likely
   *missed* → `grounding-map.md`. This is the floor — it runs even under `--no-browser`.
3. **Measure** — serve the wireframe (`serve-wireframe.sh`), inject the **same** `wf-probe.js` into
   both the wireframe and the app, drive each to the matching state, and diff band geometry / contrast
   / markup / focusables / rendered labels within tolerance (±2px, same-AA verdict, contiguity as the
   contract requires). Unreachable (auth-gated) states are labelled honestly → `measured-parity.md`.
   Skipped under `--no-browser`; on `--depth deep` each divergence is adversarially verified first.
4. **Interview** — AskUserQuestion batches classify each divergence — **regression** (fix the build),
   **intended evolution** (the build is right, the wireframe is stale), or **out of scope** — and set
   priority, so the report reflects intent rather than raw suspicion.
5. **Report** — write `./reviews/<slug>-parity.md`: parity verdict (🟢/🟡/🔴), strengths, a
   decision-by-decision parity table, a measured parity table (intended / spec-frozen / as-built / Δ),
   label fidelity, a color-coded divergence register, a "not measured" coverage section, open
   questions, and a "definition of parity" checklist. Wiki-ingested if a vault exists.

## Output

`{OUT_DIR}/<slug>-parity.md` (the read-only parity report), plus intermediate artifacts under
`wireframe-parity-analysis/` (intended-model, grounding-map, measured-parity, interview-answers). Ends
with a summary and a parity verdict, then **offers** to open the P0 regressions as tasks — or, when the
interview found intended evolutions, to refresh the stale decisions ledger + spec. It does not modify
the implementation, the spec, or the wireframe unless you say so.
