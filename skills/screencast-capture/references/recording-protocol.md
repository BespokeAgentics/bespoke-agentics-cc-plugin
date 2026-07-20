# Phase 1 — Recording protocol (Claude-in-Chrome)

You drive the browser live and record it with `gif_creator`. The recording is only as good as the
frames it captures, so the rhythm matters: **act, then screenshot, then act** — every screenshot is a
frame, and the moments between clicks are where the story reads. This runs in the **main session**
(not a subagent) because the setup gate and the handoff question need the user.

## Step 1 — Load the tools (one ToolSearch call)

The Claude-in-Chrome tools are deferred. Load the whole set you'll need in a single call — never one
at a time:

```
ToolSearch: select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__gif_creator
```

Add `mcp__claude-in-chrome__read_console_messages` too if you expect to debug a flaky page. Then:

```
tabs_context_mcp { createIfEmpty: true }
```

This is **required before any other browser tool** — it returns the MCP tab group and the tab IDs you
must pass as `tabId`. Never reuse a tab ID from another session.

## Step 2 — Fresh tab + navigate

Unless `--tab` was given, create a new tab so the recording starts clean:

```
tabs_create_mcp            -> capture the new tabId
navigate { tabId, url: "<start-url>" }
```

Standalone `navigate` will create the group for you, but creating the tab explicitly keeps the
`tabId` unambiguous when the group already has tabs.

## Step 3 — Manual setup gate (BEFORE recording)

This is the privacy boundary. If the start state needs a login, or a cookie/consent banner is
covering the app, **stop and hand control to the user**:

> "I've opened `<url>`. Please log in / dismiss the banner in the browser, then tell me you're ready
> and I'll start recording."

Rules that are not negotiable:
- **You never type passwords, card numbers, or other credentials** — entering credentials is a
  prohibited action. The user does it.
- Do it **before** `start_recording`, so the login screen, keystrokes, and consent clicks never land
  in the footage.
- For consent/cookie popups you *do* handle, choose the most privacy-preserving option (decline
  non-essential).

When the user is ready, `computer{action:screenshot, tabId}` to confirm the app sits at the flow's
starting state. If it doesn't, fix it (navigate/scroll) before recording.

## Step 4 — Record

```
gif_creator { action: "start_recording", tabId }
computer    { action: "screenshot", tabId }          # first frame = the opening state
```

Now perform the shot list from `capture-plan.md`, one step at a time:

- Interact with `computer` (`left_click`, `type` for non-secret text, `scroll`, `hover`,
  `left_click_drag`) and `navigate` for page changes.
- **Consult a screenshot before clicking** an element you haven't located yet — put the cursor tip in
  the centre of the target.
- **Screenshot between meaningful steps.** Each is a frame; without them the GIF jumps. A good cadence
  is: do one logical action → screenshot → next action.
- Insert `computer{action:"wait", duration: N}` (≤10s) where the app loads, animates, or fetches, so
  the recording shows the result rather than a spinner.
- Keep it to what the user asked for. Don't wander — extra menu-hunting becomes dead air the reel has
  to trim.

When the flow is complete:

```
computer    { action: "screenshot", tabId }          # last frame = the final state
gif_creator { action: "stop_recording", tabId }
```

## Step 5 — Export (overlay mapping)

Map `OVERLAYS` to `gif_creator.options`, then export with download so the file is written to disk:

| `OVERLAYS` | showClickIndicators | showActionLabels | showProgressBar | showDragPaths | showWatermark |
|---|---|---|---|---|---|
| `clean` | false | false | false | false | false |
| `clicks` *(default)* | **true** | false | false | false | false |
| `full` | true | true | true | true | true |

`quality` defaults to `10` (lower = better); leave it unless the user wants a smaller file.

```
gif_creator {
  action: "export",
  tabId,
  download: true,
  filename: "{CAPTURE_SLUG}.gif",
  options: { showClickIndicators: <per table>, showActionLabels: <...>,
             showProgressBar: <...>, showDragPaths: <...>, showWatermark: <...> }
}
```

The GIF is written to Chrome's download directory (the `filename` may be suffixed if it collides,
e.g. `{CAPTURE_SLUG} (1).gif`). Relocation + conversion happen in `convert-and-handoff.md`.

## Browser hygiene & failure handling

- **Never trigger a native dialog.** A JavaScript `alert/confirm/prompt` freezes the extension and it
  stops receiving commands. Avoid clicking controls that raise them; if one appears, tell the user to
  dismiss it in the browser, then re-run `tabs_context_mcp`.
- **Don't loop on failure.** If a click/navigation fails, re-`screenshot`, adjust the coordinate, and
  retry — but only 2–3 times. If it still fails, `gif_creator{action:"clear", tabId}` to drop the
  half-recording, then stop and report what you attempted. Do not keep hammering the same action.
- **Never bypass CAPTCHAs or bot-detection.** If the flow hits one, capture what's reachable or stop
  and report.
- The recording is scoped to the tab group; `clear` discards captured frames if you need to restart.
