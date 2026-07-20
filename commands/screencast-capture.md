---
name: "bespokeagentics:screencast-capture"
description: "Record a browser flow you describe as a screencast, agentically — with two capture engines. The agent drives a live Claude-in-Chrome session, opens a fresh tab and lets you log in first (credentials never hit the footage), records the described steps, produces an MP4, and asks whether to turn it into a narrated highlight reel. Default engine = gif_creator tab capture (zero-setup); --engine screen records a chosen monitor at native resolution + configurable bitrate via ffmpeg (needs macOS Screen-Recording permission). The capture companion to screencast-highlight-reel (that skill polishes a recording; this one produces one). For capturing a demo / screencast / GIF of the web app open in this session — including at higher quality / bitrate / on a specific monitor."
argument-hint: "['<start-url-or-flow>'] [capture-label] [--engine chrome-gif|screen] [--url <url>] [--out <dir>] [--fps <n>] [--overlays clean|clicks|full] [--display <idx>] [--crf <n>] [--crop auto|off|<W:H:X:Y>] [--reel] [--no-reel] [--interval <sec>] [--download-dir <dir>] [--tab <id>] [--force]"
allowed-tools: Skill(screencast-capture), Skill(screencast-highlight-reel), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep, ToolSearch, mcp__claude-in-chrome__tabs_context_mcp, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__computer, mcp__claude-in-chrome__read_page, mcp__claude-in-chrome__resize_window, mcp__claude-in-chrome__javascript_tool, mcp__claude-in-chrome__gif_creator, mcp__claude-in-chrome__read_console_messages
---

# Browser Session → Screencast (→ Reel)

Run the `screencast-capture` skill: drive a live Claude-in-Chrome session through a browser flow you
describe, record it (gif_creator tab capture by default, or `--engine screen` for a native-resolution
monitor recording), produce an MP4, and offer to hand it to `screencast-highlight-reel` for a narrated cut.

## Arguments

Parse from `$ARGUMENTS`:

```
['<start-url-or-flow>'] [capture-label] [--engine chrome-gif|screen] [--url <url>] [--out <dir>] [--fps <n>] [--overlays clean|clicks|full] [--display <idx>] [--crf <n>] [--crop auto|off|<W:H:X:Y>] [--reel] [--no-reel] [--interval <sec>] [--download-dir <dir>] [--tab <id>] [--force]
```

- `<start-url-or-flow>` (optional) — a starting URL, a one-line description of the flow, or both. Whatever's missing is elicited in the interview.
- `capture-label` (optional) — output filename slug; else derived from the confirmed intent.
- `--engine chrome-gif|screen` (default `chrome-gif`) — capture engine: `chrome-gif` records the tab (zero-setup, ~1200px, dithered GIF); `screen` records a chosen monitor at native resolution + bitrate via ffmpeg (needs macOS Screen-Recording permission).
- `--url <url>` — explicit starting URL (alternative to the positional).
- `--out <dir>` (default `./screencast-capture`) — where the recording, MP4, and artifacts are written.
- `--fps <n>` (default `12` gif / `30` screen) — capture / output frame rate.
- `--overlays clean|clicks|full` (default `clicks`) — **`chrome-gif` only:** `gif_creator` annotation; `clicks` shows only the orange click dots. (`screen` draws the real cursor + click flashes.)
- `--display <idx>` — **`screen` only:** monitor to record (avfoundation index; else identified in the interview).
- `--crf <n>` (default `18`) — **`screen` only:** H.264 quality (lower = better / larger file).
- `--crop auto|off|<W:H:X:Y>` (default `auto`) — **`screen` only:** crop to the browser window (`auto`), keep the whole monitor (`off`), or explicit pixels.
- `--reel` / `--no-reel` — hand off to the reel without asking / never hand off. Default: make the MP4, then ask.
- `--interval <sec>` — frame interval forwarded to the reel; default computed from the MP4 duration.
- `--download-dir <dir>` (default `~/Downloads`) — where Chrome saved the exported GIF.
- `--tab <id>` — reuse an existing tab instead of creating a fresh one.
- `--force` — overwrite existing outputs.

## Process

Invoke the `screencast-capture` skill and forward `$ARGUMENTS`. The skill will:

1. **Plan** — an AskUserQuestion interview turns the request into a concrete shot list (start URL, ordered steps, overlays, handoff) → `capture-plan.md`.
2. **Set up** — load the Claude-in-Chrome tools in one call, open a fresh tab, navigate, and **pause for you to log in / dismiss banners before recording** (so credentials stay out of the footage).
3. **Record** — `chrome-gif`: `start_recording` → screenshot → perform the flow step-by-step → screenshot → `stop_recording`, then export the GIF. `screen`: verify Screen-Recording permission, start `screen_record.sh` on the chosen monitor, drive the same flow, then stop — writing a native-resolution MP4 directly.
4. **Convert** — (`chrome-gif` only) relocate the GIF out of Downloads and convert it to a real-duration, time-seekable MP4 with ffmpeg. (`screen` already produced the MP4, so this is skipped.)
5. **Hand off** — present the MP4, then (per your choice) invoke `screencast-highlight-reel` on it with the right passthrough flags (`--no-tts` if no ElevenLabs key, `--no-ground` if the site isn't this repo's app). The reel runs its own confirm-before-render gate.

## Output

`{OUT_DIR}/<capture-slug>.mp4` (the recording, ready for the reel) + `<capture-slug>.gif` (the raw
export) + `capture-plan.md` (the shot list). If you continue into the reel, its narrated
`.mp4` + `.srt` land under `{OUT_DIR}/reel/`. Wiki-logged when a vault exists.
