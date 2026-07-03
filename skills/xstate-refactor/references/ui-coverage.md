# State ↔ UI Coverage

The rule this skill enforces: **every state the machine can be in has a decided visual answer.**
"Decided" includes "intentionally invisible" — but only when a human said so.

## The coverage matrix

One row per machine state (leaf states; composite states get a row only if they add UI of their
own). Built as a draft in Phase 2, resolved in the Phase 3 interview, finalized in the plan, and
verified against the wired UI at the end of Phase 5.

```markdown
| State | What the user sees | Interactive elements & their enabled/disabled state | Transition feedback | Source | Status |
|-------|--------------------|-----------------------------------------------------|---------------------|--------|--------|
| idle        | Empty form, Submit enabled          | Submit ✓, Cancel ✗ | —              | Form.tsx:42 | 🟢 exists |
| submitting  | Spinner on button, inputs disabled  | all ✗              | button spinner | Form.tsx:58 | 🟢 exists |
| retrying    | ⚠ nothing today                     | ?                  | ?              | —           | ⚠ GAP |
| failure     | Error toast                         | Submit ✓ (Retry)   | toast slide-in | Form.tsx:71 | 🟢 exists |
```

Status values: 🟢 exists (mapped from behavior map, `file:line`) · 🟡 to build (user chose a
treatment in the interview) · ⚪ intentionally invisible (user-approved, with the reason recorded) ·
⚠ GAP (unresolved — blocks Phase 5 sign-off; lives under Open Questions if deferred).

## Transition points, not just states

States lasting >100ms need *entry* feedback (the user did something; the UI acknowledged it).
Check specifically:

- **Instantaneous transitions** the user initiated (button press → new state): does anything
  visibly change at the moment of the event, or only after an async settle?
- **Self-transitions and internal retries**: `retrying` that looks identical to `loading` hides
  information the machine now has — surface the retry count from context, or get explicit approval
  to hide it.
- **Terminal/final states**: does the UI settle somewhere sensible, or strand the user on a
  spinner that stopped meaning anything?
- **Error taxonomy**: if the machine distinguishes `failure.network` from `failure.validation`,
  the UI should too — or the user approves collapsing them.

## Wiring rules (React / @xstate/react)

- Component reads state via `useMachine(machine)` (local) or `useSelector(actorRef, sel)` (shared
  actor from context/props). Prefer `useSelector` with narrow selectors in consumers so unrelated
  state changes don't re-render them.
- **Render decisions use `state.matches('...')`** (or destructured flags derived from it once,
  near the top) — never re-derive machine-truths from context (`context.error !== null` as a proxy
  for the failure state is how implicit state creeps back in).
- Sends replace the old handlers one-for-one: handler bodies shrink to `send({ type: 'SUBMIT' })`
  and the logic they held moves into the machine (guards/actions/actors). If a handler still
  contains branching after the swap, that branching probably belongs in the machine — flag it.
- Disabled/enabled props come from the matrix's column, ideally via `state.can({ type: 'SUBMIT' })`
  so the UI can never offer an event the machine would ignore.
- For non-React frameworks, the same principles apply through the framework package
  (`@xstate/vue`, `@xstate/svelte`, `@xstate/solid`) or a plain `createActor` + subscribe wrapper —
  see `references/setup.md`.

## Verification (end of Phase 5)

For each matrix row: locate the wired render path (`file:line`), confirm the status column is
🟢/⚪ (no 🟡 left unbuilt, no ⚠ unless user-deferred), and confirm a UI coverage test exists per
`references/testing.md`. The matrix in the final plan is updated to reflect reality — it doubles as
the feature's state-UI documentation going forward.
