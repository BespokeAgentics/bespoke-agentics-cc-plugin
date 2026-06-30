# The Three Pillars of Data-UI Craft

The whole skill rolls up to one idea: **a dashboard is built to display data, so the data — not a
generic template — should drive every decision.** Designing a screen that *looks* good is easy.
Orchestrating one that *works in use* is the hard part, and the difference shows up in a small,
repeatable set of details. Those details cluster into three pillars. This file explains the *why* so
the model applying the skill can reason past the literal rules; `audit-rules.md` turns each pillar
into checkable rules, and `patterns-react.md` turns each fix into code.

---

## Pillar 1 — Data drives the form

The single most common beginner tell is a layout that was decided *before* the data was considered:
a tidy grid of left-aligned text that ignores what each column actually holds. Fix it by letting the
data's **type and semantics** choose its representation.

**Categorical data → chips, not raw text.** Fields with a small set of discrete values — department,
role, employment status, plan tier, environment — read far faster as chips/badges than as words in a
sentence. The chip gives the eye a shape and (optionally) a color to group by, so a column of
statuses becomes scannable instead of a wall of text.

**Numeric data → right-aligned, with tabular figures.** Numbers compare by place value: the
thousands digit must sit above the thousands digit. Right-align numeric columns, use tabular
(monospaced-width) figures so digits don't jitter, and keep decimal precision and units consistent
down the column. `1,240.5` over `38.00` over `1,000,000.00`, all flush right, can be compared at a
glance; left-aligned with ragged decimals cannot.

**Long text → truncate with breathing room, plus a way to see the rest.** Free-text columns (notes,
descriptions, URLs) will otherwise dictate row height and column width for everyone. Truncate to a
sensible width with an ellipsis, give the column room, and make the full value reachable (tooltip,
expand, or detail view). Truncation without a reveal path is its own bug.

**State → visual de-emphasis.** Inactive, deactivated, archived, or disabled records should *look*
different — shaded/dimmed rows — so the eye separates "live" from "not live" without reading a status
column. The data's state is information; encode it in the form.

**Sometimes the right form isn't a table at all.** This is the deepest version of the pillar. Some
data is poorly served by a table even when a table is *usable*. Time-sequenced data — an event
log, an activity history, a sequence of status changes — is fundamentally temporal, and a
time-sorted table makes the user reconstruct the timeline in their head. A **timeline** shows the
same data as what it is. And the layout can flex to fit: the timeline can be a sidebar pop-out, a
second column beside the table, or a wider panel. Likewise, when a user would otherwise hunt through
a column of timestamps to understand a trend, a small **chart** answers the question directly. Ask of
every surface: *what is the nature of this data, and what container shows that nature most directly?*

**The test:** strip the column headers. Can you still tell what kind of data each column holds — by
alignment, by chips, by shading? If yes, the form is doing its job. If every column looks like every
other column, the data isn't driving the form yet.

---

## Pillar 2 — The right things are hidden until needed

A surface that shows every control at once is exhausting and, paradoxically, *harder* to use,
because the primary action competes with a dozen rare ones for attention. The craft is ranking
controls and revealing them accordingly.

**The spectrum of explicitness.** Every interactive element sits somewhere on a line from
*always-visible* (high explicitness) to *revealed only on interaction* (low explicitness):

- **High** — always on screen. Reserve for the surface's primary, frequent actions (e.g. a global
  "Share" or "New" button, the search box).
- **Medium** — one interaction away, behind a popover, menu, or overflow (`⋯`). For actions that
  matter but aren't used every visit.
- **Low** — revealed contextually: a row's secondary actions appearing on **hover** (with a tooltip
  to name them), a **swipe** gesture on mobile, a right-click menu. For per-item actions that would
  otherwise clutter every row.

The rule for placing an action is **frequency × importance**. A frequent, important action goes high.
A rare action — even an important one like "remove user" — can go low, because surfacing it on hover
keeps the default view calm while still making it reachable. A mismatch in either direction is a
finding: a rare action holding prime real estate, or a frequent action buried two clicks deep.

**Progressive disclosure** is the spectrum applied over a *sequence*: show the most important thing
first, then reveal the next thing when it's relevant. A share popover shows the search-to-add box
immediately (the primary action), while "remove" appears on hover per row (secondary). Apple's
Reminders is a clean example — the primary content is front and center; secondary actions live behind
a swipe. The point is to sequence functionality from most to least important so the surface never
asks the user to parse everything at once.

**Onboarding is progressive disclosure over time.** The beginner move is a big modal that explains
every feature on first load — which users dismiss instantly and forget. The craft move is to reveal
functionality gradually: a checklist that introduces one capability at a time, or contextual tips
that appear at the moment a feature becomes relevant. Studying real product onboarding flows (pattern
galleries like Mobbin and similar are useful for this) is the fastest way to learn good sequencing.

**The test:** for each control on the surface, ask "how often, and how important?" Then ask "is its
current visibility matched to that?" The clutter you remove and the buried things you surface are the
findings.

---

## Pillar 3 — Invisible UI makes it all function

Effective UI is partly what's visible and partly what's hidden but functional. The hidden layer —
the components, states, and interactions that aren't on screen at rest — is precisely what separates
a polished dashboard from a flat mock. Beginners build the visible 80% and skip the invisible 20%
that makes it usable.

**Tooltips and contextual guidance.** The most-omitted primitive. Any icon-only control, any
abbreviated or ambiguous label, any value that benefits from explanation, should have a tooltip. It's
the cheapest way to make a dense surface self-explanatory without adding visible clutter.

**Hidden affordances inside dense data.** A dense table can quietly carry a lot of function: a
**click-to-copy** chip on IDs/emails/codes; a **comment/annotation indicator** tied to a cell that's
reachable without cluttering the grid; inline edit on hover. These appear when relevant and vanish
when not.

**The full set of states.** A component isn't done when the happy path renders. The invisible states
are where products feel finished or broken: **hover** (affordance — does it look interactive before
you click?), **focus** (keyboard), **active/selected**, **disabled**, and — for any container that
loads data — **empty**, **loading**, and **error**. An empty state with a next step, a loading
skeleton, and an error branch with a retry are not extras; they're the difference between "works" and
"works only when the data cooperates."

**Orchestration over new pages.** New functionality rarely needs a dedicated new page. The craft is a
careful, context-sensitive implementation *within the existing structure* — a modal, a drawer, a
popover, an inline expansion, a hover action. This applies to big elements (drawers/modals) and small
ones (a copy chip, a tooltip) alike. Thoughtful spacing, sizing, and interaction design apply to the
hidden parts as much as the visible ones.

**The test:** unplug the data and shrink the window. Does every container have something to say when
empty, loading, and failing? Does every icon explain itself? Can you reach the values you'd want to
copy or annotate without leaving the surface? The gaps are the findings.

---

## How the pillars relate

The pillars are independent enough to audit separately but reinforce each other in practice:

- Pillar 1 decides **what each piece of data looks like**; Pillar 2 decides **which controls are
  visible around it**; Pillar 3 supplies **the hidden affordances and states** that make both usable.
- A chip (Pillar 1) often carries a copy action (Pillar 3) and a tooltip (Pillar 3), and its rare
  edit action lives on hover (Pillar 2). One cell can express all three.
- When in doubt, return to the root principle: **the surface exists to display data**. Every choice
  should make the data more legible, the needed action more reachable, and the surface calmer.
