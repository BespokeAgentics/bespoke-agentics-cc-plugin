# Visual Verification — Walking the Rendered Stories

Phase 3. Purpose: catch what code reading misses, not re-derive what it found.
**Graceful degradation is a feature**: any blocker below → skip with a one-line note in
the report; the code-first profiles stand alone.

## Preconditions (check in order, skip on first failure)

1. `--visual` is not `off`.
2. A browser automation tool is available (Claude-in-Chrome MCP tools, or any
   `mcp__*browser*`/`navigate` + screenshot capability).
3. Storybook boots: try `bun --filter '*storybook*' storybook` from the workspace root
   (the design-zip-to-library layout), else `bunx storybook dev -p 6006` from the
   Storybook app dir. Wait for the ready line / port to respond (curl the root URL,
   ~60s budget). If it errors, capture the first error lines for the report and skip.

## Walk procedure

1. Resolve each page's `story_id` (from the inventory; else derive from the story title
   path, e.g. `Pages/InvoiceList` → `pages-invoicelist--default`).
2. For each page profile, navigate to
   `http://localhost:6006/iframe.html?id=<story_id>&viewMode=story` (the iframe URL
   skips the Storybook chrome — you want the page, not the sidebar).
3. Screenshot at desktop width (≥1280px). If stories have multiple variants (themes,
   states), the default variant suffices unless a profile ambiguity names another.
4. Compare against the profile — specifically hunting code-invisible findings:
   - Hover/focus-revealed actions (row action buttons, tooltips with verbs)
   - Truncation/overflow implying "show more" behavior
   - Sticky headers / infinite-scroll cues vs. pagination assumptions
   - Modality (overlays implying flow interruption)
   - Visual grouping implying batch semantics or hierarchy code didn't show
   - Disabled/loading styling not obvious from props
   - Anything rendered from data you didn't trace (a column you missed)
5. Record deltas in the profile: new affordances with `source: "visual"`; confirmed
   ones upgraded to `source: "both"`; contradictions (code said X, render shows Y) → new
   ambiguity. Set `page.visual_verified: true`.

## Interaction limits

Read-only: navigate, hover, screenshot, scroll. Do not submit forms or trigger
mutations — mock handlers may `console.error` or mutate fixture state, polluting later
walks. Clicking tabs/accordion toggles to reveal designed-but-hidden content is fine.

## Budget & teardown

~2 minutes per page; if the walk stalls (story errors, blank iframe), note it on the
profile (`visual_verified: false`, note why) and move on. Kill the Storybook process
when done; report which pages were verified vs. skipped and why.
