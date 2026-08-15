# Phase 2 — Visual inventory

Code reading tells you what the feature *should* do; the walk tells you what it
actually does and what it feels like — the states that exist in practice, the
microcopy, the latency the user experiences, and the payloads really crossing
the wire. Both matter because the port re-expresses the UI from behavior: a
state nobody inventoried is a state the micro-app will silently lack.

Drive the browser from the **main session**, not a subagent. Two things force
this: the login gate (the user must type credentials into a tab you are
driving) and mid-walk questions ("is this the feature, or the older version of
it?") — neither works from a subagent.

## App discovery

In order: `--app <url>` → an already-listening dev server (probe the usual
suspects: 3000, 5173, 8080, 4321, 8000, and anything the source repo's scripts
imply) → offer to start the repo's own dev command, **asking first** (starting
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
`navigate` targets the *first* tab in the group, not yours; a tab ID from a
previous session is dead; a tab the user is working in is not yours to drive.

## The login gate

Before any capture:

- The user logs in, clears cookie banners, and dismisses consent dialogs
  **themselves**. You never type passwords, card numbers, or any credential —
  entering credentials is a prohibited action, full stop.
- For consent popups you do handle, pick the most privacy-preserving option.
- Never bypass CAPTCHAs or bot detection.
- Tell the user exactly what state to leave the tab in ("logged in, on the
  dashboard"), then wait for their go.

## The walk

Screenshot **states, not pages**. A page is one URL; a state is one distinct
configuration the user can experience — list-with-items, list-empty, loading,
error, editing, confirmation. One screenshot per state, named
`ui/state-NN-<label>.png` (two-digit sequence, short kebab label). A screenshot
of the default state proves little that a sentence would not; the empty and
error states are where ports usually go wrong, because the source app handled
them and nobody noticed.

Per state, record: the components on screen (cross-referenced to the trace's
surface lane), the data shown and its formatting, microcopy verbatim where it
matters, and the interactions available. Then exercise interactions to reach
further states, under the read-only discipline:

- Filling forms to surface validation is fine. **Submitting a mutation needs
  the user's OK in the moment** — mocked backends and production backends look
  identical from a button.
- Stop at the brink of anything irreversible (payments, emails, public posts,
  deletes): record the step as `not walked — irreversible` and ask before
  crossing, if at all.
- Retry a failed action at most 2–3 times with a fresh screenshot between
  attempts, then record what happened and move on — never loop.

**Sensitive data check.** The dossier lands in the micros workspace repo. If
the walk shows real personal or production data, say so and ask whether
screenshots or structure-only notes should be captured. Prefer test accounts
when the user has one.

## Network capture

After each meaningful interaction, `read_network_requests` filtered to the
feature's endpoints (the trace's API lane says which). Record per endpoint:
method, path, a representative request body and response body with secrets,
tokens, and PII redacted, and status codes observed — including the error
responses, which name the tagged errors the contract will need. Traffic that
matches no traced endpoint is a finding, not noise: either the trace missed a
call site or the app calls something at runtime the code obscured.

Observed shapes outrank declared types when they disagree — the wire is what
the feature actually depends on. Note disagreements explicitly; they are
contract-design input, not embarrassments to smooth over.

## Gotchas

- **A native `alert`/`confirm`/`prompt` freezes the extension** — it stops
  receiving commands entirely. Avoid clicking things likely to raise one; if
  one appears, ask the user to dismiss it in the browser, then re-run
  `tabs_context_mcp` and resume.
- An automation tab is usually **backgrounded**: scroll events, animation
  frames, and CSS transitions can silently no-op there. For an inventory this
  mostly means: screenshot right after acting (a screenshot briefly
  foregrounds the tab), and treat a "nothing happened" as suspect until
  reproduced.
- Size the window before capturing (desktop width ≥1280px) so states render as
  designed, not in a squeezed layout no user sees.

## `ui-inventory.md` format

```markdown
# UI inventory — <feature>
Date · app URL · logged-in role/account type · walk duration
Verification status: visually verified | partially (list) | not visually verified

## State catalog
| # | State | Screenshot | Components (trace refs) | Data shown | Interactions |

## Interaction log
Ordered: action → observed result → screenshot/state reached.

## Network shapes
| Endpoint | Method | Request shape | Response shape | Statuses seen | Trace ref |

## Not reached
| State | Why (login wall / irreversible / not found / time) |

## Divergences from code
Where the wire or the pixels disagreed with the trace — each one a note for
the contract draft or the TEA sketch.
```

## Degradation

| Missing | Behavior |
|---|---|
| Browser tools unavailable | Skip the walk. Derive the state catalog from the trace's surface + behavior lanes; set verification status to **not visually verified** and label every state row `derived from code`. |
| No reachable app | Same. The discovery ladder ends by asking, never by simulating. |
| Login wall uncleared | Walk what is public; everything behind the wall goes to Not reached with the reason. |
| Extension frozen by a dialog | User dismisses → `tabs_context_mcp` → resume; if it recurs, finish with what you have and say so. |

The one unforgivable failure of this phase is a fabricated visual claim — a
screenshot reference that does not exist, a state described as seen that was
derived. Labels never lie; a smaller honest inventory beats a complete
invented one.
