# Rule catalog — skill-reverse-engineer

Each rule: what to look for (detection cues you can grep or spot while reading), why it matters
(the run-to-run consequence), and the refactor recipe (the artifact that should exist instead).
Severity is assigned per finding using the definitions in SKILL.md — the same rule can be
CRITICAL in one skill and LOW in another depending on how load-bearing the step is.

The governing test, applied before filing any finding against a `model-*` step:
**would two competent runs, given the same inputs, be wrong to differ?**
Wrong-to-differ → mechanical → this catalog applies. Acceptable-to-differ → judgment → it goes in
the essential-judgment register instead, and the only legitimate findings against it are about
its *inputs* (underspecified context) or its *outputs* (no machine-checkable form) — not about
scripting the judgment itself.

## Table of contents

- [DS — Determinism: prose → script](#ds)
- [TP — Templates: generated → asset](#tp)
- [CT — Contracts: loose I/O](#ct)
- [VF — Verification: judgment → check](#vf)
- [AM — Ambiguity: divergent branching](#am)
- [RB — Robustness & bloat](#rb)
- [KM — Knowledge materialization: re-derived → artifact](#km)

---

<a name="ds"></a>
## DS — Determinism: prose → script

### DS1 — Mechanical procedure described as prose
**Cues**: a numbered or bulleted sequence of concrete operations (run X, then transform Y, then
write Z) where every operation's correct output is unique; shell commands quoted inline as
things the model should type; phrases like "then run", "use ffmpeg to", "extract the", "parse
the output and".
**Why**: the model re-derives the procedure every run. Each derivation costs tokens and can pick
different flags, orderings, or edge-case handling — variance that propagates into everything
downstream. A model update changes the derivation silently.
**Recipe**: bundle the procedure as one script in `scripts/` with an argument signature covering
the parameterizable parts. The SKILL.md step becomes: invoke the script + the *why* prose. Rule
of thumb: three or more concrete operations in sequence with no judgment between them = one
script.
**Example**: "Extract frames every N seconds with ffmpeg, name them frame-0001.jpg…, then write
a manifest listing each frame with its timestamp" → `scripts/extract_frames.sh <video> <interval>
<outdir>` that does all three and prints the manifest path.

### DS2 — "Write a script that…" / per-run helper authorship
**Cues**: the skill instructs the model to author a helper at run time ("write a small script
to", "create a python script that"); or eval/transcript evidence that runs keep writing the same
helper independently.
**Why**: the clearest possible signal that the script should ship with the skill. Per-run
authorship is the maximum-variance, maximum-cost version of DS1 — every run gets a different
implementation with different bugs.
**Recipe**: write the helper once, properly (see refactor-recipes.md quality bar), put it in
`scripts/`, and change the instruction to invoke it.

### DS3 — Model-performed parsing, counting, or aggregation
**Cues**: "read the output and count", "parse the JSON and find", "go through each file and
tally", "aggregate the results into"; any step where the model transforms structured data by
reading it.
**Why**: models miscount and mis-extract at low but nonzero rates, and the rate varies with
context pressure. A jq/python one-liner is exact every time and frees context for the judgment
steps.
**Recipe**: a script (or a documented one-liner the skill quotes verbatim as *the* command, not
as an example to adapt) that emits the aggregate; the model consumes the result, not the raw data.

### DS4 — Scaffolding described instead of shipped
**Cues**: "create the following directory structure", "create these files", followed by a tree
or file list; setup phases that materialize the same skeleton every run.
**Why**: structure drift — runs create slightly different trees, and every downstream "read X
from Y" instruction inherits the inconsistency.
**Recipe**: a scaffold script, or a template tree in `templates/` copied with one command.

---

<a name="tp"></a>
## TP — Templates: generated → asset

### TP1 — Output document structure described in prose
**Cues**: "the report should contain the following sections", "write a document with", a
described-not-shown structure for any recurring output (report, plan, spec, JSON file).
**Why**: every run regenerates the skeleton — section names, ordering, and formatting drift; any
tool or person consuming the output downstream can't rely on its shape.
**Recipe**: a literal template file (in `templates/` or a `<template>` block in a reference) with
`{{PLACEHOLDER}}` slots. Instruction becomes "fill this template" — the judgment (the content)
stays with the model; the skeleton stops being regenerated. If the skill already shows the exact
structure in a fenced block ("ALWAYS use this exact template"), that is a template in spirit —
file a LOW finding only if it drifts from what other parts of the skill describe.

### TP2 — Boilerplate regenerated per run
**Cues**: config files, HTML shells, CSS, component skeletons, hook scripts that the skill has
the model write from a description each run.
**Why**: same as TP1 but worse — boilerplate is long, so the cost is high and subtle
regeneration bugs (a missing meta tag, a renamed class) are hard to spot.
**Recipe**: ship the artifact in `templates/`/`assets/` verbatim; parameterize only what varies.

### TP3 — Example-by-description
**Cues**: "for example, the output might look something like…", paraphrased examples, or no
example at all for a nontrivial output format.
**Why**: a literal worked example pins format details prose never captures (whitespace, field
order, escaping). Its absence is where runs diverge on the fiddly bits.
**Recipe**: one real, complete example file the model can pattern-match against.

---

<a name="ct"></a>
## CT — Contracts: loose I/O

### CT1 — Phase handoffs as prose in context
**Cues**: phase N produces "findings"/"analysis"/"a list" that phase N+1 consumes, with no file
or schema in between; resumability impossible because intermediate state lives only in context.
**Why**: the handoff shape is re-invented every run; a compaction or interruption loses the
state; nothing can validate that phase N produced what phase N+1 needs.
**Recipe**: a named intermediate file with a stated schema (JSON preferred). Phase N writes it,
phase N+1 reads it, and a VF-style check can validate it.

### CT2 — Loose subagent delegation
**Cues**: "launch an agent to analyze X", "have a subagent review Y" with no verbatim prompt
packet and no structured return contract.
**Why**: the orchestrating model composes a different prompt each run, and the subagent returns
free-form prose the orchestrator must re-interpret — two extra layers of variance.
**Recipe**: a verbatim prompt template (with `{{SLOTS}}`) and an explicit return contract ("return
JSON with fields …"). The skill's own files carry the packet; the run only fills slots.

### CT3 — Arguments parsed by inference
**Cues**: `$ARGUMENTS` or flags interpreted from a loose description; defaults undefined;
flag interactions unspecified.
**Why**: two runs parse the same invocation differently; users can't predict behavior.
**Recipe**: a canonical grammar block (exact flags, defaults, precedence) early in the skill, in
one place only.

---

<a name="vf"></a>
## VF — Verification: judgment → check

### VF1 — Eyeball checks where a runnable check exists
**Cues**: "verify that", "ensure", "confirm", "check that", "make sure" followed by a condition
that is objectively decidable (a file exists, a schema validates, a grep matches zero times, an
exit code is 0) but with no command given.
**Why**: model self-verification is the weakest link in any skill — the model that made the
mistake reviews the mistake, under the same blind spot. A command is immune.
**Recipe**: state the exact check (command + expected result) next to the claim, or fold it into
a verify script. Only conditions that are objectively decidable qualify — "verify the prose is
clear" is judgment and belongs in the register, not here.

### VF2 — Untestable success criteria
**Cues**: a "done when" / quality bar / acceptance section whose items have no observable form
("the output is high quality", "everything works").
**Why**: the skill cannot know it succeeded; failures ship silently.
**Recipe**: rewrite each criterion as an observation: a command and its expected output, a file
and its required properties, or an explicit "user confirms X" gate.

### VF3 — Self-grading without independence
**Cues**: the skill has the same context that produced an artifact also grade it, where a script
or a fresh-context agent could grade instead.
**Why**: shared blind spots. Independence is the cheapest available integrity gain.
**Recipe**: programmatic checks first; where judgment grading is genuinely needed, a
fresh-context subagent with a verbatim rubric (which also makes this a CT2 fix).

---

<a name="am"></a>
## AM — Ambiguity: divergent branching

### AM1 — Vague quantifiers at load-bearing decision points
**Cues**: "as needed", "if appropriate", "when relevant", "where necessary", "if applicable" —
*at a point where the choice changes the deliverable*. (In incidental positions these are LOW
noise, not findings.)
**Why**: this is exactly where two runs diverge: each run resolves the vagueness differently.
**Recipe**: replace with the actual condition ("when the target has more than N surfaces…", "when
`--flag` is set…"), or an explicit user gate if the condition is genuinely the user's call.

### AM2 — Undefined failure paths
**Cues**: steps that depend on a tool, key, network, or file with no stated behavior when it's
absent; no degradation section; "run X" with no "and if X fails…" anywhere.
**Why**: each run improvises its own fallback — skip silently, halt, or fake it. The silent-skip
variant corrupts deliverables without a trace.
**Recipe**: a degradation section (or inline branch) per dependency: detect → stated fallback →
stated labeling in the output ("transcript unavailable → frames-only analysis, noted in report").

### AM3 — Drift between SKILL.md and its references
**Cues**: the same procedure, format, or rule stated in two places with differences; a reference
describing an older version of a flow the SKILL.md has since changed.
**Why**: which version a run follows depends on read order — nondeterminism by contradiction.
**Recipe**: single source of truth; the other location points to it.

### AM4 — Load-bearing order left implicit
**Cues**: steps whose order matters (build before verify, gate before edit) listed without
explicit sequencing, or scattered across sections.
**Why**: reordering by a run isn't visibly wrong until the consequence lands later.
**Recipe**: explicit ordered phases; where a gate exists, state the invariant ("no edit before
this gate") once, at the gate.

---

<a name="rb"></a>
## RB — Robustness & bloat

### RB1 — ALL-CAPS directives standing in for structure
**Cues**: MUST / NEVER / ALWAYS clusters around a behavior the skill could enforce with a gate,
check, or script instead of emphasis.
**Why**: shouting is a compliance hope; a check is a guarantee. Density of caps is a reliable
proxy for missing structure.
**Recipe**: convert each load-bearing MUST into its enforcement (a gate step, a VF check, a
script that refuses). Keep the prose explanation of *why*; drop the volume.

### RB2 — Instructions not pulling weight
**Cues**: restating model defaults ("be helpful", "write clean code"), motivational filler,
duplicated guidance, long preambles before the first actionable step.
**Why**: context is the skill's budget; every non-load-bearing line dilutes the load-bearing
ones and pushes real instructions toward the truncation horizon.
**Recipe**: delete. If unsure whether a line matters, it doesn't.

### RB3 — Progressive-disclosure violations
**Cues**: SKILL.md far beyond ~500 lines with no layer of references; or the inverse — critical
always-needed rules buried in a reference the skill only "suggests" reading.
**Why**: everything-in-one-file loads unneeded detail every trigger; critical-detail-in-optional
-reference means some runs never load it.
**Recipe**: SKILL.md holds the always-needed spine + explicit pointers ("read X before phase Y");
references hold the per-situation depth.

### RB4 — Fragile bundled scripts
**Cues**: existing scripts with no shebang, no usage/argument validation, no meaningful exit
codes, silent failure (`|| true`, bare `except: pass`), or output formats no instruction
documents.
**Why**: a script that fails silently is worse than prose — the run trusts it blindly.
**Recipe**: the script quality bar in refactor-recipes.md: usage on bad args, nonzero exit on
failure, documented output.

### RB5 — Hardcoded environment assumptions
**Cues**: absolute paths, `/tmp` (vs. the scratchpad), OS-specific commands with no alternative
(`sed -i ''`, `open`, `pbcopy`), assumed tools with no availability check or degradation.
**Why**: the skill works on its author's machine and nowhere else; failures surface as confusing
mid-run errors.
**Recipe**: parameterize paths, detect-and-degrade per tool (pairs with AM2), note platform
requirements in frontmatter `compatibility` when real.

---

<a name="km"></a>
## KM — Knowledge materialization: re-derived → artifact

The host-grounded family. The qualification test, anti-list, `_provenance` format, placement
policy, and honesty labels live in `references/materialization.md` — read it before filing or
fixing anything here. A KM finding proposes: a generator script (ships in the skill) that mines
a host source into a JSON artifact the skill consults at runtime, instead of the model
re-deriving (or worse, half-remembering) the answer every run.

**Host gating**: KM1–KM3 require host evidence — file them from the `knowledge_sources` rows of
`host-context.json`. In `no-host` state they may only be filed as *host-dependent guidance*
(severity-capped MEDIUM, phrased "verify in a deployment"), never as confirmed defects. KM4 and
KM5 are host-independent and file normally in any state.

### KM1 — Per-run re-derivation of stable host facts
**Cues**: "detect the project's stack/framework", "figure out the project's conventions",
"inspect the manifests and determine", "identify which library the project uses" — performed
fresh on every run of the target skill.
**Why**: tokens and latency spent every run on an answer that changes on release cadence, not
run cadence — and derivation variance: two runs that classify the stack differently diverge on
everything downstream.
**Recipe**: generator script mining manifests/lockfiles/config → `facts.json` with
`_provenance`; the consuming step reads the artifact via the fallback ladder.
**Anti-cue**: the fact is answered by one compact machine-readable file → point the instruction
at that file; do not file (or file LOW with recipe "consult the source directly").

### KM2 — LLM inference where a lookup could be mined
**Cues**: the target has the model answer an enumerable question per run — "choose the
appropriate category", "use the project's valid status values", "map the component to its
route", "pick the right config key" — where the value set is finite and defined somewhere in
host source (enums, type unions, registries, routing/naming conventions).
**Why**: the model answers from priors plus partial context, wrong at a nonzero,
context-pressure-dependent rate; a lookup is exact and free. This is the "configuration matrix
in JSON that answers the question instead of deferring to an LLM" case.
**Recipe**: configuration-matrix JSON mined from the defining source, consulted at the decision
point. Both the distill test and the materialization test must pass.

### KM3 — Data-schema knowledge re-inferred per run
**Cues**: "inspect the database schema", "read the models to understand the shape", "infer the
API response format" — against stable sources (`prisma/schema.prisma`, `migrations/`, `*.sql`,
OpenAPI/Swagger specs, zod schemas, GraphQL SDL).
**Why**: schema inference is expensive (many files) and error-prone (stale migrations vs current
state); runs can disagree on required/nullable/enum membership.
**Recipe**: schema-snapshot artifact — prefer stack-native introspection output (`prisma db
pull`, `pg_dump --schema-only`, the OpenAPI file itself) over hand-parsing — with `_provenance`;
the consuming step reads the snapshot.

### KM4 — Prose decision tables
**Cues**: "if the stack is X do Y; if Z do W" chains; conditional prose enumerating cases over a
stable axis; the same mapping restated in several places.
**Why**: prose branching is re-read and re-applied each run, misapplied under context pressure,
and prose copies drift when one is edited.
**Recipe**: JSON decision matrix (condition → action) shipped **inside the skill** — it is
skill-invariant, so it needs no host. Consult instruction + the why-prose stay.

### KM5 — Hardcoded host snapshot without provenance
**Cues**: literal enum values, schema field lists, taxonomies, paths, or thresholds embedded in
the skill's text that mirror (or once mirrored) a host source — with no citation and no
regeneration path. Detection: spot enum-like literal sets in the target, then look for the
defining source in the host; drift between them is the smoking gun.
**Why**: a cache that doesn't know it's a cache — authoritative-looking and silently stale,
strictly worse than re-derivation (which is at least current). KM5 is also the named failure
mode of a *bad* KM refactor: any materialized artifact shipped without `_provenance` and a drift
check is itself a KM5 defect, which is what keeps over-materialization self-indicting.
**Recipe**: replace the hardcoded values with a generated artifact carrying `_provenance` +
`--check`, or with a direct read of the defining source. Never ship an unlabeled snapshot.

---

## Filing discipline

- **One finding per root cause.** A 40-line prose procedure is one DS1, not forty.
- **Cite the deepest file.** If SKILL.md and a reference both exhibit it, cite where the fix
  lands; mention the other location.
- **Name the artifact.** Every finding's recipe names the concrete script/template/schema with
  its signature or slots — "make this deterministic" is not a finding.
- **Cadence decides the family.** Correct output changes per run/input → DS3 (runtime script,
  runs every time). Stable across runs against the same host → KM (generator runs rarely,
  artifact consulted every time). Within-run handoff → CT1. Regenerated *output* boilerplate →
  TP; re-derived *input* knowledge → KM. File once, under the family whose recipe you would
  actually apply; cross-reference the rejected reading.
- **No derived artifact over a compact machine-readable source.** If one small file already
  answers the question, the recipe is "point at the source" — see the anti-list in
  `references/materialization.md`.
- **Respect deliberate looseness.** Skills sometimes leave room on purpose (a creative-direction
  skill describing taste, an interview skill leaving question phrasing open). If the looseness
  is plausibly the point, classify it as judgment and let the interview settle it — do not file
  it as a defect.
