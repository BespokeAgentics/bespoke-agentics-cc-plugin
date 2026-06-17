# Phase 0 — Preprocessing

Extract frames, then run dedup + transcription in parallel. Identical machinery to the other
video skills — reuse the shared scripts, do not reimplement.

## Step 1 — Extract frames (sequential, must complete first)

```bash
${CLAUDE_PLUGIN_ROOT}/skills/extract-video-frames/scripts/extract-frames.sh "{video-path}" {interval} "{FRAMES_DIR}"
```

Verify outputs:
- `{FRAMES_DIR}/manifest.json` exists (each frame entry carries its timestamp in seconds + a paired
  audio segment path).
- `{FRAMES_DIR}/frame_*.png` files exist.
- `{FRAMES_DIR}/full_audio.aac` exists (only if the video has audio — `.gif` screencasts won't).

Report: `Extracted {N} frames at {interval}s intervals`.

## Steps 2 + 3 — Dedup and transcribe (parallel)

Launch both via the Agent tool in a single response.

### Step 2 — Deduplicate frames (unless `--skip-dedup`)

```
Agent: "Deduplicate extracted frames"
Prompt: |
  python ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/scripts/dedupe-frames.py "{FRAMES_DIR}" --keep-originals

  Report: original frame count, kept frames, removed frames, reduction percentage.
  Confirm `dedup_applied: true` in the updated manifest.json.
```

UI screencasts deduplicate aggressively (long still moments while the narrator talks). The default
threshold is fine; if the run keeps an implausibly high number of near-identical frames, a second
pass at `--threshold 10` is acceptable.

### Step 3 — Transcribe narration (unless `--skip-transcribe`)

The narration is half the signal — it tells you which component matters and why. Capture word-level
timestamps so Phase 1 can align "what was said" to "what was on screen".

```
Agent: "Transcribe narration with timestamps"
Prompt: |
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{FRAMES_DIR}/full_audio.aac" --json --output "{ANALYSIS_DIR}/transcript.json"

  If that fails, retry on the original video:
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{video-path}" --json --output "{ANALYSIS_DIR}/transcript.json"

  If JSON still fails, fall back to a plain transcript:
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{FRAMES_DIR}/full_audio.aac" --output "{ANALYSIS_DIR}/transcript.txt"

  Report success/failure, output path, and approximate word count.
```

`transcript.json` holds a `words` array; each word carries its text, a start time in seconds, and a
speaker id. Field names may be `start`/`end` or `timestamp` depending on the API version — Phase 1
agents should inspect the structure rather than assume.

Wait for both to complete before Phase 1.

Report: `Phase 0 complete. {N} unique frames, transcript: {word-count} words` (or `transcription skipped`).
