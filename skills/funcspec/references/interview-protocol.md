# Interview Protocol — Stage-1 (Frame) and Stage-2 (Validate)

Both interviews use **AskUserQuestion**: max 4 questions per call, 2–4 options each,
recommended option first with "(Recommended)", multiSelect where choices aren't
exclusive. Users can always answer "Other" — treat free-text answers as authoritative.

Rules that apply to both stages:

- **Don't re-ask what the conversation already established.** Confirm instead
  ("You said X — still true?") or skip entirely.
- **Every answer becomes written state** (`context.md` or resolutions in profiles /
  `synthesis.json`) — interviews that only live in chat history are lost to later phases.
- **Batch related questions**; never exceed 2 consecutive calls without doing visible
  work in between.

## Stage-1 — Frame the analysis (Phase 1)

Goal: enough context that evaluators infer correctly and don't chase non-goals.
Typically one call of 4 questions, a second only if answers open new ground.

Question bank (pick the 4 most load-bearing for this workspace; phrase options from
what the inventory shows):

1. **Purpose** — "What is this application for?" Options derived from the page list
   (e.g. inventory shows Dashboard/Invoices/Customers → "internal billing ops tool",
   "customer-facing portal", "admin console for an existing product").
2. **Users & roles** — "Who uses it?" (multiSelect) — single internal team / multiple
   roles with different permissions / external customers / mixed.
3. **Backend reality** — greenfield (API designed from this plan) / existing API to
   integrate (plan maps to it) / BaaS (Supabase/Firebase) / undecided (plan stays
   backend-agnostic at the contract level).
4. **Auth model** — none (internal/prototype) / simple email+password / SSO-OIDC /
   existing identity provider.
5. **Non-goals** — "Anything visible in the pages that is explicitly out of scope?"
   (free-text leaning; offer likely candidates from the inventory).
6. **Integration targets** — where should work items land (Jira/Linear/files-only),
   any systems the app must talk to.

Digest the answers into `<out>/context.md` — under ~30 lines, structured:
`Purpose / Users & roles / Backend / Auth / Non-goals / Integrations / Other constraints`.
This digest is passed verbatim to every evaluator.

## Stage-2 — Validate the synthesis (Phase 5)

Goal: every feature confirmed or cut, every blocking ambiguity resolved, every feature
prioritized. Work domain-by-domain so questions stay concrete.

### Round A — Feature confirmation (per domain)

For each functional domain in the feature inventory, one multiSelect question:
"Which of these inferred features are real requirements for <domain>?" — options are
the features with one-line descriptions; include the evidence page in the description.
Features left unselected are **cut**: mark `cut: true` in synthesis, exclude from the
plan, list under "Explicitly out of scope" in the functional spec. If a domain has >4
features, split into two questions or group minor features into one option.

### Round B — Ambiguity resolution

Order: `blocking: true` first, then by page-count touched. Each ambiguity is one
question — the profile's `question` field verbatim, its `readings` as options
(evaluator's best guess first, as "(Recommended)" only when confidence justifies it).
Always include a "Defer — decide later" option for non-blocking items; deferred items
keep status ⚪ and go to the gap register. Write `resolution` and `status: resolved |
deferred` back into the owning profile AND the consolidated register.

**Blocking ambiguities cannot be deferred silently.** If the user defers one anyway,
record it 🔴 in the gap register and label the affected plan section "BLOCKED — needs
decision".

### Round C — Priorities & phasing

1. "Which features are P0 (must ship first)?" — multiSelect over confirmed features.
2. Remaining features default P1; one question offering to demote any to P2.
3. Phasing constraints — "Anything that must come before/after something else?"
   (free-text leaning).

### Conversions (answer → state)

| Answer | Effect |
|--------|--------|
| Feature confirmed | Stays in inventory → becomes epic/stories in `backlog.md` |
| Feature cut | `cut: true`; "out of scope" section; no stories |
| Feature corrected ("Other" text) | Update feature description + affected operations; re-check entity model for ripple |
| Ambiguity resolved | `resolution` written; affected operations/entities updated; gap register entry colored (🟢🔵🟡🟣 per the resolution's nature) |
| Ambiguity deferred | ⚪ in gap register; plan notes the assumption taken |
| Priority set | `priority: P0|P1|P2` on feature; drives plan phasing + backlog order |
