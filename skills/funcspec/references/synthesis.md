# Synthesis — Merging Page Profiles into One Model

Phase 4 runs in the main thread (judgment, not mechanics). Input: schema-valid profiles
in `<out>/profiles/`. Output: `<out>/synthesis.json` + headline report.

## synthesis.json shape

```json
{
  "generated": "ISO-8601",
  "source_profiles": ["dashboard.json", "..."],
  "entities": [ { "name", "fields", "relations", "seen_on": ["page-ids"], "conflicts": [] } ],
  "routes": [ { "path", "page_id", "params", "guard" } ],
  "features": [ {
    "id", "name", "domain", "description",
    "pages": ["page-ids"], "affordances": ["page-id/aff-id"], "operations": ["page-id/op-id"],
    "priority": null, "cut": false
  } ],
  "shared_services": [ { "name", "why", "pages": [] } ],
  "ambiguities": [ { "id", "question", "readings", "blocking", "pages": [], "status", "resolution" } ]
}
```

## Entity merge

1. Group entities by name (PascalCase singular — normalize obvious variants:
   `Invoices`→`Invoice`, `InvoiceItem`/`LineItem` stay distinct unless field-identical).
2. Union fields. Same field, same type → merged, `seen_on` accumulates.
3. Same field, **conflicting type** (`status: enum[3]` on one page, `enum[5]` on
   another) → take the superset for enums; for genuine conflicts (string vs number)
   record in `conflicts` and raise a synthesis-level ambiguity.
4. Relations: union; a relation implied on any page holds for the model.
5. Entities seen on one page only are still real — but check they're not a display
   shape of another entity (e.g. `RecentActivity` is usually a projection, not a table;
   note as `projection_of` when evident).

## Route map

Start from the composite (Shell/Sidebar) profile's navigation — that's the canonical
top-level map. Add page-level navigation entries (drill-downs add parameterized child
routes; modals/drawers do NOT create routes unless deep-linking cues exist — if unclear
it's an ambiguity). Sidebar items with no matching page in the inventory → 🔴 gap
("designed nav target, no page exported").

## Feature clustering

A **feature** is a user-meaningful capability, typically 3–10 affordances + their
operations. Cluster by: same entity + same intent (e.g. all invoice-list filtering →
"Invoice search & filtering"); a page's primary workflow (e.g. "Create invoice" wizard);
cross-page services ("Global search", "Notifications") → cluster once, list all pages.

Naming: verb-noun or noun-capability ("Invoice export", "Team member management").
Domain grouping: use sidebar sections when present (they're the designer's own domain
model); else group by primary entity. Aim for 4–8 domains; merge singletons.

Every affordance with an `operation_ref` must land in exactly one feature. Decorative
affordances (confidence high, no operation) may be left unclustered — they're frontend
wiring detail, not features.

## Shared services

Promote to shared service when ≥2 pages independently imply the same capability:
auth/session, global search, notifications/toasts, realtime updates, file upload/export,
audit trail ("last edited by"), multi-tenancy. Shared services become their own plan
section and usually their own epic — they're the highest-risk underestimates.

## Ambiguity consolidation

Dedupe near-identical questions across pages (same entity + same question → one entry,
`pages` accumulates). Order: `blocking` desc, then page-count desc. This ordered list IS
the Stage-2 Round-B agenda.

## Traceability discipline

Every feature keeps `pages`/`affordances`/`operations` id arrays — `traceability.md` and
backlog story references are generated from these, so never cluster an affordance
without recording its id. The verification pass (Phase 7) walks these arrays backwards:
story → feature → affordance → page. A break anywhere fails verification.
