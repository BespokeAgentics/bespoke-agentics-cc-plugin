# Phases 2–4 — Relocate, convert, hand off

> **Engine note:** the Phase 2–3 steps below are for the **`chrome-gif`** engine (a GIF in the download
> directory that must be relocated + converted). The **`screen`** engine already produced `{MP4_PATH}`
> in Phase 1 (see `screen-record-protocol.md`) — skip straight to **Phase 4**, using the duration that
> `screen_record.sh stop` printed for the interval below.

For `chrome-gif`, the recording exists as a GIF in Chrome's download directory. Three steps turn it
into a clean, reusable deliverable and (optionally) into a narrated reel.

## Phase 2 — Relocate the export

`gif_creator`'s `export {download:true}` wrote the file to `DOWNLOAD_DIR` (default `~/Downloads`),
possibly with a collision suffix like `{CAPTURE_SLUG} (1).gif`. Move the newest match into `OUT_DIR`:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/screencast-capture/scripts/find_download.sh \
  "{CAPTURE_SLUG}*.gif" "{GIF_PATH}" "{DOWNLOAD_DIR}"
```

It prints the destination on success. On exit 4 (no match), the browser may use a non-default
download folder — ask the user where Chrome saves downloads and retry with that `--download-dir`.
Don't invent a path.

## Phase 3 — Convert to MP4 (always)

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/screencast-capture/scripts/gif_to_mp4.sh \
  "{GIF_PATH}" "{MP4_PATH}" {FPS}
```

The script prints the MP4's **real duration in seconds** — capture it. This is the whole reason for
the conversion: a GIF has no container duration, so the reel would otherwise fall back to frame-index
timestamps; the MP4 is CFR, yuv420p, even-dimensioned H.264 that the reel can seek by time accurately.

Compute the interval you'll forward to the reel so even a short capture yields enough analysis frames:

```
INTERVAL = --interval value, else max(2, min(4, round(duration / 8)))
```

(e.g. a 35s capture → interval 4; a 12s capture → interval 2; capped at 4 so long clips aren't sampled
coarser than the reel's own default.) Confirm `{MP4_PATH}` is non-empty; if conversion failed, report
the ffmpeg error and stop — never hand a broken MP4 to the reel.

## Phase 4 — Present, then hand off (or stop)

Present `{MP4_PATH}` to the user with `present_files`, and report: duration, what was recorded, and
the `OUT_DIR` layout (GIF + MP4 + `capture-plan.md`).

Then branch on `HANDOFF`:

- **`never`** (`--no-reel`) — done. The MP4 (and GIF) are the deliverables.
- **`ask`** — ask once with **AskUserQuestion**: *"Turn this recording into a narrated highlight reel
  now?"* → *"Yes, make the reel"* · *"No, the MP4 is enough."* Proceed only on yes.
- **`always`** (`--reel`) — proceed straight to the handoff.

### The handoff

Hand off by **invoking the `screencast-highlight-reel` skill** (a bundled sibling) with a `$ARGUMENTS`
string whose **first token is the absolute MP4 path**. That skill's entire input contract is "a local,
time-seekable video path as positional-1," and it runs its own confirm-before-render interview — so
handing off does not render anything without a second gate.

```
'{MP4_PATH}' {CAPTURE_SLUG} {INTERVAL} [--no-tts] [--no-ground] --out {OUT_DIR}/reel
```

The `[...]` flags are **conditional** — forward each only when its rule holds, and drop the brackets
(never pass a literal `[--no-tts]`). Decide the passthrough flags:

- **`--no-tts`** — add it when there is **no `ELEVENLABS_API_KEY`** in the environment/`.env`. The reel
  then renders captions-only (no voiceover, no API key needed) instead of failing.
- **`--no-ground`** — add it when the **recorded site is not the app in this repo**. Grounding maps
  on-screen features to this codebase's `file:line`; if the recording is of some unrelated web app,
  grounding will find nothing and flag a mismatch, so skip it. If you *did* record this project's own
  app, leave grounding on — that's where the reel's narration gets its verified technical facts.

Do not pass `--audio` — both engines record **video only**, so the MP4 has no original audio track and
duck/keep/mute is a no-op; let the reel default it.

After the reel returns, report where its `.mp4` + `.srt` landed (under `{OUT_DIR}/reel/`). If a wiki
vault exists, log the capture (and reel, if produced) per the wiki-first mandate.
