---
name: video-to-deliverables
description: "End-to-end video analysis pipeline that transforms any video recording into configurable deliverables. Supports workflow documentation, migration analysis, training extraction, meeting synthesis, and custom deliverable profiles. Takes a video, extracts frames, deduplicates, transcribes audio, runs parallel frame analysis, and synthesizes into user-selected deliverable types. Use this skill whenever a video recording needs to be turned into structured documentation, analysis, or recommendations — regardless of domain."
---

<objective>
You are the Video-to-Deliverables Pipeline Orchestrator. You coordinate a full video analysis pipeline — from raw video to client-ready deliverables — by launching specialized agents at each phase.

This pipeline is domain-agnostic. It works for workflow analysis, platform migration assessment, training documentation, meeting synthesis, product demos, or any video that needs to be systematically analyzed and turned into structured deliverables. The user selects which deliverable profile(s) to generate, and the pipeline adapts its Phase 2 analysis and final outputs accordingly.
</objective>

<arguments>

Parse these from `$ARGUMENTS`:

```
'<video-path>' '<project-name>' '<label>' [interval] [--profile <profile>] [--deliverables <list>] [--skip-dedup] [--skip-transcribe] [--force]
```

- `video-path` (required): Path to the video file (MP4, MOV, etc.)
- `project-name` (required): Project, client, or subject name (e.g., `'Acme Corp'`, `'Q1 Training'`)
- `label` (required): Short label for this video (e.g., `'onboarding-walkthrough'`, `'sprint-demo'`)
- `interval` (optional): Frame extraction interval in seconds (default: `5`)
- `--profile <profile>` (optional): Deliverable profile to use (default: `workflow`)
  - `workflow` — Application inventory, workflow timeline, friction catalog, automation recommendations
  - `migration` — Feature inventory, platform assessment, gap analysis, UI mapping, integration assessment, data schema, validation, client elicitation
  - `meeting` — Action items, decisions, key topics, follow-up agenda
  - `training` — Step-by-step procedures, reference guide, knowledge base articles
  - `custom` — User defines deliverables via `--deliverables`
- `--deliverables <list>` (optional, requires `--profile custom`): Comma-separated deliverable types
- `--skip-dedup`: Skip frame deduplication
- `--skip-transcribe`: Skip audio transcription
- `--force`: Re-run all phases even if outputs exist

If `$ARGUMENTS` is empty or missing required arguments, print this usage guide and stop:

```
Usage: /bespoke-agentics:video-to-deliverables '<video-path>' '<project-name>' '<label>' [interval] [options]

Arguments:
  video-path       Path to video file (MP4, MOV, etc.)
  project-name     Project or client name (quoted if spaces)
  label            Short identifier (e.g., 'onboarding-walkthrough')
  interval         Frame extraction interval in seconds (default: 5)

Options:
  --profile <name>       Deliverable profile: workflow | migration | meeting | training | custom (default: workflow)
  --deliverables <list>  Comma-separated deliverable types (requires --profile custom)

Flags:
  --skip-dedup       Skip perceptual frame deduplication
  --skip-transcribe  Skip ElevenLabs audio transcription
  --force            Re-run all phases, ignoring existing outputs

Examples:
  /bespoke-agentics:video-to-deliverables './recording.mp4' 'Acme Corp' 'email-workflow' 5
  /bespoke-agentics:video-to-deliverables './demo.mp4' 'Boston Beer' 'vw-walkthrough' 5 --profile migration
  /bespoke-agentics:video-to-deliverables './standup.mp4' 'Team Alpha' 'sprint-review' 3 --profile meeting
  /bespoke-agentics:video-to-deliverables './training.mp4' 'New Hires' 'crm-setup' 5 --profile training
  /bespoke-agentics:video-to-deliverables './recording.mp4' 'Client X' 'process-audit' 5 --profile custom --deliverables 'app-inventory,workflow-timeline,executive-summary'
```
</arguments>

<derived_variables>

Compute these from the arguments and use them consistently throughout:

```
PROJECT_SLUG    = lowercase kebab-case of project-name (e.g., "acme-corp", "boston-beer")
LABEL           = label value (e.g., "email-workflow")
PROJECT_DIR     = current working directory
FRAMES_DIR      = {PROJECT_DIR}/video-extraction
DOCS_DIR        = {PROJECT_DIR}/deliverables
PROFILE         = selected profile (default: "workflow")
```
</derived_variables>

<pipeline_architecture>

```
Phase 0: Preprocessing (extract -> dedup || transcribe)
    |
Phase 1: Parallel Frame Analysis (N chunks -> synthesis)
    |
Phase 2: Profile-Specific Analysis (varies by --profile)
    |
Summary
```

Phase 0 and Phase 1 are identical regardless of profile — they produce the universal intermediate artifacts (frames, transcript, screen catalog, component library, system architecture map). Phase 2 is where the pipeline branches based on the selected deliverable profile.
</pipeline_architecture>

<pre_flight_checks>

Before starting any phase, verify:

1. **Video file exists**: Confirm the video-path file is present. If not, abort with a clear error.

2. **ffmpeg installed**: Run `which ffmpeg`. If missing, abort with: "ffmpeg is required. Install with: `brew install ffmpeg`"

3. **ElevenLabs API key** (unless `--skip-transcribe`): Check for `ELEVENLABS_API_KEY` in environment or `.env`. If missing, warn and auto-enable `--skip-transcribe`.

4. **Create output directories**: Ensure `{FRAMES_DIR}` and `{DOCS_DIR}` exist.

5. **Profile validation**: Confirm the `--profile` value is valid. If `custom`, confirm `--deliverables` is provided.

6. **Smart Resume Scan** (unless `--force`): Check for existing outputs and report what will be skipped.

Print a pre-flight summary:

```
=== Video-to-Deliverables Pipeline ===
Project:     {project-name}
Label:       {label}
Profile:     {PROFILE}
Video:       {video-path}
Frames:      {FRAMES_DIR}/
Deliverables:{DOCS_DIR}/
Interval:    {interval}s
Skip Dedup:  {yes/no}
Skip Transcribe: {yes/no}
Force:       {yes/no}

Pre-flight: ✓ Video exists  ✓ ffmpeg  ✓ API key  ✓ Directories  ✓ Profile valid
```
</pre_flight_checks>

<smart_resume>

Before each phase, check if its outputs already exist. If they do (and `--force` is not set), skip that phase and report why.

### Phase 0 — Preprocessing
- **Check**: `{FRAMES_DIR}/manifest.json` exists AND has `dedup_applied: true` (or `--skip-dedup`)
- **Skip message**: "Phase 0: Skipping — manifest.json with {N} frames already exists"

### Phase 1 — Frame Analysis
- **Check**: All chunk analysis files AND synthesis files (`screen-catalog.md`, `component-library.md`, `system-architecture-map.md`) exist in `{DOCS_DIR}/`
- **Skip message**: "Phase 1: Skipping — all chunk analyses and synthesis files found"

### Phase 2 — Profile-Specific Analysis
- **Check**: The primary deliverable for the selected profile exists (see profile references for the primary deliverable filename)
- **Skip message**: "Phase 2: Skipping — {profile} deliverables already exist"

If ALL phases would be skipped, print the summary and exit:
```
All pipeline outputs already exist. Use --force to re-run.
```
</smart_resume>

<phase_0>
## Phase 0: Preprocessing

### Step 1: Extract Frames (sequential — must complete first)

Run the frame extraction script:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/extract-video-frames/scripts/extract-frames.sh "{video-path}" {interval} "{FRAMES_DIR}"
```

Verify outputs:
- `{FRAMES_DIR}/manifest.json` exists
- `{FRAMES_DIR}/frame_*.png` files exist
- `{FRAMES_DIR}/full_audio.aac` exists (if video has audio)

Report: "Extracted {N} frames at {interval}s intervals"

### Steps 2+3: Dedup and Transcribe (parallel)

Launch these in parallel using the Agent tool:

**Step 2 — Deduplicate Frames** (unless `--skip-dedup`):

```
Agent: "Deduplicate extracted frames"
Prompt: |
  Run the frame deduplication script on the extracted frames:

  python ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/scripts/dedupe-frames.py "{FRAMES_DIR}" --keep-originals

  Report the results: original frame count, kept frames, removed frames, reduction percentage.
  Read the updated manifest.json and confirm the dedup_applied field is true.
```

**Step 3 — Transcribe Audio** (unless `--skip-transcribe`):

```
Agent: "Transcribe video audio"
Prompt: |
  Transcribe the audio from the video recording.

  Run:
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{FRAMES_DIR}/full_audio.aac" --output "{FRAMES_DIR}/transcript.txt"

  If the command fails, try with the original video file:
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{video-path}" --output "{FRAMES_DIR}/transcript.txt"

  Report: success/failure and word count of transcript.
```

Wait for both to complete before proceeding.

Report: "Phase 0 complete. {N} unique frames, transcript: {word-count} words"
</phase_0>

<phase_1>
## Phase 1: Parallel Frame Analysis

This phase is identical for all profiles — it produces universal intermediate artifacts.

### Step 1: Compute Chunk Boundaries

Read `{FRAMES_DIR}/manifest.json`. Get the total frame count from the `frames` array (only entries not marked as removed/duplicate).

Compute chunks (target 5, adjust if fewer frames):
```
chunk_size = ceil(total_frames / 5)
Chunk 1: frames 1 through chunk_size
...
Chunk 5: frames chunk_size*4+1 through total_frames
```

If total frames < 10, use fewer chunks (minimum 1).

### Step 2: Launch Parallel Frame Analysts

Launch **N Agent instances simultaneously** using the Agent tool. Each agent:

```
Agent: "Frame analysis chunk {N}"
Prompt: |
  You are a Frame Analyst processing chunk {N} of {total_chunks} for the "{project-name}" project.

  Your task is to analyze video frames and identify every application, tool, screen, action, and notable content visible.

  Your assignment:
  - Frame range: {start} through {end}
  - Frames directory: {FRAMES_DIR}
  - Manifest: {FRAMES_DIR}/manifest.json
  - Transcript (if available): {FRAMES_DIR}/transcript.txt — use the portion covering timestamps for your frame range

  For each frame, use the Read tool to view the image and document:

  1. **Application identification**: What application, website, or tool is shown? (Name, version if visible)
  2. **Screen/view**: What specific screen, page, or view within the application?
  3. **Action being performed**: What is the user doing?
  4. **UI state indicators**: Counts, folder structures, tabs, notifications, loading states
  5. **Data visible**: Any visible data being worked with (anonymize sensitive content)
  6. **Integration clues**: Evidence of data moving between applications
  7. **Friction indicators**: Error messages, slow loads, excessive clicks, manual workarounds
  8. **Content/context**: Key information on screen relevant to the project

  If transcript is available, cross-reference what's being said at each timestamp with what's on screen.

  Save your output to: {DOCS_DIR}/frame-analysis-chunk-{N}.md

  Format each frame entry as:
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

### Step 3: Synthesize Frame Analyses

```
Agent: "Synthesize frame analyses"
Prompt: |
  You are synthesizing frame analysis chunks into universal intermediate artifacts for the "{project-name}" project ({label}).

  Read all frame analysis chunks:
  {list all DOCS_DIR/frame-analysis-chunk-*.md files}

  Also read the transcript if available: {FRAMES_DIR}/transcript.txt

  Produce THREE synthesis documents:

  1. **{DOCS_DIR}/screen-catalog.md** — Every unique screen/view identified:
     - Application name and type
     - Screen/view name and description
     - First and last seen timestamps
     - Total estimated screen time
     - Primary actions performed
     - Data types handled
     - Integration points with other tools

  2. **{DOCS_DIR}/component-library.md** — UI components, features, and capabilities observed:
     - Component/feature name
     - Which application it belongs to
     - Current behavior observed
     - User interaction patterns
     - Data it displays or processes

  3. **{DOCS_DIR}/system-architecture-map.md** — How all systems connect:
     - All applications/systems identified
     - Data flows between systems
     - Integration methods (manual, API, file transfer, etc.)
     - User roles and touchpoints
     - External dependencies

  Deduplicate across chunks — merge identical items into single entries with all timestamps.
```

Wait for synthesis to complete. Verify all 3 files exist.

Report: "Phase 1 complete. {N} screens cataloged, {N} components inventoried."
</phase_1>

<phase_2>
## Phase 2: Profile-Specific Analysis

This is where the pipeline branches. Read the appropriate profile reference file to get the specific agents, deliverables, and synthesis instructions for the selected profile.

**Before launching Phase 2**, read the profile reference:

```
${CLAUDE_PLUGIN_ROOT}/skills/video-to-deliverables/references/{PROFILE}-profile.md
```

The profile reference file contains:
1. The list of agents to launch (with wave dependencies)
2. The exact prompts for each agent
3. The deliverable filenames and formats
4. The final synthesis instructions
5. The primary deliverable filename (for smart resume checking)

Follow the profile reference instructions exactly, substituting all `{variables}` with computed values.

### Profile Execution Pattern

All profiles follow this general pattern, but the specific agents and deliverables vary:

```
Wave 1: Parallel independent analysis agents (all read from Phase 1 synthesis)
    ↓
Wave 2: Dependent agents (need Wave 1 outputs)
    ↓
Wave 3: Synthesis (needs all upstream outputs)
    ↓
Wave 4 (optional): Validation, export, supplementary deliverables
```

Some profiles (like `meeting`) are simpler and collapse into fewer waves. The profile reference file specifies the exact wave structure.

### Custom Profile

If `--profile custom` with `--deliverables`, construct a bespoke Phase 2 by selecting agent templates from the available deliverable types. Read `references/custom-profile.md` for the menu of available deliverable types and how to compose them.

After Phase 2 completes, report: "Phase 2 complete. {profile} deliverables generated."
</phase_2>

<pipeline_summary>

After all phases complete, print a summary table listing every generated file:

```
===============================================
  Video-to-Deliverables Complete
  Project: {project-name} | Label: {label}
  Profile: {PROFILE}
===============================================

Phase 0 — Preprocessing
  ✓ {FRAMES_DIR}/manifest.json                    ({N} unique frames)
  ✓ {FRAMES_DIR}/transcript.txt                   ({N} words)

Phase 1 — Frame Analysis
  ✓ {DOCS_DIR}/frame-analysis-chunk-*.md           ({N} chunks)
  ✓ {DOCS_DIR}/screen-catalog.md
  ✓ {DOCS_DIR}/component-library.md
  ✓ {DOCS_DIR}/system-architecture-map.md

Phase 2 — {PROFILE} Deliverables
  {list all profile-specific deliverables with status}

Total files generated: {N}
Primary deliverable: {primary deliverable path}
```

Status indicators:
- `✓` generated successfully
- `⊘` skipped (already existed)
- `✗` failed (with brief error reason)
</pipeline_summary>

<error_handling>
- If a subagent fails, log the error and continue with remaining pipeline steps where possible.
- If a **critical dependency** fails (e.g., frame extraction fails → can't do Phase 1), halt that branch and report what's blocked.
- Respect wave dependencies within Phase 2 — later waves can only run after their dependencies complete.
- Always produce whatever partial deliverables are possible and report the pipeline status.
- If transcription is unavailable, the pipeline still works — frame analysis alone provides significant value. Note the limitation in final deliverables.
</error_handling>

<important_notes>
- Use the `Agent` tool for all subagent launches. Each agent runs autonomously.
- Launch agents in parallel where the plan specifies parallel execution (use multiple Agent tool calls in a single response).
- Substitute all `{variables}` with their computed values before passing to agents.
- The `PROJECT_SLUG` must be consistent across ALL file names — double-check before each agent launch.
- Frame analyst agents must use the `Read` tool to visually inspect frame PNG files.
- The preprocessing skills (extract-video-frames, dedupe-frames, elevenlabs-transcribe) are bundled as sibling skills. Their scripts live at `${CLAUDE_PLUGIN_ROOT}/skills/{skill-name}/scripts/`.
</important_notes>
