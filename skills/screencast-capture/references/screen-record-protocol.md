# Phase 1 (engine = `screen`) — OS screen recording

The `screen` engine records a real **monitor** with ffmpeg while you drive the browser exactly as the
`chrome-gif` engine does — but at **native resolution + configurable bitrate**, writing MP4 directly
(no GIF, no ~1200px cap, no dithering). It's macOS-only (avfoundation) and needs **Screen-Recording
permission**. All ffmpeg work goes through `scripts/screen_record.sh`; you never call ffmpeg by hand.

Runs in the **main session** (the setup gate + Phase-4 question need the user). The recorder process
is `nohup`-detached, so you `start` it, drive the browser across several tool calls, then `stop` it.

## Step 1 — Pick the monitor + prove permission (pre-flight)

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/screencast-capture/scripts/screen_record.sh devices
```
lists `Capture screen 0/1/2 -> [idx]`. Resolve `DISPLAY` (the avfoundation index):
- If `--display` was given, use it.
- Else if there's one screen, use it. If several and it's unclear which holds the browser, run
  `check <idx>` on each and (optionally) `Read` the test clip it writes (`$TMPDIR/screencast-capture/perm_test_<idx>.mp4`)
  to see which shows the browser — or just ask the user in the interview.

Then **gate on permission**:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/screencast-capture/scripts/screen_record.sh check <DISPLAY>
```
- Exit 0 → permission OK, screen is non-black. Proceed.
- Exit 5 → **Screen-Recording permission not granted** (avfoundation hangs; the script kills it after
  ~13s). **Stop and relay its message** — you cannot grant it (a system security setting). The user
  enables it in *System Settings ▸ Privacy & Security ▸ Screen Recording* for the app running Claude
  Code (Terminal / iTerm / VS Code / Claude), fully quits + reopens it, then re-runs. Do not loop.

## Step 2 — Size the window + compute the crop (`--crop auto`)

OS capture grabs the **whole monitor**, so trim to the browser. After the manual-setup gate (window
open, logged in), give it a clean landscape size and read its geometry:

```
resize_window { tabId, width: 1600, height: 1000 }        # a tidy 16:10 window
javascript_tool: JSON.stringify({dpr:devicePixelRatio, x:screenX, y:screenY, w:outerWidth, h:outerHeight})
```

Compute the crop in **captured (device) pixels** — multiply CSS coords by `dpr`, force even dims:

```
CW = even(w*dpr)   CH = even(h*dpr)   CX = round(x*dpr)   CY = round(y*dpr)      # even(n)=n-(n%2)
CROP = "CW:CH:CX:CY"
```

- `--crop auto` (default): use the rect above. Assumes the window sits on the target display; for
  odd multi-monitor offsets the coords may be off — fall back to one of the next two.
- `--crop off`: record the full monitor (simplest — maximize the browser and keep the screen clean).
- `--crop W:H:X:Y`: explicit pixels.

**Zero-geometry fallback (common):** some Chrome windows report `outerWidth/Height: 0` and
`screenX/Y: 0` (the API just doesn't populate them, especially with multiple windows). You cannot
crop from that. When the geometry looks bogus, **do not `--crop auto`** — ask the user to **maximize
the browser alone on the target monitor** (or fullscreen it with Ctrl+Cmd+F) and record the full
display with `--crop off`. That's the reliable path and needs no math.

(On this class of machine `dpr` is often 1, so CSS px == device px; on a Retina display `dpr` is 2 and
the crop is 2× the CSS rect — the recording is correspondingly crisper.)

## Step 3 — Start recording

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/screencast-capture/scripts/screen_record.sh start <DISPLAY> "{MP4_PATH}" {FPS} {CRF} "{CROP}"
```
The script self-detaches ffmpeg (pidfile in `$TMPDIR/screencast-capture/record.pid`), then confirms
**bytes are actually landing** before returning — if it reports no data, that's an unresolved
permission problem; stop and tell the user. The recorder draws the real cursor and flashes clicks
(`-capture_cursor -capture_mouse_clicks`), so on-screen actions read clearly without gif overlays.

## Step 4 — Drive the flow, then stop

Perform the same shot list from `capture-plan.md` with `computer` / `navigate`. This is **real-time
video**, so pacing matters more than screenshots: insert `computer{wait}` where the app loads or
animates, and don't rush between steps (nothing is captured "per screenshot" here — it's continuous).
Avoid native `alert/confirm/prompt` dialogs as always.

**Dead time is real.** Unlike the gif engine (where each screenshot *is* a frame), the screen engine
records continuously — so your own think-time *between* tool calls lands in the video as pauses. A
~30s demo can produce a multi-minute raw file. Mitigate by **batching actions** (`browser_batch`) so
consecutive clicks/waits happen in one round-trip, and **don't narrate to yourself between calls**.
Either way, hand the raw MP4 to `screencast-highlight-reel` — trimming that dead time down to the real
moments is exactly what it does. Also consider fullscreening the app (Ctrl+Cmd+F) before recording so
the browser chrome + menu bar stay out of frame.

When the flow is done:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/screencast-capture/scripts/screen_record.sh stop "{MP4_PATH}"
```
This sends **SIGINT** (never SIGKILL) so ffmpeg writes the trailer, waits for it to finalize, and
prints `{MP4_PATH}` + its `WxH` + real duration. Keep the duration — it feeds the reel interval.

## Then

`{MP4_PATH}` is a native-resolution, real-duration H.264 MP4 — **skip Phases 2–3** (no GIF to export
or convert) and go straight to Phase 4 (present + hand off) in `convert-and-handoff.md`.

## Guardrails

- The whole monitor is recorded until you crop — anything else on that screen is in-frame. Keep
  sensitive windows off it; the browser must be foreground on the target display.
- Never `kill -9` the recorder — the MP4 won't finalize. Only `screen_record.sh stop`.
- If `start` fails or the app crashes, run `screen_record.sh stop "{MP4_PATH}"` anyway to clean up the
  pidfile before retrying.
