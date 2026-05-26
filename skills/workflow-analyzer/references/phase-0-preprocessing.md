# Phase 0 — Preprocessing

Extract frames, then run dedup + transcription in parallel.

## Step 1 — Extract frames (sequential, must complete first)

```bash
${CLAUDE_PLUGIN_ROOT}/skills/extract-video-frames/scripts/extract-frames.sh "{video-path}" {interval} "{FRAMES_DIR}"
```

Verify outputs:
- `{FRAMES_DIR}/manifest.json` exists.
- `{FRAMES_DIR}/frame_*.png` files exist.
- `{FRAMES_DIR}/full_audio.aac` exists (only if the video has audio).

Report: `Extracted {N} frames at {interval}s intervals`.

## Steps 2 + 3 — Dedup and transcribe (parallel)

Launch both via the Agent tool in a single response (parallel).

### Step 2 — Deduplicate frames (unless `--skip-dedup`)

```
Agent: "Deduplicate extracted frames"
Prompt: |
  python ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/scripts/dedupe-frames.py "{FRAMES_DIR}" --keep-originals

  Report: original frame count, kept frames, removed frames, reduction percentage.
  Confirm `dedup_applied: true` in the updated manifest.json.
```

### Step 3 — Transcribe audio (unless `--skip-transcribe`)

```
Agent: "Transcribe video audio"
Prompt: |
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{FRAMES_DIR}/full_audio.aac" --output "{FRAMES_DIR}/transcript.txt"

  If that fails, retry with the original video:
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{video-path}" --output "{FRAMES_DIR}/transcript.txt"

  Report success/failure and transcript word count.
```

Wait for both to complete before Phase 1.

Report: `Phase 0 complete. {N} unique frames, transcript: {word-count} words`.
