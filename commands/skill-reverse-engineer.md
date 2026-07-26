---
name: "bespokeagentics:skill-reverse-engineer"
description: "Reverse-engineer an existing Claude Code skill to make it more deterministic, robust, and less AI-reliant. Reconstructs what a run of the target skill actually does (step graph, each step classified script / model-mechanical / model-judgment via the distill test: would two competent runs be wrong to differ?), audits it against a rule catalog (DS* prose→script, TP* generated→template, CT* loose contracts, VF* judgment→check, AM* ambiguity, RB* robustness, KM* knowledge materialization) using a bundled deterministic inventory script, and grounds the audit in the HOST PROJECT it runs in — stack, data schemas, data stores, enumerated by a bundled host probe — so the target's per-run LLM lookups can be materialized into generated fact files (e.g. a configuration matrix mined from the host's schema, with provenance and staleness checks) that answer questions instead of deferring to the model. Writes a severity-rated, file:line-cited report with a step-executor matrix, a materialization-opportunities table, and an essential-judgment register (the AI-reliance that should STAY). Then — gated behind an interview (which facts to materialize, where artifacts live, refresh policy) — refactors in place or emits a hardened new version: mechanical procedures extracted into argument-validated scripts, stable host knowledge materialized via generator scripts, regenerated boilerplate frozen into templates, prose handoffs replaced with JSON contracts, eyeball checks replaced with runnable assertions. Behavior-preserving; every shipped script and generator is executed before it ships."
argument-hint: "'<skill-path-or-name>' [--mode audit|apply|new-version] [--out <dir>]"
allowed-tools: Skill(skill-reverse-engineer), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Skill Reverse-Engineer

Run the `skill-reverse-engineer` skill: reverse-engineer a target skill, audit where it relies
on per-run model improvisation, and (mode-dependent) restructure it so mechanical work executes
deterministically while its essential judgment stays with the model.

## Arguments

Parse from `$ARGUMENTS`:

```
'<skill-path-or-name>' [--mode audit|apply|new-version] [--out <dir>]
```

- `target` (required) — path to the skill directory, or a skill name to resolve against known
  skill locations (project `skills/`, `.claude/skills/`, `~/.claude/skills/`, plugin caches).
- `--mode` (optional) — `audit` writes the read-only report only; `apply` refactors the target
  in place after the interview gate; `new-version` never touches the original and emits a
  hardened copy plus a diff summary. When omitted, the interview asks.
- `--out` (optional, new-version only) — output directory. Default `./skill-re-out/<name>/`,
  deliberately outside auto-registered skill paths so the copy never competes with the original
  for triggering.

## Process

Invoke the `skill-reverse-engineer` skill and forward `$ARGUMENTS`. The skill will:

1. **Inventory** — resolve the target, run `scripts/inventory.py` for deterministic baseline
   metrics (prose/code split, ALL-CAPS directive counts, vague quantifiers, verify-verbs,
   broken internal references, script hygiene), and `scripts/host_probe.py` to enumerate the
   host project's grounding candidates (manifests, schema sources, wiki vaults, data-store
   evidence), then classify host state: `host-grounded` / `host-generic` / `no-host`.
2. **Reconstruct** — read every file and build the step graph of what one run actually does,
   classifying each step's executor: `script` · `model-mechanical` · `model-judgment` ·
   `user-gate`, and recording what stable host knowledge each model step consumes — written to
   the `host-context.json` sidecar.
3. **Audit** — walk the rule catalog against the step graph (KM rules with host-context.json in
   hand); every finding carries rule ID, severity, `file:line`, the run-to-run consequence, and
   a *named* refactor artifact. Builds the essential-judgment register alongside — the steps
   that must not be scripted.
4. **Report** — `./reviews/skill-re-<name>.md`: verdict (🟢/🟡/🔴; 🟢 uses the short form),
   host state, metrics, step-executor matrix, findings, materialization-opportunities table,
   judgment register, strengths, deferred. `audit` mode stops here.
5. **Interview** — mode (if not given), appetite (DS* only → full catalog), per-finding
   confirmation, judgment-register overrides, and materialization choices (which facts,
   artifact placement, refresh policy). No file touched before this gate.
6. **Apply** — extraction in order DS → KM → TP → CT → VF → AM/RB, per the refactor quality bar
   (scripts validated + executed, generators with `_provenance` + `--check`, templates with
   explicit slots, keep-the-why rewrites, behavior-preserving parity checklist).
7. **Verify** — run every created/modified script and generator (including the drift-check
   tamper test), fresh-eyes read of the result, reference integrity, re-run inventory for the
   before/after table (+ diff summary in new-version mode).

## Output

`./reviews/skill-re-<name>.md` (read-only report, always) and — only past the interview gate —
either in-place refactors (`apply`) or a hardened copy at the output directory (`new-version`).
The original is never modified in `audit` or `new-version` modes. Wiki-ingested when a vault
exists.
