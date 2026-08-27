# Phases 4-5 -- Functional inference, theater detection, synthesis and seams

A prototype proves what the product *looks like* and mimes what it *does*. The job is to
state what it must actually do -- as requirements, with citations -- and to be honest
about which parts were never real.

## Method (per module, Phase 4)

1. Read the module top to bottom. It is hand-written and commented; the comments are
   evidence.
2. Read the store modules it reads from **first** -- mock data is the best schema
   evidence that exists.
3. Walk the view tree the way a user scans: header → toolbar → content → footer → modals.
4. State each behavior as a **requirement**, not a description. "Deleting a connection
   asks for confirmation and removes it from the list" -- not "there is a delete button".
5. Tag every inference `high` / `medium` / `low`. **A `low` confidence claim MUST also
   create an `ambiguities` entry** -- confidence is not a substitute for asking.
6. Never invent. A state the prototype does not draw is `present_in_design: false`.

## Affordance → behavior taxonomy

| Cue | Inference |
| --- | --- |
| Button with an action verb (Sync, Run, Publish, Retry) | An operation on the focused entity; needs a service call, a pending state and a failure state |
| Row-level icon buttons | Per-record CRUD; check whether any is destructive → confirmation + authorization |
| Table with sortable headers | Server-side or client-side ordering; a column set is a projection of the entity |
| Pagination / "load more" / infinite scroll | Query with limit+offset or cursor; total count is a separate read |
| Filter chips, search box, date range | Query parameters on the collection read; each filter names an indexable field |
| Tabs that swap content without a URL change | View state, not a route -- unless a deep-link cue exists |
| Form with required markers / disabled submit | Validation rules; they belong in the contract schema, not the view |
| Status badge with a fixed vocabulary | An enum on the entity; capture every literal value seen |
| Metric tile / sparkline / counter | A derived read; ask whether it is computed live or stored |
| "Last synced 2 min ago" | A timestamp field plus a refresh cadence -- a subscription, not a render detail |
| Live-looking counters or streaming logs | A polling subscription; declare the interval |
| Avatar, owner, "assigned to" | A relation to a user entity, and an auth surface |
| Anything gated by a role selector | A permission boundary; record which affordances disappear |

## Theater detection -- the prototype-only lane

Every faked interaction is a service that does not exist yet. Find them mechanically,
then judge:

| Signal | What it usually means |
| --- | --- |
| `setTimeout(() => setLoading(null), 720)` | **Fake latency** standing in for a real query or command. The single highest-value finding: it names an operation the backend must provide |
| `setTimeout(… , 1500)` flipping a status to `done` | A long-running job faked; implies a real async job + progress reporting |
| A handler that mutates local array state only | An optimistic UI with no persistence behind it |
| Hardcoded result strings, canned AI answers, fixed citations | An integration or model call that was never made |
| `onClick={() => {}}` or a control with no handler | Either unbuilt or deliberately out of scope -- always ask |
| Randomized values (`Math.random`) feeding a metric | A computed read whose real source is undefined |
| A copy button, a toast, a local `copied` flag | Genuinely real -- do NOT flag pure UI feedback as theater |

Record each as a theater finding: the citation, the affordance it backs, the operation it
implies, and `disposition: null` (Stage-2 Round B sets it). **Never upgrade a faked
interaction to a planned service on your own authority.**

## Entity extraction from mock data

Mock data is ground truth for *shape*, never for content.

- Type conservatively: `"2024-03-01"` → date, `"$4,200.00"` → formatted number (record the
  format separately), `"1.24M"` → a display projection of a count.
- A repeated string set across records is an enum -- capture the full observed set.
- Nested objects become relations; an `id`-like field pointing at another collection is a
  `ref:<Entity>`.
- PascalCase singular names (`Connection`, not `connections`) so Phase 5 merges cleanly.
- A field present on some records and absent on others is optional -- and worth an
  ambiguity if it changes behavior.
- Record which collection each screen reads: that is the ownership evidence for seams.

## States checklist (run per screen)

`loading` · `empty` · `error` · `success` · `disabled` · `readonly` · `unauthorized`.

Prototypes draw the happy path and little else. A state that is implied but not drawn is
`present_in_design: false` and an automatic gap-register candidate -- not a defect of the
prototype, but a real cost in the port, because the target's TEA model needs a decided
view for every Model state.

## Synthesis (Phase 5, main thread)

Merge the profiles into `<dossier>/synthesis.json`:

```json
{
  "generated": "<ISO-8601>", "source_profiles": ["..."],
  "entities": [{ "name": "Connection", "fields": [], "relations": [], "seen_on": [], "conflicts": [] }],
  "routes": [{ "path": "/connections", "screen_id": "", "params": [], "guard": null }],
  "features": [{ "id": "", "name": "", "domain": "", "description": "",
                 "screens": [], "affordances": [], "operations": [],
                 "priority": null, "cut": false }],
  "shared_services": [{ "name": "", "why": "", "screens": [] }],
  "theater": [{ "id": "", "citation": "", "affordance": "", "implies_operation": "",
                "disposition": null }],
  "ambiguities": [{ "id": "", "question": "", "readings": [], "blocking": false,
                    "screens": [], "status": "open", "resolution": null }]
}
```

Rules: merge same-named entities and union their fields (a genuine type conflict becomes
a `conflicts` entry AND an ambiguity, never a silent pick); a feature is 3-10 affordances
plus their operations, named verb-noun; aim for 4-8 domains taken from the chrome's own
sections; promote anything appearing on ≥2 screens to `shared_services` (auth, search,
notifications, realtime, export, audit -- the reliable underestimates); dedupe
ambiguities and order them blocking-first.

## Seams analysis (Phase 5) -- evidence for composition, not the composition

Cross the `window.*` read/write graph from Phase 2 with the feature domains. Write
`<dossier>/seams.md`:

| Candidate cut | Features inside | Evidence for | What crosses it | Would need brokering |
| --- | --- | --- | --- | --- |

Candidate cuts come from the same five categories a real app port uses, translated to a
prototype:

1. **Store ownership** -- a feature cluster reading exactly one store global that nothing
   else reads. The strongest signal a prototype offers.
2. **View islands** -- screens whose state never crosses into another screen's state.
3. **Chrome sections** -- top-level nav groups, which usually encode the product's own
   mental model.
4. **Distinct data cadences** -- a live-polling surface next to a static reference
   surface wants a different service shape.
5. **Distinct audiences** -- an operator console next to an end-user view.

For each crossing, state what it becomes in the target: an **attribute** (configuration),
an **event out** (a cross-dot signal, where *a poll is the floor* and brokering is the
optimization), an **owned RPC**, or an **explicit cut**. A crossing that resolves to none
of those means the seam is wrong -- say so rather than forcing it.

**Stop there.** How many MicroDots to build, what they are called and what the host
brokers is `microdots-port-app`'s composition proposal and its user gate. This file is
the evidence it consumes.
