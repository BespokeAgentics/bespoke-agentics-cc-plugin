---
type: adr
status: superseded
superseded-by: 0004-stripe-sync-job
date: 2025-11-20
deciders: [payments-team]
tags: [payments, stripe]
---

# ADR 0003: Process Stripe webhooks synchronously

## Decision
Handle each webhook inline. Superseded because retries caused double charges; see the
[[rotate-keys]] runbook for the incident follow-up.
