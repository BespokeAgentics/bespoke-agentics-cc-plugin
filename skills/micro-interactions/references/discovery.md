# Discovery: read the app before proposing anything

A micro-interaction proposal is only as good as its grounding. Ideas that cite a real
function, a real label and a real token can be built; ideas that cite "the dashboard"
cannot. Discovery produces one file, `discovery.md` in the output folder, built from
the five investigations below. Every claim in it carries a source (`path:line`, a URL + what was seen, or
"user said").

## 1. Design authority

Find the documents that already rule on motion and visuals, in this order:

| Look for | What to take from it |
|---|---|
| `DESIGN.md`, `docs/design*`, a design-system package, Storybook | Named motion rules, easing, durations, reduced-motion policy, "never" lists |
| `PRODUCT.md`, `README`, brand docs | Voice, who the users are, what "success" means on each surface |
| The app's CSS: `@keyframes`, `transition`, `view-transition`, `prefers-reduced-motion` | Motion that **already ships**. These become `status: "ships"` motions |
| A test that asserts on animation (e.g. "zero running animations") | A hard constraint. Quote it in the guardrails |
| `ADR`s / decision logs touching UI | Choices you must not undo |

If two sources disagree (a doc says bottom sheet, the running app shows a drawer),
**follow what ships** and record the conflict in `discovery.md` under "Conflicts". Do
not fix it; it belongs to whoever owns the doc.

## 2. Tokens

Collect the values the prototype will render with. They go into `tokens.css`, mapped
onto the runtime's variable contract (see `assets/template/tokens.css`):

- background, panel, tint, hairline, ink, muted text
- the action color and the **state hues** (in progress / waiting / success / failure)
- both themes if the app has a dark theme
- the body font (self-host it next to the prototype if the license allows; otherwise
  fall back and say so), the monospace font
- the easing curve, the card radius, the control radius
- optional flair inks (brand accent colors that mean no state)

Never invent a token. If the app has no amber, map "waiting" to the closest real token
and note it.

## 3. Flows

A flow is a thing a person does, start to finish, not a page. List 4–7 of them. For
each flow record:

- **name** in the app's own words (the label on the button, the section heading)
- **surfaces** it crosses (page, drawer, dialog, toast, list row)
- **state changes** a person can see: created, in flight, landed, failed, moved,
  expired, offline
- **who causes each change**: the person, another person, an agent/system, time
- **where the outcome lands**: the place a person goes back to for the result

The last two columns are where micro-interactions live. A change the person did not
cause needs to be noticed; a change the person caused needs to be acknowledged; an
outcome that lands somewhere else needs a visible path there.

## 4. The running app

When a URL is given, drive it with the harness's browser tool (Playwright MCP, or
Claude in Chrome when the user wants their own browser):

- screenshot the first viewport and each flow's main surface at desktop width
- open every drawer/dialog a flow uses; screenshot it
- note any motion you see (and its duration if you can measure it)
- copy 2–4 real screenshots into `assets/` (compressed JPEG, ≤ 1200 px wide) for
  demos that need a real screen inside them (capture cards, previews)

**Read only.** Never submit a form, send a message, or change data in an app you were
pointed at. If a flow can only be seen by submitting, describe it from code instead
and say so.

When no URL is given, read the view code instead and say "from code, not seen running"
in `discovery.md`.

## 5. Code anchors

For each flow, find the functions that render its states and handle its events. Each
idea's `where` field cites one of these. Prefer a function name over a line number
(lines drift); give the file. Example: `renderRun(), runFinding() · board.js`.

## Output

`discovery.md` with sections: Design authority · Tokens · Flows (table) · Running app
(screens seen, motion seen) · Code anchors · Conflicts · Not seen. Keep it under 150
lines. It is the input to ideation; nothing in ideation may contradict it.
