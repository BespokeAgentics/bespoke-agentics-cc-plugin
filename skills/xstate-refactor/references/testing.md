# Deterministic Tests for XState Objects

Every machine/actor this skill introduces ships with tests in three layers. The machine makes all of
them deterministic: behavior is a graph, so coverage is enumerable, and effects are actors, so they
are mockable at the seam.

Use the project's detected runner (Vitest / Jest / `bun test`) and its conventions for file
placement. Test files: `{feature}.machine.test.ts(x)`.

## Layer 1 — Model-based path coverage (`xstate/graph`)

XState v5's model-based testing lives in **`xstate/graph`** (the standalone `@xstate/test` and
`@xstate/graph` packages are deprecated — import from the main package). `createTestModel`
generates every path through the machine; executing them guarantees every state and transition is
exercised — no hand-picked scenarios, no missed branches.

```ts
import { createTestModel } from 'xstate/graph';
import { featureMachine } from './feature.machine';

// Test against a pure version: effects stubbed at the actor seam so paths
// resolve deterministically and instantly.
const testMachine = featureMachine.provide({
  actors: {
    submitOrder: fromPromise(async () => stubOrderResult),
  },
  delays: { retryDelay: 0 },
});

const model = createTestModel(testMachine);

model.getShortestPaths().forEach((path) => {
  it(path.description, async () => {
    await path.test({
      states: {
        // one assertion block per state — often the UI coverage assertions, layer 3
      },
      events: {
        // how to fire each event against the system under test
      },
    });
  });
});
```

- **Known constraint**: `createTestModel` rejects machines containing invocations. When the machine
  invokes actors (most do), use the path generators directly — `getShortestPaths(testMachine)` /
  `getSimplePaths(testMachine)` from `xstate/graph` — and replay each path against a live
  `createActor(testMachine)` with the stubbed actor seam, asserting state at each step. Same
  coverage guarantee, no wrapper. Don't strip `invoke`s from the machine just to satisfy
  `createTestModel`; test the machine you ship.
- `getShortestPaths()` covers every reachable state minimally; add `getSimplePaths()` when
  transition *sequences* matter (e.g. retry-then-succeed vs. succeed-first must both be exercised).
- Events carrying payloads need event cases supplied so guards' both branches are reachable —
  check path coverage against the guard table from `state-model.md`.
- If a state is unreachable in the test model, that's a design finding (dead state or missing
  event case), not something to work around. Surface it.

## Layer 2 — Unit tests on machine logic (`createActor`)

Pure, no framework, no DOM. Target the specifics the path tests treat generically:

```ts
import { createActor } from 'xstate';

it('gives up after MAX_RETRIES failures', () => {
  const actor = createActor(testMachine).start();
  actor.send({ type: 'SUBMIT' });
  // drive failure events...
  expect(actor.getSnapshot().matches('failure.permanent')).toBe(true);
  expect(actor.getSnapshot().context.retries).toBe(3);
});
```

Cover: each guard at its boundary (retries at `MAX-1`, `MAX`), context evolution per action,
initial state + input handling, and — for behavior divergences confirmed in the interview — one
test per divergence, named after it (`it('no longer allows double-submit (divergence #2)')`). These
divergence tests are the migration's receipts.

For promise/callback actors with real logic of their own, test them directly as functions where
possible; the machine tests already cover their integration via stubs.

## Layer 3 — UI state-coverage tests (Testing Library)

One assertion block per machine state, mirroring the coverage matrix row for row: render the
component, drive it into each state, assert the matrix's "what the user sees" column.

```tsx
it('retrying: shows retry banner with attempt count, inputs disabled', async () => {
  render(<Feature />);   // or inject a pre-configured actor if the component accepts one
  await user.click(screen.getByRole('button', { name: /submit/i }));
  // deterministic failure via the stubbed actor seam...
  expect(await screen.findByText(/retrying \(attempt 2/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/email/i)).toBeDisabled();
});
```

- Drive state through **real events** (clicks, resolved/rejected stub promises), not by poking
  internal state — these tests double as integration proof of the wiring.
- Determinism sources: stub actors at the `provide()` seam, zero delays via `delays` overrides, fake
  timers for `after` transitions. No real network, no real clocks, no sleeps.
- The strongest pattern combines layers 1+3: pass the Testing Library assertions as the `states`
  blocks of the path test, so *every generated path* validates the UI at every stop. Do this when
  the component renders cheaply; fall back to separate per-state tests when setup is heavy.

## Old tests as the equivalence net

Existing tests over the old implementation are run before the migration (record the baseline) and
after wiring (they must still pass, except tests asserting behavior the user explicitly chose to
change — update those and annotate with the divergence number). Only delete an old test when its
subject was deleted; port its intent first if the machine still owns that behavior.
