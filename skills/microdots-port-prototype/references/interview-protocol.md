# Phases 3 & 6 -- Interview protocol

## Global contract

- AskUserQuestion, **max 4 questions per call**, 2-4 options each, the recommended option
  first and labeled `(Recommended)`. `multiSelect` wherever the choices are not exclusive.
- Free-text "Other" is authoritative -- it overrides the inference it replaces.
- **Never re-ask what the conversation already established.** Confirm it in one line instead.
- **Every answer becomes written state** -- `context.md` in Stage-1, `synthesis.json` and
  the profiles in Stage-2. An answer that changes nothing on disk was not worth asking.
- Never more than two consecutive calls without visible work between them.

## Stage-1 -- Frame the analysis (Phase 3)

Six standard questions, plus two that only a prototype raises. Batch into two calls.

| # | Question | Options |
| --- | --- | --- |
| 1 | What is this product, in one sentence, and who pays for it? | Free-text-led; offer the artifact `<title>` + inferred domain as the first option to confirm |
| 2 | Which user roles does it serve? (multi) | Roles inferred from the chrome/nav profile, plus "single role for now" |
| 3 | Backend reality | Greenfield · Existing API to wrap · BaaS · Undecided |
| 4 | Auth model | None yet · Email+password · SSO/OIDC · Existing IdP |
| 5 | Explicit non-goals | The features the prototype shows that are NOT being built |
| 6 | Integration targets | The external systems the mock data implies (name them from the stores) |
| **7** | **Which screens are the product and which are demo filler?** (multi) | One option per `screen` module, labeled with its inventory label. **This question is the reason a prototype port is cheaper than an app port** -- filler is cut before any agent is spent on it |
| **8** | **How faithful must the visual design stay?** | Pixel-faithful (tokens are a contract) · Brand-faithful (tokens carried, layout free) · Functional only (rebuild in the target's idiom) |

Q7 prunes the Phase 4 fan-out. Q8 decides whether `_src/styles/` is a port input or
merely a reference -- and it is the difference between a cheap port and an expensive one,
so ask it before, not after.

Digest to `<dossier>/context.md`, under ~30 lines, headed: `Purpose / Users & roles /
Backend / Auth / Non-goals / Integrations / In-scope screens / Visual fidelity / Other
constraints`. Passed **verbatim** to every Phase 4 agent.

## Stage-2 -- Validate the synthesis (Phase 6)

Four rounds. Present inferences as claims to be corrected, never as findings.

### Round A -- Features, per domain

One `multiSelect` per feature domain: "which of these are real requirements?" Unselected
features get `cut: true` and the reason "Explicitly out of scope" -- they generate no
stories and no MicroDot surface. Split any domain carrying more than four features.

### Round B -- Theater disposition

**The round unique to prototypes, and the highest-value one.** For each theater finding,
one question with the evidence quoted (`setTimeout(… , 720)` at `_src/app/09:347`) and
three options:

| Answer | Effect on state |
| --- | --- |
| Must become real | `disposition: "implement"` -- generates an RPC operation on the owning entity and a P-priority in Round D |
| Stays mocked for now | `disposition: "mock"` -- becomes a seeded store row plus a ⚪ gap-register entry |
| Drop the interaction | `disposition: "drop"` -- the affordance is removed from its feature |

Batch related findings (all fake-latency loaders in one screen is one question). A
theater finding left undisposed is a blocking ambiguity, not a detail.

### Round C -- Ambiguities

Ordered `blocking: true` first, then by how many screens each touches. Use the profile's
`question` field verbatim and its `readings` as the options. Non-blocking rows always
carry "Defer -- decide later". **A blocking ambiguity cannot be deferred silently**: it
is resolved, or it is marked 🔴 with explicit permission and the section is labeled
"BLOCKED -- needs decision".

### Round D -- Priorities and phasing

P0 as a `multiSelect` over confirmed features; the remainder default P1 with an optional
demotion to P2. Ask for any hard phasing constraint (a demo date, a dependency on an
integration that is not ready). Priorities flow into the handoff so port-app's waves
inherit them rather than re-deriving them.
