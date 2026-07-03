# XState Setup & Environment

## Detection (Phase 0)

Read `package.json` (all workspaces if a monorepo — check the target package's own manifest plus
the root) and the lockfile:

- `xstate` present? Record the major version. **v5 is this skill's target.**
- Framework binding present? `@xstate/react` / `@xstate/vue` / `@xstate/svelte` / `@xstate/solid`.
- Deprecated packages present? `@xstate/test`, `@xstate/graph` as standalone deps — both are folded
  into the main `xstate` package in v5 (`import ... from 'xstate/graph'`). Plan their removal.
- Detect the package manager from lockfile (`bun.lock`→bun, `pnpm-lock.yaml`→pnpm,
  `yarn.lock`→yarn, `package-lock.json`→npm) and use it — never mix.

## Installing (Phase 5, when missing)

```sh
# core (framework-agnostic)
<pm> add xstate

# React projects
<pm> add xstate @xstate/react
```

No config files, no build plugins required. TypeScript ≥5 recommended for `setup()` inference. In a
workspace monorepo, install into the target package (e.g. `bun add xstate --filter=<pkg>` or run in
the package dir), not the root, unless the repo's convention is hoisted root deps — follow what the
existing deps do.

Version-pin conventions: match the repo (exact vs caret) by looking at neighboring entries.

## If the project is on XState v4

Do not silently mix idioms — v4 `Machine()`/`interpret()` and v5 `setup()`/`createActor` differ in
typegen, actions API, and actor model. Put the decision in the plan and the interview:

1. **Upgrade to v5 first** (preferred when v4 usage is small): follow the official migration guide
   (stately.ai/docs/migration); the new machine and all tests use v5 natively.
2. **v5 alongside v4** via package alias (`"xstate5": "npm:xstate@5"`) when v4 usage is too large to
   migrate now. Note the cost: two runtimes, awkward imports. Mark 🟡 in the plan.
3. **Write this machine in v4** — only if the user insists; this skill's templates and testing
   approach assume v5, so flag reduced support.

## v5 idioms this skill generates

```ts
import { setup, createActor, assign, fromPromise } from 'xstate';

export const featureMachine = setup({
  types: {
    context: {} as FeatureContext,
    events: {} as FeatureEvent,
    input: {} as FeatureInput,
  },
  actors: {
    submitOrder: fromPromise(async ({ input }: { input: OrderDraft }) => api.submit(input)),
  },
  guards: {
    canRetry: ({ context }) => context.retries < MAX_RETRIES,
  },
  actions: {
    incrementRetries: assign({ retries: ({ context }) => context.retries + 1 }),
  },
}).createMachine({
  id: 'feature',
  initial: 'idle',
  context: ({ input }) => ({ retries: 0, draft: input.draft, error: null }),
  states: { /* ... */ },
});
```

- All implementations declared in `setup()` — string references in the machine body, so tests can
  `machine.provide({...})` at the seam.
- Typed `context`/`events`/`input` via `setup({ types })`; no typegen files.
- Effects: `fromPromise` / `fromCallback` / `fromObservable`; child machines invoked or spawned.
  `invoke` for state-scoped effects (auto-cleanup), `spawnChild`/`spawn` in `assign` for
  longer-lived actors.

## Framework wiring quick reference

- **React** (`@xstate/react`): `useMachine(machine, { input })` for component-local;
  `createActorContext(machine)` for subtree-shared; `useSelector(actorRef, selector)` for consumers
  (narrow selectors = fewer re-renders); `useActorRef` when only sending. `useActor(logic)` takes
  actor logic, not an existing ref.
- **Vue**: `@xstate/vue` — `useMachine`/`useSelector` composables.
- **Svelte**: `@xstate/svelte` — `useMachine` returning stores.
- **Solid**: `@xstate/solid` — `useMachine`/`fromActorRef`.
- **No framework / other**: `createActor(machine).start()` + `actor.subscribe(render)`; keep the
  subscription in one place and render from snapshots.

If docs are needed beyond this file (unusual APIs, framework-binding edge cases), fetch the current
docs at stately.ai/docs rather than guessing — APIs postdate training data.
