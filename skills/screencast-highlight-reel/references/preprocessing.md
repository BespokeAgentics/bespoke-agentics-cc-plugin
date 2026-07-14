# Phase 0 — Preprocessing

Identical machinery to the plugin's other video skills — **reuse the shared scripts, do not
reimplement**. The goal is a frame timeline plus a word-timed transcript so later phases can align
*what was on screen* to *what the presenter said*.

## Step 1 — Extract frames (sequential, must finish first)

```bash
${CLAUDE_PLUGIN_ROOT}/skills/extract-video-frames/scripts/extract-frames.sh "{VIDEO_PATH}" {INTERVAL} "{FRAMES_DIR}"
```

For a long demo, `INTERVAL=4` (the default) is a good balance — dense enough to catch transitions,
sparse enough to keep frame-analysis cheap. Bump to `2` for fast-moving demos, `6–8` for slow
talk-heavy ones.

Verify:
- `{FRAMES_DIR}/manifest.json` exists (each frame entry carries `timestamp_seconds` + a paired audio segment).
- `{FRAMES_DIR}/frame_*.png` exist.
- `{FRAMES_DIR}/full_audio.aac` exists (only if the source has audio — silent screencasts / GIFs won't).

Report: `Extracted {N} frames at {INTERVAL}s intervals from a {duration}s screencast`.

## Steps 2 + 3 — Dedup and transcribe (parallel)

Launch both via the Agent tool in a single response.

### Step 2 — Deduplicate frames (unless `--skip-dedup`)

```
Agent: "Deduplicate extracted frames"
Prompt: |
  python ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/scripts/dedupe-frames.py "{FRAMES_DIR}" --keep-originals
  Report: original count, kept, removed, reduction %. Confirm `dedup_applied: true` in manifest.json.
```

Demos deduplicate well (long static screens while the presenter talks). This shrinks Phase 1 work
without losing distinct moments.

### Step 3 — Transcribe narration with timestamps (unless `--skip-transcribe`)

The presenter's narration is the spine of the highlight story — it tells you which moments they
themselves thought were worth explaining. Capture **word-level** timestamps.

```
Agent: "Transcribe narration with timestamps"
Prompt: |
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{FRAMES_DIR}/full_audio.aac" --json --output "{ANALYSIS_DIR}/transcript.json"

  If that fails, retry on the original video:
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{VIDEO_PATH}" --json --output "{ANALYSIS_DIR}/transcript.json"

  If JSON still fails, fall back to a plain transcript:
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{FRAMES_DIR}/full_audio.aac" --output "{ANALYSIS_DIR}/transcript.txt"

  Report success/failure, output path, and approximate word count.
```

`transcript.json` holds a `words` array; each word carries text + a start time in seconds. Field
names may be `start`/`end` or `timestamp` depending on API version — inspect the structure, don't assume.

If the source has **no audio** (silent screencast), there is no narration to transcribe. Note it;
Phase 1 and Phase 3 will lean entirely on frame analysis + grounding, and the presenter's intent
will be recovered in the interview instead.

Wait for both to complete before Phase 1.

Report: `Phase 0 complete. {N} unique frames, transcript: {word-count} words` (or `no audio / transcription skipped`).
