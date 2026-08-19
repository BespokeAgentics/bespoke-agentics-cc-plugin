# Skill reverse-engineering report — data-ui-craft

- **Target**: `skills/data-ui-craft/`
- **Mode**: audit (read-only — nothing in the target was modified)
- **Host**: no-host — cwd is the plugin repo that *authors* this skill, not a data-dense app it would operate on; KM1–KM3 are therefore ungradeable here and were not filed as defects (KM4/KM5 file normally and did)
- **Date**: 2026-07-27
- **Verdict**: 🟡 improvisation-dependent

The judgment layer of this skill is genuinely strong — a stable-ID rule catalog with per-rule
detection cues and default severities, an explicit calibration section, worked code recipes, and
fifteen real `.tmpl` files. The mechanical layer does not exist. Of 20 reconstructed steps, **zero
are owned by a bundled artifact and 12 are mechanical work the model re-derives every run**: stack
detection, surface discovery, a 118-line HTML report skeleton retyped from a fenced block, severity
tallying, and the kit scaffolding — whose shipped barrel exports 13 modules that a partial scaffold
will not have written, so the run must improvise a fix or fail its own Phase-3 typecheck. There are
no CRITICAL findings because nothing silently corrupts the audit's *content*; the four HIGH findings
are all cost-and-variance in the layer around it. This is a skill with no `scripts/` directory, not a
skill with no thinking in it.

## Metrics

| Metric | Value |
|--------|-------|
| SKILL.md lines / words | 281 / 2,575 (228 prose lines, **0 fenced code blocks**) |
| Bundled: scripts / references / templates / assets | **0** / 4 / 15 / 0 |
| Steps: script-owned / model-mechanical / model-judgment / user-gate | **0 / 12 / 7 / 1** |
| ALL-CAPS directives (MUST/NEVER/ALWAYS) | **0** — the skill argues instead of shouting |
| Vague quantifiers at decision points | 0 (1 total occurrence, incidental: `references/pillars.md:107`) |
| Verify-verbs without a runnable check | 1 load-bearing (`SKILL.md:226`, 5 conditions) of 9 matched lines |
| Broken internal references | **0** — `inventory.py` reported 1; verified false positive (its regex truncates `templates/README.md.tmpl` at `.md`; the file exists) |
| LLM-answered questions materializable (KM) | 2 (KM4, KM5) — KM1–KM3 not assessable in `no-host` |

## Step-executor matrix

The reconstructed execution of the default `audit-and-implement` run.

| # | Step | Executor | I/O form | Failure path | Finding |
|---|------|----------|----------|--------------|---------|
| 1 | Parse `mode` / `path` args | model-mechanical | prose args → context | "if ambiguous, ask" | M5 |
| 2 | Detect framework / styling / data layer / existing utilities | model-mechanical | repo → prose summary | none | H1 |
| 3 | Print detection summary | model-mechanical | prose in chat | none | — |
| 4 | Discover data-display surfaces via a 4-bullet grep set | model-mechanical | repo → `## Surfaces` prose | "nothing found → ask user" ✅ | H1 |
| 5 | Infer each field's data type from the column defs | model-judgment | prose | none | — |
| 6 | Mode dispatch | model-mechanical | table lookup | none | — |
| 7 | Walk every `DF*`/`PD*`/`IU*` rule against each surface | model-judgment | reference → findings in context | none | — |
| 8 | Assign + calibrate severity | model-judgment | context | none | — |
| 9 | Collect Opportunities | model-judgment | context | none | — |
| 10 | Emit `./data-ui-craft-audit.md` | split: mechanical skeleton / judgment prose | context → file | none | H4, L3 |
| 11 | Emit `./data-ui-craft-audit.html` | model-mechanical | 118-line fenced block → file | none | H3, L1, L3 |
| 12 | Tally counts by severity, print chat summary | model-mechanical | context → chat | none | H4 |
| 13 | Append audit row to `wiki/_log.md` | model-mechanical | file append | "if `wiki/` exists" ✅ | — |
| 14 | Interview: frame intent, accept findings, choose kit | **user-gate** | AskUserQuestion | n/a | — |
| 15 | Classify each accepted fix: in-place vs needs a primitive | model-judgment | context | none | — |
| 16 | Scaffold the kit: select templates, substitute 3 tokens, write barrel | model-mechanical | `templates/*.tmpl` → files | none | H2, M2 |
| 17 | Apply in-place fixes to real code | model-judgment | edits | ">10 lines → show diff" ✅ | — |
| 18 | Print wiring guide + wiki log | model-mechanical | prose + file append | none | — |
| 19 | Run `tsc --noEmit` + the project's linter | model-mechanical | shell | none | M4 |
| 20 | Layout sanity pass (5 conditions) | model-judgment (should be part check) | eyeball / screenshot | "if browser tools are available" | M3, M4 |

## Findings

### H1 · HIGH — Stack detection and surface discovery are prose procedures, so the audit's *scope* varies run to run
- **Where**: `skills/data-ui-craft/SKILL.md:77-109`
- **Run-to-run consequence**: these two phases decide what gets audited at all, and both are
  re-derived from prose each run. A repo with both Tailwind and CSS Modules can be classified
  either way ("capture the *dominant* one" is a judgment with no evidence-gathering procedure
  behind it), and the four-bullet grep set at `:99-104` is retyped from memory — a run that skips
  `columnDefs` or the mapped-row pattern audits a smaller surface set and reports fewer findings
  with no indication anything was missed. Every downstream finding, severity, and fix inherits that
  variance, and two audits of the same commit can legitimately disagree on scope.
- **Evidence**: "Inspect: 1. **Framework** … 2. **Styling primitive** … Capture the *dominant* one";
  "Grep for the shapes that hold data: `<table`, `<thead`, `role=\"grid\"`, `DataGrid`, …"
- **Refactor**: two scripts, both emitting JSON the model then *judges* from:
  `scripts/detect_stack.py <root> --json` → `{framework, styling, data_layer, utilities:{cn,tooltip,popover,badge,toast,icons}}`, each with the evidence paths and import counts that support it;
  `scripts/find_surfaces.py <root> [--path P] --json` → candidate surfaces with `file:line` and the
  pattern that matched. The SKILL.md prose keeps the *why* and the ambiguity rule ("dominant one
  wins; if the counts are close, say so and ask").
- **Family note**: the KM1 reading (materialize the host's stack into a facts file) was considered
  and rejected — the answer is recomputable in under a second, so an artifact would add a staleness
  surface for nothing. Recorded in `host-context.json`.

### H2 · HIGH — The kit barrel exports 13 modules a partial scaffold will not have written
- **Where**: `skills/data-ui-craft/templates/index.ts.tmpl:5-21` against `SKILL.md:168`
- **Run-to-run consequence**: Phase 2b says "write only the primitives that are actually needed",
  but `index.ts.tmpl` unconditionally re-exports all thirteen. A run that scaffolds three primitives
  and copies the barrel verbatim ships a kit that fails the skill's own Phase-3 `tsc --noEmit` on
  ten missing modules; a run that notices improvises its own pruning; a run that over-corrects
  writes all thirteen files to make the barrel true. Three different outcomes from one instruction,
  and the failure only surfaces two phases later where it reads as an integration problem.
- **Evidence**: `export { NumericCell } from "./NumericCell";` … `export { TableSkeleton, EmptyState, ErrorState } from "./TableStates";` — a fixed list, versus "write only the primitives that are actually needed".
- **Refactor**: `scripts/scaffold_kit.py --dest <dir> --primitives NumericCell,Tooltip,TableStates [--cn <import>] [--icons <pkg>] [--list] [--dry-run]` — copies only the requested templates, substitutes the three tokens, **generates** the barrel from the selected set (grouped by pillar, with the `ChecklistStep` type export only when `OnboardingChecklist` is selected), and writes `cn.ts` only when `--cn` is absent. `--list` prints each primitive with its pillar and the rules it fixes; the SKILL.md table at `:172-175` becomes that script's `--list` output.

### H3 · HIGH — The HTML report is a 118-line skeleton the model retypes on every audit
- **Where**: `skills/data-ui-craft/references/report-format.md:72-189`
- **Run-to-run consequence**: every audit regenerates ~50 CSS rules, a five-card summary grid, a
  findings table, the collapsible card markup, and the `toggle()` script by transcribing a fenced
  block into a written file. The token cost is paid on every run, and the failure mode is quiet:
  drop the `.card-body.open` rule or mistype `nextElementSibling` and the report renders but no
  finding expands — nothing in the skill checks the emitted HTML, so the run reports success. The
  markdown report next to it *is* a real template with a worked example, which makes the asymmetry
  clearer: one deliverable is pinned, the other is re-improvised.
- **Evidence**: `<!DOCTYPE html>` … `function toggle(h){const b=h.nextElementSibling,c=h.querySelector(".chevron"); …}` — 118 lines inside a fenced block in a reference.
- **Refactor**: move the block verbatim to `assets/audit-report.html` with six comment slots
  (`<!--{{META}}-->`, `<!--{{SUMMARY_GRID}}-->`, `<!--{{EXEC_SUMMARY}}-->`, `<!--{{FINDINGS_TABLE}}-->`,
  `<!--{{FINDING_CARDS}}-->`, `<!--{{OPPORTUNITY_CARDS}}-->`, `<!--{{METHODOLOGY}}-->`), and add
  `scripts/render_report.py <findings.json> --html-out ./data-ui-craft-audit.html --md-out ./data-ui-craft-audit.md`
  that fills both from the H4 contract. Pairs with H4: the renderer needs the JSON, and the JSON
  needs a renderer to be worth writing.

### H4 · HIGH — Findings never leave the model's context, so nothing can validate, resume, or count them
- **Where**: `skills/data-ui-craft/SKILL.md:127-129`, `:140-141`, `:153-154`, `:209-214`
- **Run-to-run consequence**: the finding record is specified as prose fields, then flows to two
  report files, a chat summary, an interview, and the implement phase entirely through context.
  Consequences compound: (a) the severity counts at `:140` are tallied by the model — miscounts are
  low-rate but silent; (b) the md and html reports are written independently from the same context
  with nothing enforcing that they contain the same findings; (c) the accepted set from the
  interview is carried as recollection, so a compaction between Phase 2-AI and Phase 2c can drop or
  add an accepted fix; (d) `implement` invoked directly is told to "run a quick scan … first"
  (`:153-154`) — the skill explicitly re-audits because the previous audit left no artifact it can
  read.
- **Evidence**: "Record each finding with: rule ID, the pillar, `file:line`, what the user
  experiences …, severity …, and a one-line fix pointer"; "If invoked directly as `implement`, run a
  quick scan against `references/audit-rules.md` first so you know what to fix".
- **Refactor**: `./data-ui-craft-audit.json` as the single source of truth, written by the audit
  phase and read by everything after it —
  `{stack:{…}, surfaces:[{file,line,name,fields:[{name,type}],actions:[]}], findings:[{id,rule,pillar,severity,file,line,instances,user_impact,fix,fix_kind:"column-def"|"jsx"|"primitive",accepted:null}]}`
  — plus `assets/rules.json` (rule id → pillar, default severity, fix section) so the renderer
  derives pillar tags and counts by lookup rather than recall. `implement` mode reads the file when
  present instead of re-scanning; the interview writes `accepted` back.

### M1 · MEDIUM — The cross-stack adapter mapping is stated eleven times
- **Where**: `skills/data-ui-craft/references/patterns-react.md:351-360` (the quick map) and the
  per-section **Adapt** notes at `:32-35, 61-63, 99-101, 124-125, 153, 181-183, 228-229, 251, 279, 300-301`
- **Run-to-run consequence**: the same condition→action mapping (stack × concern → the fix) exists
  as a table and as ten prose restatements. Which one a run applies depends on read order, and they
  already differ in detail — the quick map gives MUI's chip as `<Chip>` while the section note gives
  `<Chip color=…>`; the quick map omits Ant entirely for tooltips while `§ Chips` names `<Tag color=…>`.
  Editing one location leaves the others stale, and a run adapting to a non-React stack picks
  whichever it read last.
- **Evidence**: "**Adapt:** shadcn/ui — wrap its `Badge` with a variant map; MUI — `<Chip color=…>`; Ant — `<Tag color=…>`" versus the `| Chip | … | wrap `Badge` | `<Chip>` | cell renderer | same classes |` row.
- **Refactor**: KM4 — `assets/stack-adapters.json`, keyed `{concern: {react-tailwind, shadcn, mui, antd, ag-grid, vue, svelte, angular, plain-css}}` with one entry per fix section, shipped inside the skill (skill-invariant, needs no host). The Adapt prose keeps only what the JSON can't hold (the *why*, the caveats like "don't add a heavy timeline dependency") and points at the file.

### M2 · MEDIUM — The `{{CN}}` substitution contract contradicts itself across three files
- **Where**: `skills/data-ui-craft/SKILL.md:179-181`, `templates/cn.ts.tmpl:1-2`, `templates/index.ts.tmpl:23-25`
- **Run-to-run consequence**: `{{CN}}` is an *import specifier* in all 15 templates, but its default
  is never written as a literal. SKILL.md says "default a local `cn`" (is that `cn`, `./cn`, or
  `@/lib/utils`?) and locates the no-helper fallback in the barrel; `cn.ts.tmpl` locates the same
  fallback in itself and says to delete the file when the project has its own helper; the barrel
  comment describes a third arrangement. A run that follows SKILL.md alone emits
  `import { cn } from "cn"` in thirteen files — a bare specifier that resolves to nothing, so every
  generated file fails to compile, caught two phases later by `tsc` and read as a project problem.
- **Evidence**: SKILL.md — "`{{CN}}` — the project's class-merge helper import (default a local `cn`; if none exists, the `index.ts` barrel exports a tiny fallback)"; `cn.ts.tmpl` — "If the project already has one, set {{CN}} to it (e.g. \"@/lib/utils\") and delete this file."
- **Refactor**: one source of truth — the `--cn` flag of the H2 scaffold script, defaulting to
  `"./cn"` and writing `cn.ts` alongside; SKILL.md and the template comments state the default by
  pointing at the script, not by re-describing it.

### M3 · MEDIUM — The layout sanity pass is five decidable conditions with no check and an optional trigger
- **Where**: `skills/data-ui-craft/SKILL.md:223-228`
- **Run-to-run consequence**: this is the only verification of the fixes the skill just applied, and
  it is an eyeball. Four of its five conditions are objectively decidable from the diff (a numeric
  cell carries `text-right` + `tabular-nums`; a truncation site has a reveal; an icon-only button
  has an accessible name; a container has all three branches), yet none has a command. The trigger
  is conditional on browser tooling ("if browser tools are available"), so a run without it skips
  the whole pass — including the four checkable conditions — and still reports the fixes as done,
  with nothing in the wiring guide saying verification didn't happen.
- **Evidence**: "Eyeball (or screenshot, if browser tools are available) the edited surface at a
  narrow and a wide width and confirm: numbers still align, truncation shows an ellipsis …"
- **Refactor**: `scripts/check_fixes.py <findings.json> --json` asserting, per applied fix, that the
  expected marker landed (`text-right` + `tabular-nums` on DF1 sites, a `title=`/`Tooltip`/expand on
  DF3 sites, `aria-label` or a `Tooltip` wrapper on IU1 sites, all three branches present at IU4/5/6
  sites) with a nonzero exit and a per-fix verdict. The genuinely visual residue (chips wrapping,
  hover-induced layout shift at narrow widths) stays an eyeball — but becomes an explicitly labelled
  one: "not visually verified — no browser tools" in the wiring guide when it doesn't run.

### M4 · MEDIUM — No degradation section; three Phase-3 tool dependencies have undefined absence behavior
- **Where**: `skills/data-ui-craft/SKILL.md:218-228`
- **Run-to-run consequence**: `npx tsc --noEmit`, the linter, and browser tooling are all invoked
  with no stated behavior when unavailable or when they fail for unrelated reasons. In a JavaScript
  project with no `tsconfig.json`, `npx tsc --noEmit` produces errors the skill did not cause —
  one run reports the implementation as broken, another "fixes" unrelated files, a third silently
  skips. The skill *does* define fallbacks in two other places (`:92-93` unsupported stack →
  recipe-only; `:108-109` no surfaces → ask the user), which shows the pattern is understood and
  simply wasn't extended to the verify phase.
- **Evidence**: "After implementing, run (or instruct the user to run): `npx tsc --noEmit` … The
  project's linter … A **layout sanity pass**" — with no branch for any of the three being absent.
- **Refactor**: a `<degradation>` block per dependency: detect → stated fallback → stated label in
  the output. `no tsconfig.json` → skip typecheck, state it; `pre-existing tsc/lint failures` →
  capture a baseline before editing and report only new failures; `no browser tools` → run the M3
  script-checkable subset and label the visual conditions unverified.

### M5 · MEDIUM — No canonical argument grammar
- **Where**: `skills/data-ui-craft/SKILL.md:21-27` (frontmatter) and `:111-119` (dispatch table)
- **Run-to-run consequence**: `mode` and `path` are both optional positionals with no stated order,
  precedence, or disambiguation rule. `/data-ui-craft src/tables` — is `src/tables` a mode the run
  failed to recognize, or the path? The skill's answer is "If ambiguous, ask via AskUserQuestion"
  (`:113`), which converts a grammar question into an interview turn that a one-line grammar block
  would have settled, and different runs will draw the ambiguity line differently.
- **Evidence**: "Read the `mode` arg (or infer from the command). If ambiguous, ask via AskUserQuestion."
- **Refactor**: a grammar block near the top of SKILL.md, in one place only:
  `/bespoke-agentics:data-ui-craft [mode] [path]` — `mode ∈ {audit, implement, audit-and-implement}`,
  default `audit-and-implement`; a first argument that is not one of those three literals is `path`;
  `path` defaults to the repo root; a `path` naming a file scopes to that file, a directory scopes
  to its tree.

### L1 · LOW — The severity palette is an uncited copy of ux-audit's, with no way to notice drift
- **Where**: `skills/data-ui-craft/references/report-format.md:5`, `:9-15`, `:81-86` (origin:
  `skills/ux-audit/references/report-format.md:12-16`)
- **Run-to-run consequence**: none today — verified identical across all five levels on 2026-07-27.
  The defect is structural: the file *claims* alignment ("The color system matches the plugin's
  `ux-audit` skill so reports look native side by side") while carrying fifteen hex literals with no
  pointer to where they came from and no check. When ux-audit's palette changes, this copy silently
  becomes a false claim, and the two reports stop looking native side by side — which is the whole
  stated reason the values were copied.
- **Evidence**: "The color system matches the plugin's `ux-audit` skill so reports look native side
  by side." followed by `| Critical | `#FEF2F2` | `#F87171` | `#991B1B` |` and the same values again
  in the `:root` block.
- **Refactor**: cheapest honest fix — add the `file:line` citation to the sentence. If the
  duplication must persist for standalone HTML rendering (it must), fold it into H3: the palette
  lives once in `assets/audit-report.html`, and `scripts/render_report.py --check-palette` diffs it
  against `skills/ux-audit/references/report-format.md:12-16` and warns on divergence.

### L2 · LOW — Two instructions are justified by a conversation the running model can't see
- **Where**: `skills/data-ui-craft/SKILL.md:135`, `:147`
- **Run-to-run consequence**: "Per the user's earlier choice this skill defaults to **both** formats"
  and "(by the user's earlier choice)" reference an authoring-time decision that no run has access
  to. The behavior is stated correctly alongside, so most runs proceed — but the phrasing invites a
  run to treat the choice as re-openable ("which formats did they want?") and gives no rule to fall
  back on if a user asks for something else.
- **Evidence**: "Per the user's earlier choice this skill defaults to **both** formats — read
  `references/report-format.md` and emit:"
- **Refactor**: state the rule as a rule — "emit both formats; `--format md|html|both` overrides,
  default `both`" — and delete the appeal to an unavailable conversation.

### L3 · LOW — Report paths are fixed at the repo root, so a second audit destroys the first
- **Where**: `skills/data-ui-craft/SKILL.md:138-139`, `references/report-format.md:3-4`
- **Run-to-run consequence**: `./data-ui-craft-audit.md` and `.html` are hardcoded with no scope or
  date in the name and no `--out`. Auditing a second surface, or re-auditing after fixes, silently
  overwrites the previous report — the before/after comparison the user most wants is the one the
  skill destroys. Sibling skills in this plugin write to `./reviews/<name>.md`, so this is also a
  house-style break.
- **Evidence**: "`./data-ui-craft-audit.md` — the in-repo, diff-friendly markdown report."
- **Refactor**: default to `./reviews/data-ui-craft-<scope-slug>.{md,html,json}` with an `--out`
  override, added to the M5 grammar block.

## Materialization opportunities

| Question answered per-run via LLM | Artifact | Generator | Placement | Staleness policy |
|---|---|---|---|---|
| How does this fix adapt to shadcn / MUI / AG Grid / Ant / Vue / Svelte / Angular / plain CSS? (M1, KM4) | `assets/stack-adapters.json` — `{concern: {stack: fix}}` | none — authored once from `patterns-react.md`; skill-invariant, no host to mine | inside the skill (`assets/`) | n/a — edited with the skill; the ten prose restatements are deleted, so there is nothing left to drift against |
| Which hex values encode each severity in the HTML report? (L1, KM5) | the palette inside `assets/audit-report.html` (H3), cited to its origin | `scripts/render_report.py --check-palette` compares against `skills/ux-audit/references/report-format.md:12-16` | inside the skill | check on render; warn (don't fail) on divergence — the source wins |

KM1–KM3 were not filed: host state is `no-host`, and both candidate host facts (the audited
project's stack, its data-display surfaces) fail the materialization test independently — the first
is recomputable in under a second (→ H1, a runtime script), the second is volatile working state
(anti-list). See `skill-re-data-ui-craft.host-context.json`.

## Essential-judgment register

Steps that stay with the model, on purpose.

| Step | Why scripting it would be wrong | Hardening applied instead |
|---|---|---|
| Applying `DF*`/`PD*`/`IU*` detection patterns (step 7) | The reference says it outright: patterns are *proxies* — "a present `aria-label` doesn't guarantee it's meaningful" (`audit-rules.md:75-79`). A grep for `aria-label` would produce confidently wrong findings. | H1 gives it a verified surface list; H4 gives it a machine-checkable output shape |
| Severity calibration and escalation (step 8) | "Context sets the bar" (`audit-rules.md:82-84`) — DF1 is Critical on a financial comparison table and Medium on an internal admin tool. A fixed severity map would produce mechanically alarming reports, the exact failure the calibration section exists to prevent. | `assets/rules.json` (H4) supplies the *default*; only the adjustment is judged, and the adjustment's reason becomes a JSON field |
| Inferring each field's data type from a column def (step 5) | `tier: string` is categorical, `notes: string` is free text, `orderId: string` is a copyable id — the distinction is semantic and lives in names and values, not types. | `find_surfaces.py` (H1) hands over the column defs with `file:line`; the model classifies |
| Respecting intent (step 7/14) | "Some 'violations' are deliberate product choices" (`audit-rules.md:86-88`) — a power-user surface that assumes memorized icons is a decision, not a defect. Only a human can settle it. | already gated: findings are presented to *confirm*, and the interview at step 14 is the gate |
| Spectrum placement — frequency × importance (step 7) | Requires knowing how often real users do a thing. It is not in the code. | the decision rule is stated explicitly (`audit-rules.md:45-48`); where frequency is unknowable, it becomes a question in the interview |
| Executive summary and finding titles (step 10) | Deliberate prose for a PM: "first-time users see a blank page that looks broken", not "IU4 violation" (`report-format.md:191-199`). Generated titles would defeat the purpose. | H3/H4 templatize the container so the judgment is the only thing being written |
| Applying in-place fixes to real code (step 17) | The whole point: minimum change, project conventions, preserve formatting, prefer the column def when a data layer exists. Every codebase differs. | already well-specified (`SKILL.md:189-196`); M3 adds a post-hoc assertion that the intended marker landed |
| Selecting Opportunities (step 9) | Taste — "Opportunities are genuine: … not filler" (`report-format.md:199`). A rule that fires on every timestamp column would fill the section with noise. | unchanged |

## What's already deterministic

- **Fifteen real `.tmpl` files**, not descriptions of components. The kit's *content* is fully
  pinned — only its assembly (H2) is improvised. This is TP2 already solved for the largest
  boilerplate surface in the skill.
- **The markdown report is a literal template with a worked example** (`report-format.md:24-63`),
  including realistic filled-in findings — TP1 and TP3 both satisfied.
- **A stable-ID rule catalog** (`audit-rules.md`) with detection cue, default severity, user-impact
  phrasing, and fix pointer per rule, plus documented escalation cues. This is what good judgment
  *input* looks like.
- **An explicit calibration section** (`audit-rules.md:72-91`) that names the failure mode
  ("an over-alarming audit gets ignored") and gives four concrete tie-break rules.
- **Zero ALL-CAPS directives** in 281 lines — measured, not estimated. The one strong prohibition
  ("never introduce a second styling system") is lowercase and load-bearing.
- **Correct progressive disclosure**: a 281-line spine plus a "read only what the current mode
  needs" pointer table (`SKILL.md:232-242`) mapping question → reference. No RB3 finding.
- **The destructive step is properly gated** (`SKILL.md:205-216`): audit → present → interview →
  implement exactly the accepted set, with "confirm, don't assume" stated at the gate.
- **Two fallbacks already defined** where they matter most: unsupported stack → recipe-only
  (`:92-93`), no surfaces found → ask the user (`:108-109`).
- **"One finding per root cause"** stated in both SKILL.md and the rule catalog — the single most
  effective anti-noise rule an audit skill can have.
- **Three evals** covering audit-only, audit-and-implement, and a recommendation-only conversation.
- **Zero broken internal references** (the inventory script's one hit is its own regex artifact).

## Deferred / out of scope

- **No fan-out for large codebases.** The audit walks every rule × every surface serially in one
  context (step 7). A repo with thirty data surfaces will exhaust context before the report is
  written, and nothing in the skill says what to do about it — parallel read-only agents per surface
  with a JSON return contract (which H4 would supply) is the natural fix. Not filed as a finding:
  no rule in the catalog covers scalability, and the fix is a design change rather than an
  extraction.
- **KM1–KM3 not assessable.** Host state is `no-host`; per the catalog's gating these could only be
  filed as capped-MEDIUM guidance, and both candidates failed the materialization test on their own
  merits, so nothing was filed. Re-run this audit from a real dashboard project to grade them
  properly.
- **The target's templates were not compiled.** No React/TypeScript toolchain was exercised in this
  run, so the thirteen `.tsx.tmpl` files were reviewed statically only. H2's barrel/partial-scaffold
  mismatch is a reading of the template text against `SKILL.md:168`, not an observed `tsc` failure —
  labelled **not executed**.
- **`inventory.py`'s broken-reference count was corrected by hand**, not by the script: its
  `REF_PATH` regex matches `templates/README.md` inside `templates/README.md.tmpl`. That is a defect
  in the *auditing* skill, not the target, and is out of scope here.
- **Nothing in `skills/data-ui-craft/` was modified.** `audit` mode stops at this report; the twelve
  refactors above are proposals, gated behind the Phase-4 interview that `--mode apply` or
  `--mode new-version` would run.
