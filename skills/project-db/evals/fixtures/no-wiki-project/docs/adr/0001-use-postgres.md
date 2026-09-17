---
type: adr
status: accepted
date: 2026-02-03
deciders: [platform-team]
tags: [database, infra]
---

# ADR 0001: Use Postgres as the system of record

## Context
We need durable, transactional storage for invoices and ledger entries.

## Decision
Use Postgres 16 on Neon. Ledger tables are append-only.

## Consequences
Event replay is possible; see [[0002-event-sourcing]].
