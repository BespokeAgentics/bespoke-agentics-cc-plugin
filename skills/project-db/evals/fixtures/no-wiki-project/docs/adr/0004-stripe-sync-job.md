---
type: adr
status: accepted
date: 2026-01-08
deciders: [payments-team]
tags: [payments, stripe, reliability]
---

# ADR 0004: Reconcile Stripe with a periodic sync job

## Decision
Poll Stripe every 5 minutes and reconcile; webhooks only enqueue. Replaces [[0003-stripe-webhooks]].
