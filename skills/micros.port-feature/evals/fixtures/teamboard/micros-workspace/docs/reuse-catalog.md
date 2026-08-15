# Reuse catalog

Patterns this workspace has already solved. Before building a feature, match
the request against the Trigger index; port per the entry.

**Status** — `shared`: lives in `@kit/effect`; import it, never copy.
`copy-adapt`: port the listed files and adapt names. `mixed`: the core is
shared, the wiring around it is copy-adapt.

## Trigger index

| When the request says… | Pattern |
|---|---|
| "PIN", "password", "admin-only", "gate" | P1 |
| "needs a database", "persist", "store submissions" | P2 |
| "poll", "live value", "refresh every N seconds" | P3 |

## P1 — Secret gate (PIN auth)

- **Status:** mixed
- **Files:** `packages/kit-effect/src/secret.ts` (shared);
  `micros/pulse/service/handlers.ts` shows per-call verification wiring
- **Key symbols:** `SecretGate`, `makeSecretGateLive`, `Unauthorized`
- **Adaptation notes:** the gate is fail-closed; every RPC that mutates or
  reads gated data takes `pin` in its payload and verifies before acting.
  No sessions, no cookies.

## P2 — Store seam (D1 + bun:sqlite dual adapter)

- **Status:** copy-adapt
- **Files:** `micros/pulse/service/store.ts` (interface + shared SQL);
  adapters live beside it as `storeD1.ts` / `storeSqlite.ts` in stateful
  micros
- **Key symbols:** `PulseStore`, `makeStoreSqlite`, `changesOf`
- **Adaptation notes:** one interface, two adapters running the same SQL;
  `handlers.ts` takes the layer as an argument. Migrations are numbered SQL in
  `micros/<name>/migrations/`. The D1 binding name must be `DB`.

## P3 — Polling ticker

- **Status:** copy-adapt
- **Files:** `micros/pulse/src/app.ts` (subscriptions + AsyncData model)
- **Key symbols:** `Subscription.every`, `AsyncData`, `Refreshing`
- **Adaptation notes:** poll in `subscriptions`, never `setInterval` in view
  code; model the refresh so a failed poll keeps the last good value (stale
  beats blank).

## Maintenance

Verify before trusting: `ls` every listed path; on a miss, grep the Key
symbols — patterns move more often than they die. Fix the entry in the same
run. Add an entry (template below) when you ship something reusable.
