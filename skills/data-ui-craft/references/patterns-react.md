# Fix Recipes (React + Tailwind, with cross-stack notes)

Each section is the fix for one or more rules in `audit-rules.md`. Examples are React + Tailwind
because that's the most common case; the **Adapt** note at the end of each section generalizes. When
a fix recurs across call sites, prefer the matching primitive in `templates/` (scaffolded into
`{{KIT_ROOT}}`) over hand-rolling it each time. Always apply the fix in the **data layer** (column
def) when the surface uses one (TanStack/AG Grid/MUI/Ant) — it's one change instead of per-row JSX.

---

## § Numeric cells  — DF1, DF7

Right-align, use tabular figures, and format consistently (fixed decimals, grouping, unit/symbol).

```tsx
// Before
<td className="px-3 py-2">{row.revenue}</td>

// After — right-aligned, tabular, formatted once
const usd = new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 2,
});
<td className="px-3 py-2 text-right tabular-nums">{usd.format(row.revenue)}</td>
```

- `text-right` aligns by place value; `tabular-nums` (CSS `font-variant-numeric: tabular-nums`) stops
  digit-width jitter so columns line up. Right-align the **header** too.
- Pick one precision per column and keep it. Use `Intl.NumberFormat` for currency, percent, and
  grouping rather than ad-hoc string math.
- Kit: `NumericCell` wraps this (props: `value`, `format`, `currency`, `unit`, `decimals`).

**Adapt:** Vue/Svelte/Angular — same classes; bind a formatter in the template. Plain CSS —
`text-align:right; font-variant-numeric: tabular-nums;`. MUI DataGrid — set
`align: "right"` + `valueFormatter` on the column. AG Grid — `cellClass: "text-right"` +
`valueFormatter`.

---

## § Chips & status  — DF2

Render a small fixed value set as a chip; map each value to a deliberate (accessible-contrast) color.

```tsx
const STATUS = {
  active:    "bg-green-100 text-green-800 ring-green-600/20",
  pending:   "bg-amber-100 text-amber-800 ring-amber-600/20",
  inactive:  "bg-gray-100 text-gray-600 ring-gray-500/20",
} as const;

<span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium
  ring-1 ring-inset ${STATUS[row.status] ?? STATUS.inactive}`}>
  {label(row.status)}
</span>
```

- Color must **mean** something (status/category), never decoration. Don't rely on color alone — keep
  the text label (and an icon for the most important states) so it survives color-blindness.
- Keep the palette small and consistent across the app; centralize the value→style map.
- Kit: `Chip` (neutral) and `StatusChip` (semantic variants + optional dot/icon).

**Adapt:** shadcn/ui — wrap its `Badge` with a variant map; MUI — `<Chip color=…>`; Ant —
`<Tag color=…>`. Don't introduce a new chip if the library already ships one.

---

## § Truncation + reveal  — DF3

Truncate to keep rows even, but always provide the full value.

```tsx
<td className="max-w-[28ch] px-3 py-2">
  <span className="block truncate" title={row.note}>{row.note}</span>
</td>
```

- `truncate` = `overflow:hidden; text-overflow:ellipsis; white-space:nowrap`; needs a width bound
  (`max-w-*`/table-layout). For multi-line use `line-clamp-2`.
- The reveal is the important half: `title` for a quick native tooltip, or the kit `Tooltip` for a
  styled one, or expand-on-click, or the row's detail view. Never truncate with no path to the rest.
- Kit: `TruncatedText` (props: `text`, `lines`, `reveal: "tooltip" | "expand"`).

**Adapt:** identical classes everywhere with Tailwind; plain CSS uses the three properties above plus
`-webkit-line-clamp` for multi-line.

---

## § Row state  — DF4

De-emphasize inactive/archived/disabled records so state is visible without reading a column.

```tsx
<tr className={cn("border-b", !row.active && "bg-gray-50 text-gray-400 [&_a]:text-gray-400")}>
```

- Dim text and lightly shade the background; keep it legible (it's de-emphasized, not hidden).
- Pair with a status chip (§ Chips) for the explicit label; the shading is the at-a-glance cue.
- Kit: `DataRow` (props: `state: "active" | "inactive" | "disabled"`).

**Adapt:** any framework — a conditional class on the row element. Data grids — `getRowClassName`
(MUI) / `rowClassRules` (AG Grid).

---

## § Timeline vs table  — DF5

When the data is an event sequence, render a timeline instead of a time-sorted table. Place it where
it fits the layout: a sidebar pop-out, a second column beside the table, or a wider panel.

```tsx
<ol className="relative border-l border-gray-200 pl-6">
  {events.map((e) => (
    <li key={e.id} className="mb-6 last:mb-0">
      <span className="absolute -left-1.5 mt-1.5 h-3 w-3 rounded-full bg-blue-500 ring-4 ring-white" />
      <time className="text-xs text-gray-500 tabular-nums">{fmt(e.at)}</time>
      <p className="text-sm">{e.summary}</p>
    </li>
  ))}
</ol>
```

- The vertical line + dots make sequence, ordering, and gaps legible — the thing a table hides.
- Keep absolute/relative time consistent; group by day when long.

**Adapt:** the structure (ordered list + connector line) ports to any framework; or use a charting/
timeline lib already in the project. Don't add a heavy timeline dependency for a short list.

---

## § Summarize with charts  — DF6

When the user scans rows to perceive a trend, add a small chart or inline sparkline that answers the
question directly — alongside the table, not necessarily replacing it.

- Use the project's existing chart lib (Recharts, Chart.js, visx, ECharts, nivo). Don't add a second.
- A sparkline in a summary row, or a small trend chart above the table, often beats a new screen.
- This is usually an **Opportunity**, not a defect — propose it, size it, let the user opt in.

---

## § Dates  — DF8

Format dates by type and keep one format per column.

```tsx
const date = new Intl.DateTimeFormat("en-US", { dateStyle: "medium" });        // Jun 30, 2026
const dt   = new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" });
<td className="px-3 py-2 tabular-nums">{date.format(new Date(row.createdAt))}</td>
```

- Show relative time ("2h ago") when recency is what matters, with the absolute time in a tooltip.
- `tabular-nums` keeps date columns aligned too.

**Adapt:** `Intl.DateTimeFormat` is platform-native (no dependency). date-fns/Day.js if already used.

---

## § Hover actions + overflow  — PD1, PD6

Keep rare per-row actions off the default view; reveal on hover (desktop) and provide an overflow
menu (always reachable, keyboard- and touch-friendly).

```tsx
<tr className="group">
  {/* …cells… */}
  <td className="px-3 py-2 text-right">
    <div className="invisible flex justify-end gap-1 group-hover:visible
      group-focus-within:visible">
      <IconButton label="Edit" onClick={…}><Pencil/></IconButton>
      <IconButton label="Archive" onClick={…}><Archive/></IconButton>
    </div>
  </td>
</tr>
```

- Use `group` + `group-hover:visible` + `group-focus-within:visible` so keyboard users get them too.
- Prefer `invisible` (reserves space → no layout shift) over `hidden`.
- Put the long tail in an overflow `⋯` menu so nothing is hover-only on touch. Always tooltip the
  icon-only buttons (§ Tooltips).
- Kit: `HoverActions` (renders inline on hover + collapses to overflow on small screens/touch).

**Adapt:** any framework — a hover/focus-within class toggle. Data grids — an actions column with the
same reveal logic.

---

## § Spectrum placement  — PD2, PD3

Re-home an action to match frequency × importance:

- **Too high** (PD2: rare/destructive sitting prominent) → move to hover actions or an overflow menu;
  for destructive actions add a confirm or an undo window.
- **Too low** (PD3: frequent/important buried) → promote to an always-visible primary button or the
  toolbar.
- Decision: frequent **and** important → high; important but infrequent → medium (popover/menu);
  per-item/rare → low (hover/swipe) + tooltip. Make the change, then re-check the surface reads calm.

---

## § Disclosure ordering  — PD4

Inside a popover/menu/drawer, lead with the primary action.

```tsx
<Popover title="Share">
  {/* Primary action visible immediately */}
  <SearchAddPeople autoFocus />
  {/* Secondary: per-row remove appears on hover (see Hover actions) */}
  <PeopleList renderRowActions={(p) => <HoverActions>…</HoverActions>} />
</Popover>
```

- The first thing the user sees in the disclosure should be the thing they opened it to do.
- Kit: `Popover` (focuses its primary slot on open).

---

## § Sequenced onboarding  — PD5

Replace a feature-dump modal with progressive reveal.

- A **checklist** of 3–5 steps that each introduce one capability and mark complete as the user does
  them; persists across sessions.
- Or **contextual tips** that appear when a feature first becomes relevant, not all at once.
- Study real flows (pattern galleries like Mobbin) for sequencing; introduce capability *at the
  moment of need*.
- Kit: `OnboardingChecklist` (steps, completion state, dismissible, resumable).

**Adapt:** the pattern is state + sequencing, not framework-specific. Persist progress (localStorage
or server) so it doesn't re-show.

---

## § Tooltips  — IU1, IU2

Every icon-only control gets both a tooltip **and** an accessible name; ambiguous labels/values get a
tooltip.

```tsx
<Tooltip content="Archive">
  <button aria-label="Archive" className="rounded p-1 hover:bg-gray-100 focus-visible:ring-2">
    <Archive className="h-4 w-4" />
  </button>
</Tooltip>
```

- Tooltip ≠ accessibility: keep `aria-label` for screen readers; the tooltip is the visual hint.
- Don't put *essential* info only in a tooltip on touch (no hover) — use it for hints, not the only
  path to critical data.
- Kit: `Tooltip` (hover + focus, keyboard-dismissible, positioned).

**Adapt:** shadcn/ui & MUI ship tooltips — wrap those. Plain HTML — `title` is a low-effort fallback.

---

## § Click-to-copy  — IU3

Make fiddly values one-click copyable with confirmation feedback.

```tsx
function CopyChip({ value }: { value: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      onClick={async () => { await navigator.clipboard.writeText(value);
        setDone(true); setTimeout(() => setDone(false), 1200); }}
      className="inline-flex items-center gap-1 rounded bg-gray-100 px-1.5 py-0.5
        font-mono text-xs hover:bg-gray-200 focus-visible:ring-2"
      aria-label={`Copy ${value}`}>
      <span className="truncate max-w-[16ch]">{value}</span>
      {done ? <Check className="h-3 w-3 text-green-600"/> : <Copy className="h-3 w-3 opacity-60"/>}
    </button>
  );
}
```

- Always confirm the copy (icon swap or toast) — silent copy leaves the user unsure.
- Kit: `CopyChip` (truncates, confirms, optional toast hook).

**Adapt:** `navigator.clipboard` is universal; wire the project's toast if present.

---

## § Empty/loading/error states  — IU4, IU5, IU6

Every data container needs all three branches. Treat them as part of "done", not extras.

```tsx
if (isLoading) return <TableSkeleton rows={6} />;                 // perceivable progress
if (error)     return <ErrorState onRetry={refetch} message="Couldn't load records." />;
if (!rows.length) return <EmptyState title="No records yet"
  action={<button onClick={onCreate}>Add the first one</button>} />;  // guidance + next step
return <Table rows={rows} />;
```

- **Empty:** say what's missing and offer the next step (don't render a bare frame).
- **Loading:** a skeleton matching the table shape beats a spinner for >~500ms fetches.
- **Error:** plain-language message + retry; never leave a record stuck mid-state.
- Kit: `TableStates` exports `TableSkeleton`, `EmptyState`, `ErrorState`.

**Adapt:** the branch logic is framework-agnostic; data libraries expose `isLoading`/`isError` to
drive it.

---

## § Hover/focus states  — IU7

Interactive elements must look interactive and be keyboard-reachable.

- Real `<button>`/`<a>` over `<div onClick>`. If a div must be interactive: `role`, `tabIndex={0}`,
  and a key handler.
- Provide `hover:` and `focus-visible:` styles (ring/background). `focus-visible` shows the ring for
  keyboard, not mouse.
- Ensure hover-only affordances (§ Hover actions) also trigger on `focus-within`.

---

## § Indicators  — IU8

Surface hidden context (comments, attachments, notes) with a small indicator that doesn't clutter.

```tsx
{row.commentCount > 0 && (
  <Tooltip content={`${row.commentCount} comments`}>
    <button aria-label={`${row.commentCount} comments`} className="inline-flex items-center gap-0.5
      text-xs text-gray-500 hover:text-gray-700">
      <MessageSquare className="h-3.5 w-3.5" /> {row.commentCount}
    </button>
  </Tooltip>
)}
```

- The indicator is the entry point to the full thread/panel (often a drawer — § Orchestration).
- Kit: `CommentIndicator` (count + click → opens a panel/drawer slot you provide).

---

## § Orchestration (in-place surfaces)  — IU9

New functionality rarely needs a new page. Implement it within the current surface:

- **Drawer** for detail/edit beside the list (keeps context); **modal** for a focused, blocking task;
  **popover** for a small action (share, filter); **inline expansion** (a row expands) for per-item
  detail.
- Decide by scope: small action → popover; per-item detail → inline/drawer; focused task → modal;
  rich detail → drawer or split view. A whole route is the last resort, for genuinely separate
  destinations.
- Reuse the project's existing modal/drawer/dialog primitive; don't add a second.

---

## Cross-stack quick map

| Concern | React/Tailwind | shadcn/ui | MUI | AG Grid | Vue/Svelte/Angular |
|---|---|---|---|---|---|
| Right-align + format | `text-right tabular-nums` + `Intl` | same | col `align`+`valueFormatter` | `cellClass`+`valueFormatter` | same classes, template binding |
| Chip | `Chip`/`StatusChip` kit | wrap `Badge` | `<Chip>` | cell renderer | same classes |
| Tooltip | `Tooltip` kit | `Tooltip` | `<Tooltip>` | `tooltipValueGetter` | lib tooltip / `title` |
| Hover actions | `group-hover` | same | actions col | actions cell renderer | hover/focus class toggle |
| States | `TableStates` kit | same | `slots` overlays | `overlayNoRowsTemplate` etc. | branch on loading/error/empty |

Whatever the stack: detect what already exists, reuse it, and never introduce a second styling system
or a duplicate primitive.
