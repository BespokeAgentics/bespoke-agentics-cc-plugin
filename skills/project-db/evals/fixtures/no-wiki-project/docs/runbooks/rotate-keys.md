# Runbook: rotate Stripe API keys

1. Create the new restricted key in the Stripe dashboard.
2. Update the `STRIPE_KEY` secret.
3. Deploy; watch the reconcile job (ADR 0004) for 15 minutes.
4. Revoke the old key.
