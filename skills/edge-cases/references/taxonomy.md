# Edge-case lenses

Each lens is one way a feature meets the world off its happy path. The checklists are **prompts for
looking**, not a list to transcribe. A checklist item becomes a case only when the surface map shows
the target can actually reach it, and the case names the concrete trigger. "Unicode input" is a
prompt. "A display name of `زينب` renders right-to-left and pushes the edit button off the card" is a
case.

Lens ids are fixed. `scripts/check_cases.py` rejects any other id.

| id | Lens | Applies when the surface has… |
| --- | --- | --- |
| `input` | Input and data boundaries | any input: form field, API parameter, file, CLI argument, message payload, env value |
| `state` | State, lifecycle and data integrity | persisted data, multi-step flows, status fields, caches, sessions |
| `timing` | Concurrency and timing | async work, more than one user or tab, background jobs, retries, clocks, schedules |
| `failure` | Dependencies and failure modes | I/O: network, database, filesystem, third-party API, queue, storage, email |
| `actors` | Actors and permissions | more than one kind of user, authentication, roles, tenants, ownership |
| `security` | Security and abuse | a trust boundary: untrusted input reaching a server, query, shell, HTML, file path, or another user |
| `scale` | Volume and scale | collections, lists, files, history, fan-out, anything that grows |
| `environment` | Environment, platform and configuration | a client on many devices or browsers, config, feature flags, locales, deploy-time differences |
| `ux` | Interaction and UX | a UI: forms, navigation, loading, feedback |
| `domain` | Business rules and domain | rules, thresholds, money, units, dates with meaning, policy, regulated behavior |
| `change` | Change impact and compatibility | a **changes** target, or a plan that modifies existing behavior |
| `interaction` | Combined conditions | never a first-pass lens: produced only by the `deep` interaction analyst |

Record every lens you skip, with the reason ("`ux` — no UI: the target is a CLI importer"). The
report's Coverage section lists them.

---

## `input` — Input and data boundaries

- **Absence:** missing field, `null` vs `undefined` vs empty string vs whitespace-only, empty array or
  object, a field present but empty.
- **Numeric edges:** 0, negative, −0, 1, the exact minimum and maximum, one past each (off-by-one),
  very large, `NaN`/`Infinity`, integer overflow, float precision (`0.1 + 0.2`), rounding direction,
  currency minor units.
- **Text:** maximum length and one past it, very long single words, leading or trailing whitespace
  (pasted values), case differences, Unicode normalization (é as one code point vs two), emoji and
  surrogate pairs, RTL text, zero-width characters, newlines in single-line fields, quotes and
  backslashes.
- **Format:** malformed (bad email, bad JSON, truncated file), valid-but-unusual (IPv6, `+` in email,
  apostrophe in surnames, a name with no surname), the wrong type (string `"10"` vs number `10`),
  locale-formatted input (`1.000,50`).
- **Dates and times:** time zones, DST transitions (the missing and the repeated hour), midnight
  boundaries, leap day, end of month, a date-only string parsed as UTC midnight, epoch 0, the far
  future, client clock vs server clock.
- **Collections:** duplicates, ordering assumptions, one element, mixed valid and invalid elements.
- **Files:** zero bytes, huge, wrong extension vs real type, unusual names (spaces, Unicode, `..`),
  encodings (UTF-8 BOM, UTF-16, Latin-1), CSV with embedded commas, quotes or newlines.

## `state` — State, lifecycle and data integrity

- **First and last:** first use (empty state, no history, no defaults yet), the last item deleted, an
  account with no data.
- **Mid-flow interruption:** refresh, back button, closed tab, lost connection, app backgrounded, then
  resume. Is the partial state saved, lost, or duplicated?
- **Stale state:** acting on data another actor changed or deleted; a cached value outliving its
  source; an optimistic update that the server rejects.
- **Lifecycle transitions:** an action on an archived, deleted, suspended, expired, or draft entity; an
  illegal transition (paid → pending); re-running a completed step.
- **Idempotency:** the same request twice (double submit, retry after timeout). Does it charge, send,
  or create twice?
- **Persisted shape:** records written by older code (missing new fields, old enum values), `null`s
  the new code does not expect, data that violates a newly added constraint.
- **Integrity:** partial writes when step 2 of 3 fails, orphaned children, cascading deletes, two
  sources of truth disagreeing.
- **Sessions:** expiry mid-action, login as a different user in another tab, logout in another tab.

## `timing` — Concurrency and timing

- **Races:** two users editing one record; check-then-act (`if count < max` then increment) across an
  `await`; two tabs of one user; double-click before the button disables.
- **Ordering:** responses arriving out of order (a search for "ab" resolves after "abc"); events
  delivered twice or late; a webhook before the record it refers to exists.
- **Slowness and timeouts:** a slow dependency (does the UI show progress, can the user leave?);
  timeout followed by a late success; retry storms.
- **Cancellation:** user cancels mid-operation; navigation away while a request is in flight; an unmount
  that still runs a `setState`.
- **Time-based behavior:** a scheduled job overlapping its previous run, a job running during a deploy,
  a token expiring between check and use, a TTL boundary, clock skew between services.

## `failure` — Dependencies and failure modes

- **Down or erroring:** the dependency is unreachable, returns 5xx, returns 4xx the code did not expect,
  returns 200 with an error body.
- **Partial failure:** a batch where some items succeed; a multi-step write where step 2 fails after
  step 1 committed; a fan-out where one branch fails.
- **Contract drift:** a field missing or renamed, a new enum value, pagination changed, an unexpected
  `null`.
- **Limits:** rate limiting (429), quota exhausted, payload too large, disk full, connection pool
  exhausted.
- **Degraded mode:** offline, read-only database, cache miss storm, a feature flag service unavailable
  (what is the default?).
- **Error surfacing:** is the failure shown, logged, retried, or swallowed? Does a swallowed error leave
  the user believing something succeeded?

## `actors` — Actors and permissions

- **Who:** anonymous, signed-in but unverified, a new user, a power user, an admin acting on someone
  else's data, a service account, a deactivated user with a live session.
- **Changes mid-session:** role downgraded, permission revoked, membership removed, plan downgraded,
  while the user is on the page.
- **Boundaries:** tenant A reaching tenant B's object by id; a shared resource where owner and viewer
  see different actions; a delegated or impersonated session.
- **Assistive and alternative use:** keyboard-only, screen reader, zoomed to 200%, reduced motion,
  a user in another locale or language.

## `security` — Security and abuse

- **Authorization:** object ids in URLs or bodies that the user does not own (IDOR); a hidden UI action
  still reachable via the API; mass assignment of fields like `role` or `price`.
- **Injection:** SQL or NoSQL, shell, path traversal (`../`), HTML or script injection (stored and
  reflected), header injection, template injection, CSV formula injection (`=HYPERLINK(...)`).
- **Abuse:** enumeration (does "user not found" differ from "wrong password"?), brute force, replay of a
  one-time token, coupon or referral farming, unbounded resource requests.
- **Leakage:** secrets or PII in logs, error messages, URLs, analytics, or client bundles; another
  user's data cached and shown.
- **Files:** uploads with executable content, oversized or decompression-bomb archives, SVG with script.

Security cases against an exposed surface are at least `possible` in likelihood: someone looks for them.

## `scale` — Volume and scale

- **Counts:** 0, 1, 2 (the first plural), the page size, page size + 1, 10× and 1000× the typical
  volume.
- **Size:** very large records, deeply nested data, a huge file, a long-lived account with years of
  history.
- **Cost cliffs:** N+1 queries, an unindexed filter, loading everything to count it, a sort in memory,
  a request that times out only at production volume.
- **Display:** very long lists without virtualization, a chart with one point or 100,000, a table where
  one cell holds 5,000 characters.

## `environment` — Environment, platform and configuration

- **Clients:** the browsers and devices the product supports, small and very large viewports, touch vs
  mouse, an old app version calling a new API, browser autofill and extensions.
- **Configuration:** a missing env var, a feature flag in each state (and flipping mid-session),
  per-environment differences (staging vs production), a default that is only safe in development.
- **Locale:** the language, number, date and currency formats the product supports, text expansion
  (German is about 30% longer), RTL layouts, time zone of the user vs the server.
- **Deploys:** a request that spans a deploy, a migration running while old code serves traffic,
  rollback after new data has been written.

## `ux` — Interaction and UX

- **Feedback:** what shows while loading, after success, after failure, and when the result is empty?
- **Leaving:** navigating away with unsaved changes, browser back after submit, refreshing a
  confirmation page (resubmission).
- **Input mechanics:** paste, autofill, IME composition (Japanese, Chinese), Enter key submits early,
  disabled-state that does not actually block a keyboard submit.
- **Recovery:** undo, editing a submitted item, recovering a form after an error without retyping it.
- **Focus and order:** focus after a modal closes, after an inline error, after a list item is deleted.
- **Multiplicity:** the same flow open in two tabs; notifications about an item the user already acted on.

## `domain` — Business rules and domain

- **Thresholds:** exactly at the boundary. Is "orders of $50 or more" implemented with `>=` or `>`?
  "Within 30 days" counted from purchase date, delivery date, or the next day?
- **Combination of rules:** two discounts, a rule exception that meets another rule, priority between
  conflicting policies.
- **Money and units:** rounding per line vs per total, currency conversion and its timing, tax-inclusive
  vs exclusive, unit conversion, negative totals, refunds larger than the remaining balance.
- **Reversals:** cancel, refund, chargeback, partial return, an undo after downstream effects (an email
  sent, a shipment created).
- **Rule changes:** a price, policy, or plan that changes while an order, trial, or subscription is in
  flight. Which version applies?
- **Regulation:** consent, retention, deletion requests, age, region-specific rules — only when the
  domain actually carries them.

## `change` — Change impact and compatibility

For **changes** targets, and for plans that modify existing behavior. Read every changed hunk and ask
what it broke for something that is not in the diff.

- **Callers:** every caller of a changed function, type, endpoint, or event. Does each still hold the
  assumption the change removed (a return type, a thrown error, a default, a side effect, an ordering)?
- **Changed defaults:** a default value or fallback changed; code that relied on the old default
  silently changes behavior.
- **Removed or narrowed branches:** a case the old code handled that the new code does not (a deleted
  `else`, an early return that moved, a narrower type check).
- **Persisted data:** records written before the change; old enum values; caches and queues holding the
  old shape; a migration that must run before the code does.
- **Clients:** older clients, other services, webhooks, and public API consumers still sending or
  expecting the old contract.
- **Flags:** behavior with the new flag on, off, and flipped mid-flow; the cleanup path when the flag is
  removed.
- **Tests that still pass for the wrong reason:** a test updated to match new behavior that no longer
  asserts what it used to.

## `interaction` — Combined conditions (deep and prove only)

Produced by the interaction analyst (`references/verification.md` § Interactions), never by a
first-pass analyst. An interaction case pairs two conditions from existing cases and is kept only when
the pair produces an outcome that **neither condition produces alone**. Examples: an expired coupon on a
cart priced in a converted currency; offline + double-submit queues two orders that both sync later; a
role downgrade during a multi-step wizard whose last step needs the old role.
