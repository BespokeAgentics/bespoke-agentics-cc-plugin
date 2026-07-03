# Deprecating the Old Code

The migration isn't done when the machine works — it's done when the old state logic can no longer
be reached, imported, or accidentally resurrected. Half-migrated features are worse than
unmigrated ones: two sources of truth for the same state.

## Interview decision (Phase 3)

Ask the user's appetite up front; it shapes the plan:

- **Delete outright** (default for component-local state) — the old `useState`/`useEffect`/handler
  logic is removed in the same PR that wires the machine. The git history is the archive.
- **Deprecate, then delete** (for exported/shared state: hooks, store slices, utils with outside
  consumers) — mark `@deprecated` with a pointer to the machine and a removal note, migrate
  consumers, delete in a follow-up. The plan lists the consumers (from the Phase 1 blast-radius
  sweep) and the removal condition.
- **Feature-flag both paths** (only for high-risk, high-traffic surfaces, and only if the user asks)
  — note the real cost in the plan: every future change lands twice until the flag dies, and the
  flag itself is a new implicit state. Mark 🟡 and record the flag-removal criterion.

## The deprecation checklist (goes in the plan, executed in Phase 5 step 5)

Build it from the Phase 1 behavior map — it already lists every state variable, effect, handler,
and consumer with `file:line`. For each item: **replaced by** (machine state/context/actor/guard) →
**action** (delete / deprecate / keep). Items that are *not* replaced need an explicit reason
("kept: unrelated to this state logic").

Categories to sweep:

1. State variables and reducers the machine replaced.
2. Effects the machine's actors replaced — including their cleanup functions and refs
   (`isMountedRef` and friends usually die here).
3. Handlers whose bodies moved into the machine — the handler stays but shrinks to `send(...)`;
   delete any now-dead helpers it called.
4. Derived-state utilities (`getStatus(flags)`-style functions) — replaced by `state.matches`.
5. Types for the old state shape.
6. Tests superseded per `references/testing.md` (port intent before deleting).
7. Store slices / context providers that only existed to host this state.

## Verification

- **Grep-verify**: every deleted symbol greps to zero references; every `@deprecated` symbol greps
  to zero *new* references (only the known consumers listed in the plan).
- Typecheck + lint + full relevant test suite green.
- No `eslint-disable`/`@ts-expect-error` added to paper over half-removed code.
- The final summary reports the count: `{N} old state vars retired, {N} files cleaned, {N} deferred
  (deprecated, removal tracked in {plan section})`.
