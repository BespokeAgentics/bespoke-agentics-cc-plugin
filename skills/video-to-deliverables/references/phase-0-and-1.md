# Phase 0 — Preprocessing and Phase 1 — Frame analysis

Both phases are profile-agnostic. Skip Phase 0 entirely if `--from-deliverables` was provided.

## Phase 0 — Preprocessing

### Step 1 — Extract frames (sequential, must complete first)

```bash
${CLAUDE_PLUGIN_ROOT}/skills/extract-video-frames/scripts/extract-frames.sh "{VIDEO_PATH}" {INTERVAL} "{FRAMES_DIR}"
```

Verify outputs:
- `{FRAMES_DIR}/manifest.json` exists.
- `{FRAMES_DIR}/frame_*.png` files exist.
- `{FRAMES_DIR}/full_audio.aac` exists (only if the video has audio).

Report: `Extracted {N} frames at {INTERVAL}s intervals`.

### Steps 2 + 3 — Dedup and transcribe (parallel)

Launch both in a single Agent-tool response.

**Step 2 — Deduplicate frames** (unless `--skip-dedup`):

```
Agent: "Deduplicate extracted frames"
Prompt: |
  python ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/scripts/dedupe-frames.py "{FRAMES_DIR}" --keep-originals

  Report: original frame count, kept frames, removed frames, reduction percentage.
  Confirm `dedup_applied: true` in the updated manifest.json.
```

**Step 3 — Transcribe audio** (unless `--skip-transcribe`):

If `{FRAMES_DIR}/auto-captions.vtt` exists (YouTube auto-captions from pre-flight), prefer the ElevenLabs result for accuracy but merge the VTT cue timestamps as a fallback grid. If the user explicitly passed `--skip-transcribe`, copy the VTT into `transcript.txt` (stripping VTT headers) so the pipeline still has a transcript to work with, and report `Using YouTube auto-captions as transcript`.

```
Agent: "Transcribe video audio"
Prompt: |
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{FRAMES_DIR}/full_audio.aac" --output "{FRAMES_DIR}/transcript.txt"

  If that fails, retry with the source video:
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{VIDEO_PATH}" --output "{FRAMES_DIR}/transcript.txt"

  Report success/failure and transcript word count.
```

Wait for both to complete.

Report: `Phase 0 complete. {N} unique frames, transcript: {word-count} words`.

## Phase 1 — Parallel frame analysis

Identical for all profiles — produces the three universal intermediate artifacts.

### Step 1 — Compute chunk boundaries

Read `{FRAMES_DIR}/manifest.json`. Total frame count = entries in `frames` not marked removed/duplicate.

```
chunk_size = ceil(total_frames / 5)
Chunk 1: frames 1 ... chunk_size
...
Chunk 5: frames chunk_size*4+1 ... total_frames
```

If total frames < 10, use fewer chunks (minimum 1).

### Step 2 — Launch parallel frame analysts

Launch N Agent instances simultaneously (single response, multiple tool calls).

```
Agent: "Frame analysis chunk {N}"
Prompt: |
  You are a Frame Analyst processing chunk {N} of {total_chunks} for the "{project-name}" project.

  Your task: identify every application, tool, screen, action, and notable content visible.

  Your assignment:
  - Frame range: {start} through {end}
  - Frames directory: {FRAMES_DIR}
  - Manifest: {FRAMES_DIR}/manifest.json
  - Transcript (if available): {FRAMES_DIR}/transcript.txt — use the portion covering your frame range

  For each frame use the Read tool to view the image and document:

  1. **Application identification** — Name (and version if visible).
  2. **Screen/view** — Specific screen, page, or view.
  3. **Action being performed** — What is the user doing?
  4. **UI state indicators** — Counts, folder structures, tabs, notifications, loading states.
  5. **Data visible** — Anonymize sensitive content.
  6. **Integration clues** — Evidence of data moving between applications.
  7. **Friction indicators** — Error messages, slow loads, excessive clicks, manual workarounds.
  8. **Content / context** — Key information on screen relevant to the project.

  If transcript is available, cross-reference what's being said at each timestamp with what's on screen.

  Save output to: {DOCS_DIR}/frame-analysis-chunk-{N}.md

  Per-frame entry format:
  ## Frame {number} — {timestamp}
  - **Application**: ...
  - **Screen**: ...
  - **Action**: ...
  - **State**: ...
  - **Data**: ...
  - **Integration clues**: ...
  - **Friction**: ...
  - **Content/context**: ...
  - **Transcript context**: ... (if available)
```

Wait for ALL agents to complete.

### Step 3 — Synthesize frame analyses

```
Agent: "Synthesize frame analyses"
Prompt: |
  You are synthesizing frame analysis chunks into universal intermediate artifacts for the "{project-name}" project ({label}).

  Read all frame analysis chunks:
  {list all DOCS_DIR/frame-analysis-chunk-*.md files}
  Also read the transcript if available: {FRAMES_DIR}/transcript.txt

  Produce THREE synthesis documents:

  1. **{DOCS_DIR}/screen-catalog.md** — every unique screen/view identified:
     - Application name and type
     - Screen/view name and description
     - First and last seen timestamps
     - Total estimated screen time
     - Primary actions performed
     - Data types handled
     - Integration points with other tools

  2. **{DOCS_DIR}/component-library.md** — UI components, features, capabilities observed:
     - Component / feature name
     - Which application it belongs to
     - Current behavior observed
     - User interaction patterns
     - Data it displays or processes

  3. **{DOCS_DIR}/system-architecture-map.md** — how all systems connect:
     - All applications / systems identified
     - Data flows between systems
     - Integration methods (manual, API, file transfer, …)
     - User roles and touchpoints
     - External dependencies

  Deduplicate across chunks — merge identical items into single entries with all timestamps.
```

Wait for synthesis to complete. Verify all 3 files exist.

Report: `Phase 1 complete. {N} screens cataloged, {N} components inventoried`.
