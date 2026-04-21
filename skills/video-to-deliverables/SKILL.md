---
name: video-to-deliverables
description: "End-to-end video analysis pipeline that transforms any video recording into configurable deliverables. Supports workflow documentation, migration analysis, training extraction, meeting synthesis, skill-factory (video → installable Claude plugin), and custom deliverable profiles. Takes a video (local file OR YouTube URL), extracts frames, deduplicates, transcribes audio, runs parallel frame analysis, and synthesizes into user-selected deliverable types. Use this skill whenever a video recording needs to be turned into structured documentation, analysis, recommendations, or executable automation — regardless of domain."
---

<objective>
You are the Video-to-Deliverables Pipeline Orchestrator. You coordinate a full video analysis pipeline — from raw video to client-ready deliverables — by launching specialized agents at each phase.

This pipeline is domain-agnostic. It works for workflow analysis, platform migration assessment, training documentation, meeting synthesis, product demos, turning technical videos into installable plugins (`skill-factory` profile), or any video that needs to be systematically analyzed and turned into structured deliverables. The user selects which deliverable profile(s) to generate, and the pipeline adapts its Phase 2 analysis and final outputs accordingly.
</objective>

<arguments>

Parse these from `$ARGUMENTS`:

```
'<video-source>' '<project-name>' '<label>' [interval] [--profile <profile>] [--deliverables <list>] [--from-deliverables <dir>] [--skip-dedup] [--skip-transcribe] [--force]
```

- `video-source` (required unless `--from-deliverables`): Either a path to a local video file (MP4, MOV, etc.) OR a YouTube URL (`https://www.youtube.com/watch?v=...` or `https://youtu.be/...`). YouTube URLs are auto-downloaded via `yt-dlp` in pre-flight.
- `project-name` (required): Project, client, or subject name (e.g., `'Acme Corp'`, `'Q1 Training'`)
- `label` (required): Short label for this video (e.g., `'onboarding-walkthrough'`, `'sprint-demo'`)
- `interval` (optional): Frame extraction interval in seconds (default: `5`, or `3` when `--profile skill-factory`)
- `--profile <profile>` (optional): Deliverable profile to use (default: `workflow`)
  - `workflow` — Application inventory, workflow timeline, friction catalog, automation recommendations
  - `migration` — Feature inventory, platform assessment, gap analysis, UI mapping, integration assessment, data schema, validation, client elicitation
  - `meeting` — Action items, decisions, key topics, follow-up agenda
  - `training` — Step-by-step procedures, reference guide, knowledge base articles
  - `skill-factory` — Reverse-engineer a technical video into an installable Claude Code plugin (Skills + Commands + executable scripts + optional subagents). Interviews the user after content analysis to decide what to build.
  - `custom` — User defines deliverables via `--deliverables`
- `--deliverables <list>` (optional, requires `--profile custom`): Comma-separated deliverable types
- `--from-deliverables <dir>` (optional): Skip Phase 0 and Phase 1 entirely — reuse a prior run's outputs at `<dir>` (must contain `screen-catalog.md`, `component-library.md`, `system-architecture-map.md`, and a `../video-extraction/` with `manifest.json` + `transcript.txt`). Useful for iterating on Phase 2 without re-extracting.
- `--skip-dedup`: Skip frame deduplication
- `--skip-transcribe`: Skip audio transcription
- `--force`: Re-run all phases even if outputs exist

If `$ARGUMENTS` is empty or missing required arguments, print this usage guide and stop:

```
Usage: /bespoke-agentics:video-to-deliverables '<video-source>' '<project-name>' '<label>' [interval] [options]

Arguments:
  video-source     Path to local video file OR a YouTube URL
  project-name     Project or client name (quoted if spaces)
  label            Short identifier (e.g., 'onboarding-walkthrough')
  interval         Frame extraction interval in seconds (default: 5; 3 for skill-factory)

Options:
  --profile <name>          Deliverable profile: workflow | migration | meeting | training | skill-factory | custom (default: workflow)
  --deliverables <list>     Comma-separated deliverable types (requires --profile custom)
  --from-deliverables <dir> Reuse prior Phase 0/1 outputs at <dir>, skip extraction + analysis

Flags:
  --skip-dedup       Skip perceptual frame deduplication
  --skip-transcribe  Skip ElevenLabs audio transcription
  --force            Re-run all phases, ignoring existing outputs

Examples:
  /bespoke-agentics:video-to-deliverables './recording.mp4' 'Acme Corp' 'email-workflow' 5
  /bespoke-agentics:video-to-deliverables './demo.mp4' 'Boston Beer' 'vw-walkthrough' 5 --profile migration
  /bespoke-agentics:video-to-deliverables './standup.mp4' 'Team Alpha' 'sprint-review' 3 --profile meeting
  /bespoke-agentics:video-to-deliverables './training.mp4' 'New Hires' 'crm-setup' 5 --profile training
  /bespoke-agentics:video-to-deliverables './neo4j-tech-talk.mp4' 'Neo4j' 'graph-rag' 3 --profile skill-factory
  /bespoke-agentics:video-to-deliverables 'https://www.youtube.com/watch?v=abc123' 'Conf Talk' 'keynote' 5 --profile skill-factory
  /bespoke-agentics:video-to-deliverables '' 'Neo4j' 'graph-rag' --profile skill-factory --from-deliverables ./prior-run/deliverables
  /bespoke-agentics:video-to-deliverables './recording.mp4' 'Client X' 'process-audit' 5 --profile custom --deliverables 'app-inventory,workflow-timeline,executive-summary'
```
</arguments>

<derived_variables>

Compute these from the arguments and use them consistently throughout:

```
PROJECT_SLUG    = lowercase kebab-case of project-name (e.g., "acme-corp", "boston-beer")
LABEL           = label value (e.g., "email-workflow")
PROJECT_DIR     = current working directory
FRAMES_DIR      = {PROJECT_DIR}/video-extraction   (or parent of --from-deliverables target when in reuse mode)
DOCS_DIR        = {PROJECT_DIR}/deliverables       (or the --from-deliverables value itself when in reuse mode)
PROFILE         = selected profile (default: "workflow")
VIDEO_PATH      = the local file path to use downstream. If video-source is a YouTube URL, this becomes the downloaded file at {FRAMES_DIR}/source.mp4 after Pre-Flight step 7. If --from-deliverables is set, this is unused.
INTERVAL        = explicit interval argument, else 3 when PROFILE == skill-factory, else 5
```

If `--profile skill-factory` is chosen, ALSO set:
```
PLUGIN_SLUG     = populated during Phase 2 interview (Wave 2, Batch 1); default to {PROJECT_SLUG}-{LABEL} until the user chooses
PLUGIN_DIR      = {PROJECT_DIR}/generated-plugin-{PLUGIN_SLUG}
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

1. **Profile validation**: Confirm the `--profile` value is valid (one of `workflow`, `migration`, `meeting`, `training`, `skill-factory`, `custom`). If `custom`, confirm `--deliverables` is provided. If `skill-factory`, no extra required arg (identity is collected in Phase 2).

2. **Reuse-mode short-circuit**: If `--from-deliverables <dir>` is set, verify the directory exists and contains `screen-catalog.md`, `component-library.md`, `system-architecture-map.md`. Verify the sibling `../video-extraction/` has `manifest.json`. Set `DOCS_DIR = <dir>` and `FRAMES_DIR = <dir>/../video-extraction`. Skip steps 3-7 below and jump straight to Phase 2. (Phases 0 and 1 are considered "done".)

3. **Video source normalization**: Inspect `<video-source>`:
   - If it starts with `http://` or `https://` AND matches a YouTube host (`youtube.com`, `youtu.be`): treat as YouTube URL — continue to step 7 for download.
   - Otherwise: treat as a local path. Confirm the file exists. If not, abort with a clear error. Set `VIDEO_PATH = <video-source>`.

4. **ffmpeg installed**: Run `which ffmpeg`. If missing, abort with: "ffmpeg is required. Install with: `brew install ffmpeg`"

5. **ElevenLabs API key** (unless `--skip-transcribe`): Check for `ELEVENLABS_API_KEY` in environment or `.env`. If missing, warn and auto-enable `--skip-transcribe`.

6. **Create output directories**: Ensure `{FRAMES_DIR}` and `{DOCS_DIR}` exist.

7. **YouTube download** (only if step 3 identified a YouTube URL): Run the helper at `${CLAUDE_PLUGIN_ROOT}/skills/video-to-deliverables/scripts/fetch-youtube.sh "<video-source>" "{FRAMES_DIR}"`. On success, set `VIDEO_PATH = {FRAMES_DIR}/source.mp4`. The helper may also drop `{FRAMES_DIR}/auto-captions.vtt` — if present and `--skip-transcribe` is not set, use it as the transcript seed and still let the Phase 0 transcribe agent run to refine (or set `--skip-transcribe` if the user prefers to trust YouTube captions). If the helper fails, abort with the returned error.

8. **Smart Resume Scan** (unless `--force`): Check for existing outputs and report what will be skipped.

Print a pre-flight summary:

```
=== Video-to-Deliverables Pipeline ===
Project:        {project-name}
Label:          {label}
Profile:        {PROFILE}
Video source:   {original video-source}
Video path:     {VIDEO_PATH}  (downloaded if YouTube)
Frames:         {FRAMES_DIR}/
Deliverables:   {DOCS_DIR}/
Interval:       {INTERVAL}s
Skip Dedup:     {yes/no}
Skip Transcribe:{yes/no}
From Prior:     {--from-deliverables value or "no"}
Force:          {yes/no}

Pre-flight: ✓ Profile valid  ✓ Source resolved  ✓ ffmpeg  ✓ API key  ✓ Directories
```

If `--profile skill-factory`, also print: `  Plugin slug:    {PLUGIN_SLUG} (provisional — final value chosen in Phase 2)`.
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
- **Check**: The primary deliverable for the selected profile exists (see profile references for the primary deliverable filename). For `skill-factory`, this is `{PLUGIN_DIR}/plugin.json` — but note PLUGIN_SLUG isn't known until Phase 2 runs, so the check is "any directory matching `{PROJECT_DIR}/generated-plugin-*/plugin.json`". If one exists, describe it and ask the user whether to reuse or rebuild before auto-skipping.
- **Skip message**: "Phase 2: Skipping — {profile} deliverables already exist"

### Reuse Mode (`--from-deliverables`)
- **Check**: both `--from-deliverables` was set AND pre-flight step 2 validated it. Phases 0 and 1 are considered complete — do NOT re-run them, do NOT check their outputs again.

If ALL phases would be skipped, print the summary and exit:
```
All pipeline outputs already exist. Use --force to re-run.
```
</smart_resume>

<phase_0>
## Phase 0: Preprocessing

**Skip this entire phase** if `--from-deliverables` was provided (pre-flight step 2). In reuse mode, the manifest, frames, and transcript are considered already produced by the prior run.

### Step 1: Extract Frames (sequential — must complete first)

Run the frame extraction script against the resolved VIDEO_PATH (this is the local file whether the user passed a path or a YouTube URL that pre-flight downloaded):

```bash
${CLAUDE_PLUGIN_ROOT}/skills/extract-video-frames/scripts/extract-frames.sh "{VIDEO_PATH}" {INTERVAL} "{FRAMES_DIR}"
```

Verify outputs:
- `{FRAMES_DIR}/manifest.json` exists
- `{FRAMES_DIR}/frame_*.png` files exist
- `{FRAMES_DIR}/full_audio.aac` exists (if video has audio)

Report: "Extracted {N} frames at {INTERVAL}s intervals"

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

If `{FRAMES_DIR}/auto-captions.vtt` exists (YouTube auto-captions from the pre-flight fetcher), the transcribe agent should prefer ElevenLabs output for accuracy but merge the auto-captions' timestamps as a fallback grid. If the user explicitly passed `--skip-transcribe`, copy the VTT into `transcript.txt` (stripping VTT cue headers) so the pipeline still has a transcript to work with, and report "Using YouTube auto-captions as transcript".

```
Agent: "Transcribe video audio"
Prompt: |
  Transcribe the audio from the video recording.

  Run:
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{FRAMES_DIR}/full_audio.aac" --output "{FRAMES_DIR}/transcript.txt"

  If the command fails, try with the original video file:
  uv run ${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-transcribe/scripts/transcribe.py "{VIDEO_PATH}" --output "{FRAMES_DIR}/transcript.txt"

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

If `PROFILE == skill-factory`, the Phase 2 block should also list the generated plugin artifacts explicitly:
```
Phase 2 — skill-factory Deliverables
  ✓ {DOCS_DIR}/candidate-skills.md
  ✓ {DOCS_DIR}/extracted-artifacts.md
  ✓ {DOCS_DIR}/external-references.md
  ✓ {DOCS_DIR}/interview-answers.json
  ✓ {DOCS_DIR}/skill-factory-validation.md
  ✓ {PLUGIN_DIR}/plugin.json                  ← primary deliverable
  ✓ {PLUGIN_DIR}/README.md
  ✓ {PLUGIN_DIR}/skills/{name}/SKILL.md       (×N)
  ✓ {PLUGIN_DIR}/skills/{name}/scripts/       (×N when artifacts were promoted)
  ✓ {PLUGIN_DIR}/commands/{plugin}:*.md       (×N)
  ✓ {PLUGIN_DIR}/agents/*.md                  (when include_subagents)
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
