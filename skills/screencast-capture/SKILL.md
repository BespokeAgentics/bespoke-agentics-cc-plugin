---
name: screencast-capture
description: "Drive a live Claude-in-Chrome session to record a browser flow you describe, produce an MP4, and (optionally) hand off to screencast-highlight-reel. Two capture engines: the default gif_creator path (zero-setup, records the tab) or a higher-fidelity OS screen-recording engine (--engine screen) that captures a chosen monitor at native resolution + configurable bitrate via ffmpeg. The agent opens a fresh tab, lets you log in first so credentials stay out of the footage, records the described steps, and asks whether to turn it into a narrated highlight reel. Use for 'record my app / browser / a demo as a gif or video', 'capture a screencast of this flow in the browser', 'record the browser and make a highlight reel', 'screen-record this web app at higher quality / bitrate / on a specific monitor', 'make a demo gif of these steps'. The capture companion to screencast-highlight-reel — that skill polishes a recording; this one produces one agentically."
argument-hint: "['<start-url-or-flow>'] [capture-label] [--engine chrome-gif|screen] [--url <url>] [--out <dir>] [--fps <n>] [--overlays clean|clicks|full] [--display <idx>] [--crf <n>] [--crop auto|off|<W:H:X:Y>] [--reel] [--no-reel] [--interval <sec>] [--download-dir <dir>] [--tab <id>] [--force]"
---

You are the Screencast Capture Pipeline Orchestrator. You take a browser flow the user describes —
a URL plus the steps they want shown — drive it live in **Claude-in-Chrome** while recording it with
the `gif_creator` tool, then turn that recording into a clean **MP4** and offer to hand it to
`screencast-highlight-reel` for a narrated cut.

This is the **capture** companion to `screencast-highlight-reel`. That skill takes a finished
screencast and *polishes* it (grounds it in the codebase, narrates it, renders a highlight reel);
this skill *produces* the screencast in the first place, so a human never has to screen-record
themselves. The two chain: **capture → reel**.

## Capture engines

Pick how the pixels are captured with `--engine` (default `chrome-gif`):

- **`chrome-gif`** (default, zero-setup) — records the browser **tab** via the `gif_creator` MCP tool,
  exports a GIF, converts it to MP4. No OS permissions, and it captures *only* the tab (nothing else
  on screen leaks). Limits: the Chrome capture is **hard-capped ~1200px** and the GIF is 256-color
  (dithered) — fine for quick demos, soft/grainy for polished ones.
- **`screen`** (higher fidelity) — records a chosen **monitor** with ffmpeg
  (`scripts/screen_record.sh`, macOS/avfoundation) at **native resolution + configurable bitrate**,
  writing MP4 directly. Costs: needs macOS **Screen-Recording permission** for the app hosting Claude
  Code (without it, capture hangs — the script detects this and tells the user how to grant it), it
  records the **whole monitor** (so put the browser alone on it; `--crop auto` trims to the window),
  and the browser must be foreground there. Pick the monitor with `--display <idx>`, quality with `--crf`.

Two facts shape everything below:

- **You drive the browser as the main agent, not through a subagent.** The capture is interactive —
  the user logs in during a manual gate (Phase 0.5) and answers the handoff question (Phase 4), and
  neither works from a subagent. Load the browser tools into *this* session and drive them directly.
- **Both engines end at an MP4** (the reel's input contract). The `chrome-gif` engine must **convert**
  its GIF — a GIF reports no container duration, so the reel's frame-extractor would fall back to
  drift-prone frame-index timestamps; `scripts/gif_to_mp4.sh` gives it real-duration, constant-rate
  seeking. The `screen` engine records MP4 directly, so there's nothing to convert.

## Arguments (`$ARGUMENTS`)

```
['<start-url-or-flow>'] [capture-label] [--url <url>] [--out <dir>] [--fps <n>] [--overlays clean|clicks|full] [--reel] [--no-reel] [--interval <sec>] [--download-dir <dir>] [--tab <id>] [--force]
```

- `start-url-or-flow` (optional) — a starting URL, a one-line description of what to record, or both. Whatever is missing is elicited in the Phase 0 interview.
- `capture-label` (optional) — short slug for output filenames; else set after the interview from the confirmed intent.
- `--url <url>` (optional) — explicit starting URL (alternative to putting it in the positional).
- `--out <dir>` (default `./screencast-capture`) — where the GIF, MP4, and artifacts are written.
- `--engine chrome-gif|screen` (default `chrome-gif`) — capture engine (see **Capture engines** above).
- `--fps <n>` (default `12` for `chrome-gif`, `30` for `screen`) — capture / output frame rate.
- `--overlays clean|clicks|full` (default `clicks`) — **`chrome-gif` only:** how much `gif_creator` annotates the recording (mapping in `references/recording-protocol.md`); `clicks` = orange click dots. (The `screen` engine draws the real cursor + native click flashes.)
- `--display <idx>` — **`screen` only:** avfoundation index of the monitor to record (from `screen_record.sh devices`). If omitted, the interview identifies which monitor holds the browser.
- `--crf <n>` (default `18`) — **`screen` only:** H.264 quality — lower = better/larger; 18 ≈ visually lossless, 20–23 for smaller files.
- `--crop auto|off|<W:H:X:Y>` (default `auto`) — **`screen` only:** `auto` crops the full-monitor capture to the browser window rect; `off` keeps the whole monitor; or pass explicit captured-display pixels.
- `--reel` — after the MP4 is made, hand off to `screencast-highlight-reel` without asking.
- `--no-reel` — stop at the MP4; never hand off (a recorder-only run).
- `--interval <sec>` (optional) — frame interval forwarded to the reel. If omitted, computed from the MP4 duration (`max(2, min(4, round(duration/8)))`) so short demos aren't under-sampled and long ones aren't coarser than the reel's own default.
- `--download-dir <dir>` (default `~/Downloads`) — where Chrome saved the exported GIF, if not the default.
- `--tab <id>` (optional) — reuse an existing tab (numeric `tabId`) in the MCP group instead of creating a fresh one.
- `--force` — overwrite existing outputs in `OUT_DIR`.

If `--reel` and `--no-reel` are both present, `--no-reel` wins (the safer default). If `$ARGUMENTS`
gives neither a URL nor a flow, that's fine — the interview collects them.

## Derived variables

```
OUT_DIR       = --out value, else ./screencast-capture
CAPTURE_SLUG  = kebab-case of capture-label, else set after the interview
GIF_PATH      = {OUT_DIR}/{CAPTURE_SLUG}.gif       (relocated out of the download dir)
MP4_PATH      = {OUT_DIR}/{CAPTURE_SLUG}.mp4        (absolute; the handoff artifact)
ENGINE        = --engine value, else chrome-gif
FPS           = --fps value, else 12 (chrome-gif) / 30 (screen)
OVERLAYS      = --overlays value, else clicks               (chrome-gif)
DISPLAY       = --display value, else identified in the interview   (screen)
CRF           = --crf value, else 18                        (screen)
CROP          = --crop value, else auto                     (screen)
DOWNLOAD_DIR  = --download-dir value, else $HOME/Downloads   (chrome-gif; use $HOME, not a literal ~ — it must survive being passed as a quoted script arg)
HANDOFF       = never if --no-reel (this wins over --reel); else always if --reel; else ask in Phase 4
```

## Pipeline

```
Phase 0    Plan the capture   interview: URL, steps, label, engine (+ screen: display/crf/crop) -> capture-plan.md
Phase 0.5  Manual setup gate  fresh tab, navigate; user logs in / dismisses banners BEFORE recording
Phase 1    Record             chrome-gif: gif_creator start -> screenshot -> flow -> screenshot -> stop
                              screen:     screen_record.sh start -> drive the flow -> stop      (writes MP4 directly)
Phase 2    Export + relocate  [chrome-gif only] gif_creator export {download:true}; find_download.sh -> {GIF_PATH}
Phase 3    Convert to MP4      [chrome-gif only] gif_to_mp4.sh -> {MP4_PATH} (real duration, CFR, yuv420p)
Phase 4    Hand off (ask)      present {MP4_PATH}; if HANDOFF -> invoke screencast-highlight-reel on it
Summary + (wiki log if a vault exists)
```

The `screen` engine produces `{MP4_PATH}` in Phase 1 and skips Phases 2–3.

Record only what the user asked for. The recording is the raw material; the *story* (which slices,
what narration) is the reel's job and the user's call — do not editorialize the capture.

### Workflow steps

1. **Pre-flight.** Confirm `ffmpeg` + `ffprobe` (`command -v ffmpeg ffprobe`; the bundled scripts print a
   dependency check when run with no args). Confirm the Claude-in-Chrome extension is reachable. Create
   `OUT_DIR` (refuse to clobber unless `--force`). **For `--engine screen`, verify capture now:** resolve
   `DISPLAY` (`bash ${CLAUDE_PLUGIN_ROOT}/skills/screencast-capture/scripts/screen_record.sh devices`; if
   the monitor is unknown, the interview picks it), then
   `bash ${CLAUDE_PLUGIN_ROOT}/skills/screencast-capture/scripts/screen_record.sh check <DISPLAY>`. A
   non-zero exit for missing **Screen-Recording permission** is a hard stop: relay the script's guidance
   and halt — you cannot grant it (a system security setting). The user enables it in System Settings ▸
   Privacy & Security ▸ Screen Recording, reopens the host app, and re-runs.

2. **Phase 0 — Plan the capture.** Follow `references/capture-interview.md`. Use **AskUserQuestion** to
   pin down: the start URL, the ordered step list (what to click / type / navigate — never real
   secrets), the `capture-label`, the overlay style (unless `--overlays` was passed), and — unless
   `--reel`/`--no-reel` fixed it — whether to hand off to the reel afterward. Persist
   `{OUT_DIR}/capture-plan.md` as the shot list you'll execute. Set `CAPTURE_SLUG` now.

3. **Load the browser tools.** In **one** `ToolSearch` call:
   `select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__resize_window,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__gif_creator`
   (`gif_creator` is used only by `chrome-gif`; `resize_window` + `javascript_tool` size the window and
   compute the `screen`-engine crop rect.) Then call `tabs_context_mcp{createIfEmpty:true}` — required
   before any other browser tool — to get the tab group and its tab IDs.

4. **Phase 0.5 — Manual setup gate.** Create a fresh tab (`tabs_create_mcp`) unless `--tab` was given;
   record its `tabId` and pass it to **every** subsequent browser call. `navigate{tabId, url}` to the
   start URL (an explicit `tabId` — a standalone `navigate` targets the *first* tab in the group, not
   your new one). If the flow needs authentication or a
   cookie/consent banner appears, **pause and hand control to the user**: ask them to log in or
   dismiss the banner themselves. You never type passwords or other credentials (a prohibited
   action), and you choose the most privacy-preserving consent option. Do this **before** recording
   so passwords and consent clicks never enter the footage. Screenshot to confirm the app is at the
   flow's starting state, then continue.

5. **Phase 1 — Record.** Branch on `ENGINE`:
   - **`chrome-gif`** — follow `references/recording-protocol.md`: `gif_creator{start_recording, tabId}`
     → immediately `computer{screenshot, tabId}` (first frame) → perform the shot list one step at a
     time with `computer` (click / type non-secret text / scroll / hover) + `navigate`, screenshotting
     between steps and inserting short `wait`s → final `computer{screenshot, tabId}` (last frame) →
     `gif_creator{stop_recording, tabId}`.
   - **`screen`** — follow `references/screen-record-protocol.md`: size + position the window and compute
     the crop, `screen_record.sh start <DISPLAY> {MP4_PATH} {FPS} {CRF} <crop>`, drive the same shot list
     with `computer`/`navigate` (short `wait`s between steps — you're recording real-time video, not
     discrete frames), then `screen_record.sh stop {MP4_PATH}` (SIGINT → finalized MP4). This writes
     `{MP4_PATH}` directly and prints its duration — **skip Phases 2–3**, go to Phase 4.

6. **Phase 2 — Export + relocate.** *(chrome-gif only — the `screen` engine already has `{MP4_PATH}`.)*
   Export with the overlay options mapped from `OVERLAYS`:
   `gif_creator{action:export, tabId, download:true, filename:"{CAPTURE_SLUG}.gif", options:{...}}`.
   The GIF lands in Chrome's download directory, so move it into place:
   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/skills/screencast-capture/scripts/find_download.sh "{CAPTURE_SLUG}*.gif" "{GIF_PATH}" "{DOWNLOAD_DIR}"
   ```
   If it can't find the file, ask the user where Chrome saved it and retry with the right `--download-dir`.

7. **Phase 3 — Convert to MP4.** *(chrome-gif only.)* Convert the GIF:
   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/skills/screencast-capture/scripts/gif_to_mp4.sh "{GIF_PATH}" "{MP4_PATH}" {FPS}
   ```
   The script prints the MP4's real duration. Keep it (both engines — the `screen` engine gets duration
   from `screen_record.sh stop`): it drives the reel interval,
   `INTERVAL = --interval value, else max(2, min(4, round(duration / 8)))`.

8. **Phase 4 — Hand off (or stop).** Present `{MP4_PATH}` to the user (via `present_files`), and report
   the duration, what was recorded, and where the GIF + MP4 live. Then, per `HANDOFF`:
   - `never` (`--no-reel`) → stop here; the MP4 is the deliverable.
   - `always` (`--reel`) or `ask` → if `ask`, use **AskUserQuestion** ("Turn this recording into a
     narrated highlight reel now?"). On yes, **hand off: invoke the `screencast-highlight-reel` skill**
     with a `$ARGUMENTS` string whose first token is the absolute MP4 path, per
     `references/convert-and-handoff.md`:
     ```
     '{MP4_PATH}' {CAPTURE_SLUG} {INTERVAL} [--no-tts] [--no-ground] --out {OUT_DIR}/reel
     ```
     The `[...]` flags are **conditional** — include a flag only when its condition holds, and drop the
     brackets (never forward a literal `[--no-tts]`): add `--no-tts` when there's no
     `ELEVENLABS_API_KEY` (else the reel attempts TTS and fails instead of rendering captions-only), and
     `--no-ground` when the recorded site is not the app in this repo. The reel runs its own
     confirm-before-render interview, so nothing renders without a second gate.

9. **Summary.** Report the MP4 path + duration, whether a reel was produced (and where), and the
   `OUT_DIR` layout. If a wiki vault exists, log the run per the wiki-first mandate.

## Error handling

- ffmpeg/ffprobe missing → halt before recording; tell the user to install ffmpeg (no converter, no MP4).
- Browser tool fails or the extension is unresponsive → retry the action ≤2–3× with a re-`screenshot`; if it still fails, **stop and report** what you attempted rather than looping (per the Chrome-automation guardrails). A recording left open can be closed with `gif_creator{action:clear}`.
- A native `alert/confirm/prompt` dialog appears → it freezes the extension; do not proceed. Warn the user they must dismiss it in the browser, then re-`tabs_context_mcp`.
- Export downloaded nothing / `find_download.sh` exits non-zero → ask the user for Chrome's download directory and retry; do not fabricate a GIF path.
- GIF→MP4 conversion fails → report the ffmpeg stderr and the input path; do not hand a broken/zero-byte MP4 to the reel.
- Login wall the user can't clear (SSO, MFA, CAPTCHA) → capture what's reachable or stop and report; never attempt to bypass bot-detection or enter credentials yourself.
- **`screen` engine** — capture hangs, or `screen_record.sh check`/`start` fails for permission → macOS Screen-Recording permission is not granted; relay the script's guidance and stop (you cannot grant it — a system security setting). Never stop a recording with `kill -9`/SIGKILL — always `screen_record.sh stop` (SIGINT), or the MP4 won't finalize.

## Important conventions

- Substitute every `{variable}` with its computed value before calling a tool or script.
- The **main agent** drives the browser — do not delegate recording to a subagent (the manual gate and the Phase 4 question need the user).
- `CAPTURE_SLUG` must be identical across the GIF, MP4, and `OUT_DIR` artifacts.
- Reuse the bundled scripts at `${CLAUDE_PLUGIN_ROOT}/skills/screencast-capture/scripts/`; the reel is a bundled sibling at `${CLAUDE_PLUGIN_ROOT}/skills/screencast-highlight-reel/` — hand off by invoking that skill, not by reimplementing any of it.
- Never type credentials, card numbers, or other secrets into a page — the user does that during the manual gate. Never bypass CAPTCHAs or bot-detection. Choose the most privacy-preserving consent option.
- Take a screenshot right after `start_recording` and right before `stop_recording` — those become the first and last frames.

## Reference files

- `references/recording-protocol.md` — the **`chrome-gif`** recording lifecycle: tool loading, the fresh tab, the manual-setup gate, the start→screenshot→act→screenshot→stop sequence, the `OVERLAYS`→`options` mapping, and browser/dialog/privacy handling.
- `references/screen-record-protocol.md` — the **`screen`** recording lifecycle: monitor selection + the permission check, window sizing + `--crop auto` rect computation, `screen_record.sh start/stop`, and clean finalize.
- `references/capture-interview.md` — Phase 0: the AskUserQuestion protocol that turns a loose request into a concrete shot list (`capture-plan.md`) — including the engine + (for `screen`) display/quality questions.
- `references/convert-and-handoff.md` — Phases 2–4: relocating the export, the GIF→MP4 conversion, computing the reel interval, and the ask-then-hand-off to `screencast-highlight-reel` (with passthrough-flag logic).
