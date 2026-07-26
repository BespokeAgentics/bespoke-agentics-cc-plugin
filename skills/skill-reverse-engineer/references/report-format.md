# Report format — `./reviews/skill-re-<name>.md`

Fill this template. Slots are `{{SCREAMING_SNAKE}}`; drop a section only where noted.

**Two forms — pick by rule, not feel.** When the verdict is 🟢, or there are fewer than 3
findings: use the **short form** — header block, metrics table, strengths, the findings (if
any), and a one-line essential-judgment note. Omit the step-executor matrix (its executor counts
already live in the metrics table) and every section that would be empty. Target ≤60 body lines;
a casual "give it a once-over" on a healthy target deserves a page, not a dossier. Otherwise use
the **full form** — everything below.

```markdown
# Skill reverse-engineering report — {{TARGET_NAME}}

- **Target**: {{TARGET_PATH}}
- **Mode**: {{MODE}}
- **Host**: {{HOST_STATE — one line, e.g. "host-grounded: cwd holds the wiki vault the target operates on"}}
- **Date**: {{ISO_DATE}}
- **Verdict**: {{🟢 already-hardened | 🟡 improvisation-dependent | 🔴 vibes-driven}}

{{ONE_PARAGRAPH_RATIONALE — tie the verdict to the CRITICAL/HIGH counts and the share of
mechanical steps currently owned by the model, not to vibes}}

## Metrics

| Metric | Value {{| After (apply modes only)}} |
|--------|-------|
| SKILL.md lines / words | |
| Bundled: scripts / references / templates / assets | |
| Steps: script-owned / model-mechanical / model-judgment / user-gate | |
| ALL-CAPS directives (MUST/NEVER/ALWAYS) | |
| Vague quantifiers at decision points | |
| Verify-verbs without a runnable check | |
| Broken internal references | |
| LLM-answered questions materializable (KM) | |

## Step-executor matrix

The reconstructed execution, in run order. Executor: `script` · `model-mechanical` ·
`model-judgment` · `user-gate`.

| # | Step | Executor | I/O form | Failure path | Finding |
|---|------|----------|----------|--------------|---------|
| 1 | {{STEP}} | {{EXECUTOR}} | {{IO}} | {{DEFINED_OR_NONE}} | {{RULE_ID_OR_—}} |

## Findings

{{Grouped by severity: CRITICAL → HIGH → MEDIUM → LOW. Add a table of contents when >10.
Each finding:}}

### {{RULE_ID}} · {{SEVERITY}} — {{ONE_LINE_TITLE}}
- **Where**: {{FILE:LINE}}
- **Run-to-run consequence**: {{WHAT_VARIES_OR_BREAKS_ACROSS_RUNS}}
- **Evidence**: {{SHORT_QUOTE}}
- **Refactor**: {{NAMED_ARTIFACT — script + argument signature | template + slots | schema +
  fields | check + command}}

## Materialization opportunities {{(only when ≥1 KM finding — otherwise omit the section)}}

{{One row per KM finding, mirroring host-context.json's knowledge_sources:}}

| Question answered per-run via LLM | Artifact | Generator | Placement | Staleness policy |
|-----------------------------------|----------|-----------|-----------|------------------|

## Essential-judgment register

Steps that stay with the model, on purpose. {{One row per model-judgment step:}}

| Step | Why scripting it would be wrong | Hardening applied instead |
|------|--------------------------------|---------------------------|

## What's already deterministic

{{Honest strengths — existing scripts, templates, contracts, gates that work. Never empty unless
the target truly has none.}}

## Deferred / out of scope

{{Findings the interview deselected, each marked `acknowledged — out of scope`, plus anything
labeled "not executed" / "not verified" and why.}}
```

## Apply / new-version addenda

Appended after Phase 6:

```markdown
## Before / after

{{The Metrics table's After column filled from re-running inventory.py, plus one paragraph on
what moved where.}}

## Diff summary {{(new-version mode only)}}

| File | Status | What changed |
|------|--------|--------------|
| {{PATH}} | added / modified / unchanged | {{ONE_LINE}} |

Output location: {{OUT_DIR}} — deliberately outside auto-registered skill paths. Swap it in by
replacing the original directory when satisfied.

## Verification

{{Each script created/modified: the exact invocation run in this session and its result. Each
generator: usage path, happy path against the real source, `--check` on the fresh artifact, and
the tamper test (modified scratchpad copy of a source → `--check` fails). The parity checklist
outcome. Anything not executed, labeled as such.}}
```
