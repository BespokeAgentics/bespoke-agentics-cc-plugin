# Kickoff contract: {FEATURE_NAME}

<!-- Derived from the plan at {PLAN_PATH} and confirmed by the human at Phase A.
     Extract from the plan verbatim where it carries structure; label every inferred element
     "(inferred)". Never contradict a locked decision — raise it as a Phase-A question instead. -->

- **Plan (authoritative):** {PLAN_PATH}
- **Run slug:** {RUN_SLUG}   ·   **Engine:** {workflow|agent}   ·   **Attempts:** {ATTEMPTS}
- **Confirmed:** {date} by {human}

## 1. Mission

{One paragraph: what this build delivers and why. The plan is the contract — read it first.}

## 2. Read before coding

1. This contract.
2. The plan: {PLAN_PATH}
3. {root CLAUDE.md, and each subsystem CLAUDE.md the workstreams touch}

## 3. Branch & working tree

- **Branch:** {feature-branch} (never a protected branch).
- **Pre-existing uncommitted changes:** {list} — preserved untouched, kept out of every code commit.
- **First action (if any):** {docs commit the plan calls for, before WS-0}.

## 4. Orchestration shape

Strictly sequential workstreams — one Workflow per workstream, `code → validate → commit`, no
worktrees, ≤{ATTEMPTS} attempts then halt, a human checkpoint between workstreams. WS-(n+1) begins
only after WS-n is committed and green.

## 5. Gates (run every workstream; expand where noted)

- {bun run typecheck / equivalent}
- {focused tests for the touched surface — never a bare full-suite run mid-build if the repo warns against it}
- {build}
- **Schema workstreams add:** {db:generate + db:migrate against an ISOLATED/disposable DB only, then reseed}
- **Final workstream adds:** {full test suite}
- **Any workstream touching the plan doc adds:** {wiki lint / plan lint}

## 6. Guardrails (a validate FAIL if violated)

- {allowed directories for new code}
- {naming rules}
- {the enforcement-layer rule — hard gates live at the authoritative layer, see §Hard gates}
- {single lockfile; never add a child lockfile}
- Conventional Commits — one commit per validated workstream; stage only that workstream's files.
- {any other plan-specific hard constraint}

## 7. Workstreams (sequential; each ends at its §5 gate)

| id   | scope (one line) | seams (file:line, grounded) | terminal gate |
|------|------------------|-----------------------------|---------------|
| WS-0 | {…}              | {…}                         | {…}           |
| WS-1 | {…}              | {…}                         | {…}           |
| …    | …               | …                           | …             |

## 8. Workflow skeleton

Driven by `assets/workflow-templates/workstream-loop.mjs`, invoked once per workstream with:

```
args = { ws, planPath, contractPath, gates, hardGates, commitStyle, attempts, models }
```

Nothing feature-specific is inlined in the template — it rides in `args` + the contract slice above.

## Hard gates

<!-- Server-authoritative invariants the validator must PROVE, not observe. "none" is valid — do not
     manufacture ceremony. Any "must never be possible" permission/visibility statement is usually one. -->

| id   | statement (must hold)  | enforced_at (authoritative fn/file) | proof_method |
|------|------------------------|-------------------------------------|--------------|
| HG-1 | {a crafted X cannot force Y} | {src/.../resolve.ts::fn}       | {craft input → assert output at enforced_at} |

## 9. Stop and ask the human when

- A validate FAIL survives {ATTEMPTS} code attempts.
- A migration would touch a shared/prod database.
- The plan is ambiguous, or a locked decision appears wrong (raise it — never silently deviate).
- A blocking open question the plan names becomes load-bearing: {list}.

## 10. Definition of done

- All workstreams committed and green.
- Every hard-gate proof on record (proved, with artifact).
- Every declared round-trip demonstrated: {e.g. hide → restore with data intact}.
- {plan status advanced; wiki lint clean; PR opened or handed back — only when the human asks}.
