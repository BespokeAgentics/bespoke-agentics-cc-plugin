# Fixture — ontology-vault

A two-client wiki with deliberately planted vocabulary drift, used by `skills/project-ontology/evals`.
Planted (do not "fix" — the evals assert on them):

| Page | Planted | Expected rule after init |
|---|---|---|
| `clients/northwind/gaps/credit-limit-enforcement.md` | `client: Northwind Traders` | value-noncanonical (spelling variant of `northwind`) |
| `clients/northwind/features/credit-limits.md` | `priority: P0` (templates allow P1–P3) | value-proposed — observed, never silently approved |
| `clients/northwind/gaps/approval-escalation.md` | `related-feature: "[[feature\|order-approvals]]"`, body `[[Order Approvals]]` | relation-noncanonical, link-noncanonical |
| `clients/northwind/gaps/bulk-import.md` | `related-feature: "[[approval-escalation]]"` (a gap, not a feature) | relation-range |
| `clients/northwind/decisions/credit-check-provider.md` | `[[missing-vendor-eval]]` | link-broken |
| `_schema/SCHEMA.md` vs `_schema/templates/gap.md` | gap status `open\|in-progress\|resolved` vs `open\|mitigated\|resolved` | init conflict |
