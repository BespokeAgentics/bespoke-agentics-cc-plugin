# Evaluation Playbook — Affordance → Behavior Inference

How to read a page and extract its implied functionality. This is the page-evaluator
agent's core reference. Output must conform to `assets/templates/page-profile.schema.json`.

## Method

1. **Read the page source top-to-bottom.** Note every primitive instantiation, its props,
   handlers, and the mock data feeding it.
2. **Read the mock data module(s)** the page imports. Field names and shapes are your best
   entity evidence.
3. **Walk the JSX tree as a user would scan the screen** — header → toolbar → content →
   footer. Record an affordance for every interactive or state-bearing element.
4. **For each affordance, state the behavior as a requirement** ("Generates a CSV of the
   current filtered set"), not a description ("there is an export button").
5. **Tag confidence honestly.** `high` = label + handler + data agree. `medium` = standard
   pattern, plausible inference. `low` = guess → MUST also create an `ambiguities` entry.
6. **Never invent.** If the design shows no error state, record `present_in_design: false`
   — don't imagine one into the profile.

## Inference taxonomy

### Buttons & action verbs

| Cue | Inference |
|-----|-----------|
| Verb label (`Save`, `Send`, `Approve`, `Archive`, `Export`) | Mutation or domain action → `operations[]` entry with `crud: action/create/update` |
| `+ New <Entity>` / `Add` | `create` operation + likely modal/drawer or navigation to a form page |
| `Delete` / `Remove` | `delete` operation; ALWAYS raise ambiguity: soft vs. hard delete, confirmation flow |
| Destructive styling (`variant="danger"`) | Confirmation dialog requirement even if none is shown |
| `Cancel` / `Discard` | Form state reset + dirty-state tracking requirement |
| Icon-only button | Infer from icon name (`trash`→delete, `pencil`→edit, `download`→export); confidence ≤ medium |
| Disabled button in mock state | A validity/permission rule exists — find what enables it; if unclear, ambiguity |

### Tables & lists

A data table implies, at minimum: `query` operation (list), pagination decision, and
loading/empty states. Look for:

| Cue | Inference |
|-----|-----------|
| Column headers with sort arrows / clickable headers | Sortable fields → query params |
| Filter chips / dropdowns above table | Filterable fields + filter persistence question |
| Search input | Text query endpoint; ambiguity: client-side vs. server-side search |
| Pagination controls / "1–10 of 240" | Server-side pagination (the count proves a total exists) |
| Row checkboxes + bulk bar | Bulk operations — enumerate each bulk action |
| Row click / chevron / kebab menu | Drill-down navigation (`navigation[]`) and/or per-row actions |
| Status badges in a column | Status enum on the entity — record the exact values seen as `enum_values` |
| Avatars/names in cells | `ref:User` relation on the entity |

### Forms

| Cue | Inference |
|-----|-----------|
| Input with label + placeholder | Entity field; placeholder often reveals format ("you@company.com" → email validation) |
| Required asterisk / `required` prop | Validation rule |
| Select/radio options | Enum field — record all option values |
| Date/time pickers | Date field + range rules if paired (start/end) |
| Multi-step / wizard layout | Draft persistence question (ambiguity: can users resume?) |
| Submit button label | `create` vs `update` (e.g. "Save changes" → update; "Create project" → create) |
| Inline error styles in tokens (`--error-*`) | Field-level validation display requirement |

### Status, badges & metrics

| Cue | Inference |
|-----|-----------|
| Status badge variants | Entity state machine — enumerate states; ambiguity: what transitions are legal and who triggers them? |
| Metric cards (KPI tiles) | Aggregate query operations (count/sum/avg) — each tile is one `operations[]` entry |
| Trend arrows / sparklines / "+12% vs last month" | Time-series data requirement + period comparison logic |
| Progress bars | Computed ratio — identify numerator/denominator entities |
| Notification dot / unread count | Realtime or polling requirement → `realtime: true` |

### Navigation & layout composites

| Cue | Inference |
|-----|-----------|
| Sidebar items | Route map — each item is a page/route; mark items with no corresponding page export as gaps |
| Breadcrumbs | Route hierarchy + parent list pages |
| Tabs within a page | View states (same route) vs. sub-routes — pick one, note the choice |
| User avatar menu in TopBar | Auth session, profile page, sign-out operation |
| Org/workspace switcher | Multi-tenancy requirement — this is architectural, flag prominently |
| Settings gear | Settings surface exists even if no settings page was exported (gap if missing) |

### Search, filters & realtime

| Cue | Inference |
|-----|-----------|
| Global search in TopBar | Cross-entity search service (vs. per-page search — ambiguity if both exist) |
| "Last updated 2m ago" / relative timestamps | Refresh strategy question: polling, websocket, or manual |
| Toast/snackbar components in the library | Async operation feedback pattern — operations need success/failure surfacing |
| Skeleton components in the library | Loading states were designed — wire them per page |

### Roles & permissions

| Cue | Inference |
|-----|-----------|
| Mock data with `role`/`permission` fields | RBAC model — record roles seen |
| Admin-prefixed pages or sections | Privileged area; auth boundary in plan |
| "Assigned to me" / "My items" filters | Per-user ownership + session identity requirement |
| Locked/readonly visual states | Permission-gated editing |

## Entity extraction rules

- **Mock data is the ground truth** for field names and types. A `mockInvoices` array with
  `{ id, customer, amount, status, dueDate }` defines the `Invoice` entity better than any
  visual inspection.
- Infer types conservatively: `"2024-03-01"` → `date`, `"$4,200.00"` → formatted `number`
  (note the formatting as a frontend concern), repeated string set → `enum`.
- Objects nested in mock data → relations (`customer: { name, avatar }` → `ref:Customer`).
- The same entity seen on multiple pages gets merged in Phase 4 — name entities
  consistently (PascalCase, singular) so the merge keys cleanly.

## States checklist (run per page)

For each of `loading / empty / error / success / disabled / readonly / unauthorized`,
ask: does the functionality imply this state can occur, and did the design show it?
`implied but not designed` entries are automatic gap-register candidates (🟡 or ⚪).

## Visual verification deltas (Phase 3 only)

When walking the rendered story, look specifically for what code reading misses:
hover/focus-revealed actions, truncation/overflow behavior, scroll-position cues
(sticky headers, infinite scroll), z-order implying modality, visual grouping implying
batch semantics, and disabled styling not obvious from props. Append findings as
affordances with `source: "visual"`, or upgrade existing ones to `source: "both"`.

## Anti-patterns

- **Don't pad.** An affordance with no implied behavior (decorative divider) is not an
  affordance.
- **Don't resolve ambiguities yourself.** Two readings → `ambiguities[]` entry. The
  Stage-2 interview exists for this.
- **Don't design the backend.** `endpoint_sketch` is a sketch — synthesis and the user
  decide the real API shape.
- **Don't skip composites.** Shell/Sidebar/TopBar carry the route map, auth surface, and
  tenancy cues — evaluate them first; pages inherit their context.
