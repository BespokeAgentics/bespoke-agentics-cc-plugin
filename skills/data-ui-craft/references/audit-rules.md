# Data-UI Craft — Audit Rule Catalog

Apply these against each surface from Phase 0.5. Every finding records: **rule ID**, **pillar**,
`file:line`, **what the user experiences** (not the code symptom), **severity**, and a **fix
pointer** into `patterns-react.md`. Severities are *defaults* — adjust with § Calibration at the
bottom. Rule IDs are stable so reports and the wiki log can reference them.

Severity scale: **Critical** (blocks a task / causes data loss or silent failure) ·
**High** (significant confusion, extra steps, frequent errors) · **Medium** (friction or broken
convention; user recovers with effort) · **Low** (polish) · **Opportunity** (positive or
high-value low-effort win).

---

## Pillar 1 — Data drives the form  (rule prefix `DF`)

| ID | Detect | Default severity | User experience when violated | Fix |
|----|--------|------------------|-------------------------------|-----|
| **DF1** | Numeric / currency / percentage column rendered left- or center-aligned, or with ragged decimal precision down the column (`text-left` on a number cell; `{value}` with no formatter; mixed `.5` / `.00`). | High | Can't compare magnitudes at a glance; the eye does arithmetic the layout should do. | `patterns-react.md` § Numeric cells |
| **DF2** | Categorical / enum field rendered as raw text (`{row.status}`, `{dept}`) when it has a small fixed value set (status, role, department, tier, env, type). | High | A wall of words where the eye wants groupable shapes; scanning by category is slow. | § Chips & status |
| **DF3** | Free-text column with no truncation (long notes/URLs setting row height/column width), **or** truncation (`truncate`, `line-clamp`) with no way to read the full value. | Medium | Rows of uneven height / blown-out columns, or text cut off with no reveal. | § Truncation + reveal |
| **DF4** | Record state (inactive, deactivated, archived, disabled, draft) not visually encoded on the row/card — only knowable by reading a status column. | Medium | "Dead" records look identical to live ones; users act on the wrong row. | § Row state |
| **DF5** | Time-sequenced / event data (activity log, history, status changes, audit trail) presented as a time-sorted **table**. | High | The user reconstructs the timeline in their head; sequence and gaps are invisible. | § Timeline vs table |
| **DF6** | A column of timestamps or repeated metrics the user must scan to perceive a trend, where a small chart/sparkline would answer the question directly. | Opportunity | Hunting through rows to infer what one glance at a chart would show. | § Summarize with charts |
| **DF7** | Numeric values missing units/symbols, or applying them inconsistently (`1240` vs `$1,240` vs `1240 USD` in one column). | Low | Ambiguity about what the number means; mis-reads. | § Numeric cells |
| **DF8** | Dates/times shown as raw ISO strings (`2026-06-30T14:25:00Z`) or in inconsistent formats within one column. | Low | Hard to read and compare; type not respected. | § Dates |

**Pillar-1 escalation cues:** DF1 → **Critical** if the table is the product's core comparison view
(pricing, financials, leaderboards). DF5 → escalate if the temporal data is the primary thing the
user came to understand.

---

## Pillar 2 — Progressive disclosure & the spectrum of explicitness  (rule prefix `PD`)

| ID | Detect | Default severity | User experience when violated | Fix |
|----|--------|------------------|-------------------------------|-----|
| **PD1** | Every row / card shows all its actions inline at all times (3+ action buttons per row, always rendered). | Medium | Visual noise scales with row count; the primary action is lost among rare ones. | `patterns-react.md` § Hover actions + overflow |
| **PD2** | A rare and/or destructive action (delete, deactivate, reset) is given primary, always-visible prominence equal to the main action. | High | Constant accidental-click risk; rare action steals attention from the common one. | § Spectrum placement |
| **PD3** | A frequent, important action is buried behind extra clicks (in an overflow menu, a sub-tab, a detail page) while rare actions sit on top. | High | The thing users do most takes the most effort. | § Spectrum placement |
| **PD4** | A popover/menu/drawer whose **primary** action isn't immediately visible on open (e.g. a Share popover that opens to settings instead of the add/search box). | Medium | The user hunts inside the disclosure for the obvious next step. | § Disclosure ordering |
| **PD5** | Onboarding / feature introduction delivered as one large modal listing many features at once, with no sequencing. | Medium | Dismissed and forgotten; nothing is learned at the moment it's needed. | § Sequenced onboarding |
| **PD6** | Per-item secondary actions exist but there's no hover-reveal, overflow, or swipe pattern available to defer them. | Low | Forces an all-or-nothing visibility choice; usually shows up as PD1. | § Hover actions + overflow |

**How to place an action (frequency × importance):** frequent **and** important → high (always
visible). Important but infrequent → medium (popover/menu). Per-item or rare → low (hover/swipe),
with a tooltip naming it. Flag any action whose current visibility doesn't match this — too high
(clutter/risk) **or** too low (buried).

---

## Pillar 3 — Invisible UI  (rule prefix `IU`)

| ID | Detect | Default severity | User experience when violated | Fix |
|----|--------|------------------|-------------------------------|-----|
| **IU1** | Icon-only button/control with no tooltip **and** no `aria-label`/accessible name. | High | User must click to discover what a control does; screen readers announce nothing. | `patterns-react.md` § Tooltips |
| **IU2** | Ambiguous label, abbreviation, truncated header, or value that needs explanation, with no tooltip/help affordance. | Low | Quiet confusion; the user guesses at meaning. | § Tooltips |
| **IU3** | Copyable values (IDs, emails, API keys, hashes, order numbers) with no click-to-copy affordance. | Medium | Manual select-and-copy of fiddly strings; transcription errors. | § Click-to-copy |
| **IU4** | A data container (table/list/grid/panel) with no **empty** state — renders nothing or a bare frame when there's no data. | High | A blank screen reads as broken; no guidance on what to do next. | § Empty/loading/error states |
| **IU5** | A data container with no **loading** state (no skeleton/spinner) for fetches >~500ms. | Medium | The user can't tell if the app is working or stuck. | § Empty/loading/error states |
| **IU6** | A data container / data action with no **error** state and retry. | High | Silent failure; the user trusts stale or missing data. | § Empty/loading/error states |
| **IU7** | Interactive element with no hover/focus affordance, or not keyboard-focusable (`<div onClick>` with no role/tabindex, no `:hover`/`:focus` styling). | Medium | Controls look dead; keyboard users can't reach them. | § Hover/focus states |
| **IU8** | Comments/annotations/attachments/metadata exist for a row or cell but there's no indicator surfacing them. | Low | Hidden context the user never discovers. | § Indicators |
| **IU9** | A whole new page/route created for functionality that belongs in a popover, drawer, or inline expansion of the current surface. | Medium | Needless navigation and context loss for a small task. | § Orchestration (in-place surfaces) |

**Pillar-3 escalation cues:** IU4/IU6 → **Critical** if the empty/error happens on the primary
data path of the app (the main table is blank on first load with no guidance, or a failed save shows
nothing). IU1 → escalate if the icon-only control is destructive.

---

## Calibration

These keep the report trustworthy — an over-alarming audit gets ignored.

- **Don't flag what you can't see.** If a tooltip/handler might live in a wrapper or a column-def
  elsewhere, write "potentially missing — verify at `<location>`", not a confirmed violation. Code
  patterns are *proxies*: a present `aria-label` doesn't guarantee it's meaningful; note the
  distinction.
- **One finding per root cause.** 12 numeric columns left-aligned is **one** DF1 finding with 12
  instances, not 12 findings. Group by rule + surface.
- **Context sets the bar.** An internal admin power-tool tolerates more density than a consumer
  onboarding flow; a financial comparison table makes DF1 Critical that would be High elsewhere. If
  the audience/criticality is unclear, ask before escalating.
- **Rate conservatively.** Torn between two levels → choose the lower.
- **Respect intent.** Some "violations" are deliberate product choices (a deliberately sparse view,
  a power-user surface that assumes memorized icons). Present these as findings to *confirm*, not
  facts to fix — the implement phase only touches the accepted set.
- **Severity ≠ effort.** Note quick wins (often Low/Medium with tiny diffs, like right-aligning a
  column or adding a tooltip) explicitly in the report's Opportunities so the user can knock them out
  fast.
