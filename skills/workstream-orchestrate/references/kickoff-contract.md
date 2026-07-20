# Kickoff contract — the 10-section template & derivation rules

The kickoff contract is the skill's central artifact: a self-contained document, derived from the
plan and confirmed by the human at Phase A, that every workstream is built and judged against. It
generalizes a hand-authored orchestration kickoff into a repeatable form. Write it to
`{CONTRACT}` = `{RUN_DIR}/kickoff-contract.md` using `assets/templates/kickoff-contract.md`.

Two rules govern derivation:

- **Extract before you invent.** A mature plan already carries most of these sections (numbered
  workstreams, locked decisions, a surface spec, verification gates, a hard gate). Lift them verbatim
  and cite the plan. Only where the plan is silent do you **propose** structure — and you label every
  proposed element as your inference so the human can correct it at the confirm gate.
- **The plan stays authoritative.** The contract points at the plan; it never contradicts a locked
  decision. If a decision looks wrong, that is a Phase-A question, not a contract edit.

## The ten sections

Each section, and where it comes from:

1. **Mission** — one paragraph: what this build delivers + a pointer to the authoritative plan
   (path). Derived from the plan's objective/summary.
2. **Read before coding** — the ordered reading list every implementer gets: this contract, the plan,
   and the specific `CLAUDE.md`s the workstreams touch. Derived from the plan's seams + the subsystem
   map you built at pre-flight.
3. **Branch & working tree** — the feature branch (never a protected branch); how pre-existing
   uncommitted changes are preserved and kept out of code commits; any first-action docs commit the
   plan calls for. Derived from pre-flight `git status` + the plan.
4. **Orchestration shape** — restate the invariant: strictly sequential workstreams, one Workflow per
   workstream, `code → validate → commit`, no worktrees, ≤`ATTEMPTS` then halt, a human checkpoint
   between workstreams. Fixed by the skill; the contract records the chosen `ATTEMPTS` and engine.
5. **Gates** — the exact gate commands, with per-phase expansions (e.g. a schema workstream adds
   `db:generate` / `db:migrate` against an **isolated/disposable** DB; the final workstream adds the
   full test suite; a workstream touching the plan doc adds the wiki lint). Derived from repo
   `CLAUDE.md` + manifest at pre-flight; **never** a command that runs against a shared/prod database.
6. **Guardrails** — the hard constraints whose violation is an automatic validate FAIL: allowed
   directories, naming rules, the enforcement-layer rule, single-lockfile rule, "Conventional
   Commits, one per workstream". Lifted from the plan's constraints + repo conventions.
7. **Workstreams** — the ordered list WS-0…WS-N. For each: id, one-line scope, the seams (`file:line`,
   grounded), and its terminal gate. Extracted from the plan's workstream section, or proposed (and
   labeled) when the plan has none. Order encodes dependency — a schema/resolution layer precedes
   anything that consumes it.
8. **Workflow skeleton** — a pointer to `assets/workflow-templates/workstream-loop.mjs` and the `args`
   passed per workstream. Do **not** inline feature text here; the template is generic and everything
   specific rides in `args` + the contract slice.
9. **Stop-and-ask** — the escalation conditions: a validate FAIL that survives `ATTEMPTS`; a migration
   that would touch a shared/prod DB; an ambiguous or apparently-wrong locked decision; a blocking
   open question the plan names. Derived from the plan's open questions + the standing hard stops.
10. **Definition of done** — the whole-build completion criteria + verification: every workstream
    committed and green, every **hard-gate proof** on record, and every explicit round-trip the plan
    declares (e.g. hide→restore with data intact). Lifted from the plan's verification section.

## Hard gates within the contract

Sections 6 and 10 reference the hard gates, but record them once, explicitly, in a dedicated block
the validator reads (schema in `hard-gate-proofs.md`):

```
## Hard gates
| id   | statement (must hold)                                          | enforced_at (authoritative fn/file)     | proof_method |
|------|----------------------------------------------------------------|-----------------------------------------|--------------|
| HG-1 | a crafted per-item override cannot force a Not-available tab on | src/lib/.../resolve.ts::resolveTabs      | craft an override with the N/A tab set "show"; assert resolveTabs() output omits it |
```

## Confirming the contract (Phase A gate)

Present the human, in one `AskUserQuestion` batch, the choices that are expensive to get wrong:

- the **workstream list + order** (accept / reorder / split / merge),
- the **gate commands** (correct? missing a step? any that would hit a shared DB?),
- the **guardrails** (any missing hard constraint?),
- the **declared hard gates** (right invariant? right `enforced_at`?),
- the **commit convention** and the **checkpoint cadence** (`--no-confirm`, or pause each WS?).

Anything the plan already locked is shown as confirmation, not re-litigation. Anything you inferred is
flagged for correction. Only after confirmation do you write `{CONTRACT}` and enter Phase B.
