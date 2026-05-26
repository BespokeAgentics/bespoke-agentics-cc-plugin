# Phase 1 — Parallel frame analysis

## Step 1 — Compute chunk boundaries

Read `{FRAMES_DIR}/manifest.json`. Total frame count = entries in `frames` not marked removed/duplicate.

```
chunk_size = ceil(total_frames / 5)
Chunk 1: frames 1 ... chunk_size
Chunk 2: frames chunk_size+1 ... chunk_size*2
...
Chunk 5: frames chunk_size*4+1 ... total_frames
```

If total frames < 10, use fewer chunks (minimum 1).

## Step 2 — Launch parallel frame analysts

Launch N Agent instances simultaneously (single response, multiple tool calls). Each analyst gets one chunk.

```
Agent: "Frame analysis chunk {N}"
Prompt: |
  You are a Workflow Frame Analyst processing chunk {N} of {total_chunks} for {client-name}.
  The goal is to identify every application, tool, screen, and action visible in the frames.

  Your assignment:
  - Frame range: {start} through {end}
  - Frames directory: {FRAMES_DIR}
  - Manifest: {FRAMES_DIR}/manifest.json
  - Transcript (if available): {FRAMES_DIR}/transcript.txt — use the portion covering your frame range

  For each frame use the Read tool to view the image and document:

  1. **Application identification** — Name (and version if visible).
  2. **Screen/view** — Specific screen, page, or view within the application.
  3. **Action being performed** — What the user is doing (composing email, searching, copying data, …).
  4. **UI state indicators** — Inbox counts, folder structures, tabs open, notifications, loading states.
  5. **Data visible** — Anonymize sensitive content; capture form fields, email subjects, contact names.
  6. **Integration clues** — Evidence of data moving between apps (copy-paste, manual entry, exports).
  7. **Friction indicators** — Errors, slow loads, excessive clicks, manual workarounds.

  If transcript is available, cross-reference what {client-name} is saying at each timestamp with what's on screen.

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
  - **Transcript context**: ... (if available)
```

Wait for ALL analysts to complete. Verify every `{DOCS_DIR}/frame-analysis-chunk-*.md` file exists.

## Step 3 — Synthesize frame analyses

```
Agent: "Synthesize frame analyses into workflow catalog"
Prompt: |
  You are synthesizing frame analysis chunks into a unified workflow catalog for {client-name}'s {workflow-label}.

  Read all frame analysis chunks:
  {list all DOCS_DIR/frame-analysis-chunk-*.md files}
  Also read the transcript if available: {FRAMES_DIR}/transcript.txt

  Produce THREE synthesis documents:

  1. **{DOCS_DIR}/application-inventory.md** — Every application/tool identified:
     - Name and type (email client, CRM, spreadsheet, browser, …)
     - First and last seen timestamps
     - Total estimated screen time
     - Primary actions performed in this application
     - Data types handled
     - How it connects to other applications in the workflow

  2. **{DOCS_DIR}/workflow-timeline.md** — Chronological workflow map:
     - Every step in sequence with timestamps
     - Application transitions
     - Data flow between applications
     - Decision points
     - Repetitive patterns (same sequence of actions repeated)

  3. **{DOCS_DIR}/friction-catalog.md** — Every friction point:
     - Explicit pain points with transcript quotes
     - Observed friction (excessive steps, manual data transfer, context switching)
     - Error states or failures observed
     - Time sinks (estimate per occurrence and frequency)
     - Workarounds observed

  Deduplicate across chunks: if the same application or pattern appears in multiple chunks, merge into a single entry with all timestamps.
```

Wait for synthesis to complete. Verify all 3 files exist.

Report: `Phase 1 complete. {N} applications cataloged, {N} workflow steps mapped, {N} friction points identified`.
