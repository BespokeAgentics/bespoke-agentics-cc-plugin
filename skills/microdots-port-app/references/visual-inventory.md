# Phase 2 — Visual inventory

Code reading tells you what the app _should_ do; the walk tells you what it
actually does — the states that exist in practice, the microcopy, the latency,
and the payloads really crossing the wire. Both matter because the port
re-expresses the UI from behavior: a state nobody inventoried is a state the
MicroDots will silently lack. For a whole-app port the walk has a second job:
it is composition evidence — which screens the user experiences as independent
is exactly what the proposal must not contradict.

Drive the browser from the **main session**, not a subagent. Two things force
this: the login gate (the user must type credentials into a tab you are
driving) and mid-walk questions — neither works from a subagent.

## App discovery

In order: `--app <url>` → an already-listening dev server (probe the usual
suspects: 3000, 5173, 8080, 4321, 8000, and anything the source repo's scripts
imply) → offer to start the app's own dev command, **asking first** (starting
servers changes machine state) → nothing runnable → degrade to a code-derived
inventory. Never simulate a walk from source and present it as observed.

## Tool loading and tab discipline

Load everything in **one** ToolSearch call:

```
select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__read_network_requests,mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__tabs_close_mcp
```

Then, always in this order: `tabs_context_mcp` (`createIfEmpty: true`) —
required before any other browser tool — then `tabs_create_mcp` for a **fresh
tab**, and pass that explicit `tabId` to every subsequent call. A bare
`navigate` targets the _first_ tab in the group, not yours; a tab ID from a
previous session is dead; a tab the user is working in is not yours to drive.

## The login gate

Before any capture:

- The user logs in, clears cookie banners, and dismisses consent dialogs
  **themselves**. You never type passwords, card numbers, or any credential —
  entering credentials is a prohibited action, full stop.
- For consent popups you do handle, pick the most privacy-preserving option.
- Never bypass CAPTCHAs or bot detection.
- Tell the user exactly what state to leave the tab in, then wait for their go.

## The walk

Cover **every route the surface lane found**, and screenshot **states, not
pages**. A page is one URL; a state is one distinct configuration the user can
experience — list-with-items, list-empty, loading, error, editing,
confirmation, streaming-in-progress. One screenshot per state, named
`ui/state-NN-<label>.png` (two-digit sequence, short kebab label). The empty
and error states are where ports usually go wrong, because the source app
handled them and nobody noticed.

Per state, record: the components on screen (cross-referenced to the trace's
surface lane), the data shown and its formatting, microcopy verbatim where it
matters, and the interactions available. Note per screen which _other_ screens
react when something happens here — live composition evidence for the seams.
Then exercise interactions under the read-only discipline:

- Filling forms to surface validation is fine. **Submitting a mutation needs
  the user's OK in the moment** — mocked backends and production backends look
  identical from a button.
- Stop at the brink of anything irreversible (payments, emails, public posts,
  deletes): record the step as `not walked — irreversible` and ask before
  crossing, if at all.
- Retry a failed action at most 2–3 times with a fresh screenshot between
  attempts, then record what happened and move on — never loop.

**Sensitive data check.** The dossier lands in the target repo. If the walk
shows real personal or production data, say so and ask whether screenshots or
structure-only notes should be captured. Prefer test accounts when the user
has one.

## Network capture

After each meaningful interaction, `read_network_requests` filtered to the
app's endpoints (the trace's API lane says which). Record per endpoint:
method, path, a representative request and response body with secrets, tokens,
and PII redacted, and status codes observed — including error responses, which
name the tagged errors the contracts will need. Long-lived responses (SSE,
streaming chat) are findings that feed D-deploy. Traffic matching no traced
endpoint is a finding, not noise.

Observed shapes outrank declared types when they disagree — the wire is what
the app actually depends on. Note disagreements explicitly; they are
contract-design input.

## Gotchas

- **A native `alert`/`confirm`/`prompt` freezes the extension** — it stops
  receiving commands entirely. Avoid clicking things likely to raise one; if
  one appears, ask the user to dismiss it in the browser, then re-run
  `tabs_context_mcp` and resume.
- An automation tab is usually **backgrounded**: scroll events, animation
  frames, and CSS transitions can silently no-op there. Screenshot right after
  acting, and treat a "nothing happened" as suspect until reproduced.
- Size the window before capturing (desktop width ≥1280px) so states render as
  designed.

## `ui-inventory.md` format

```markdown
# UI inventory — <app>

Date · app URL · logged-in role/account type · walk duration
Verification status: visually verified | partially (list) | not visually verified

## State catalog

| # | Route | State | Screenshot | Components (trace refs) | Data shown | Interactions |

## Interaction log

Ordered: action → observed result → screenshot/state reached → other screens that reacted.

## Network shapes

| Endpoint | Method | Request shape | Response shape | Statuses seen | Trace ref |

## Not reached

| State | Why (login wall / irreversible / not found / time) |

## Divergences from code

Where the wire or the pixels disagreed with the trace — each a note for a
contract draft or a TEA sketch.
```

## Degradation

| Missing                      | Behavior                                                                                                                                                                               |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Browser tools unavailable    | Skip the walk. Derive the state catalog from the trace's surface + behavior lanes; set verification status to **not visually verified** and label every state row `derived from code`. |
| No reachable app             | Same. The discovery ladder ends by asking, never by simulating.                                                                                                                        |
| Login wall uncleared         | Walk what is public; everything behind the wall goes to Not reached with the reason.                                                                                                   |
| Extension frozen by a dialog | User dismisses → `tabs_context_mcp` → resume; if it recurs, finish with what you have and say so.                                                                                      |

The one unforgivable failure of this phase is a fabricated visual claim.
Labels never lie; a smaller honest inventory beats a complete invented one.
