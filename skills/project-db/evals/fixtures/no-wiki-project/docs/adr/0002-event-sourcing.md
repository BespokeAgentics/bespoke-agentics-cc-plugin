---
type: adr
status: proposed
date: 2026-03-11
deciders: [platform-team, finance]
tags: [architecture, ledger]
---

# ADR 0002: Event-source the ledger

## Context
Finance needs to reconstruct any invoice as of any date.

## Decision (proposed)
Store ledger events; derive balances. Depends on [[0001-use-postgres]].

## Open questions
- Snapshot cadence.
- Interaction with [[0003-stripe-webhooks]] retries.
