---
name: workflow-analyzer
description: "End-to-end client workflow analysis pipeline. Takes a video recording and produces comprehensive workflow documentation with application inventory, challenge mapping, and Claude/AI agent automation recommendations."
---

<objective>
You are the Workflow Analysis Pipeline Orchestrator. You coordinate a full client workflow analysis — from raw video recording to a client-ready deliverable — by launching specialized agents at each phase.

The goal is to thoroughly document a client's demonstrated workflow: every application used, the role each plays, the complete step-by-step process, all challenges and friction points, and actionable recommendations for automating and agentically enhancing the workflow using Claude and AI agents.
</objective>

<arguments>

Parse these from `$ARGUMENTS`:

```
'<video-path>' '<client-name>' '<workflow-label>' [interval] [--skip-dedup] [--skip-transcribe] [--force]
```

- `video-path` (required): Path to the video file (MP4, MOV, etc.)
- `client-name` (required): Client's name (e.g., `'Dejon'`, `'Sarah Mitchell'`)
- `workflow-label` (required): Short label for the workflow (e.g., `'email-workflow'`, `'invoice-processing'`)
- `interval` (optional): Frame extraction interval in seconds (default: `5`)
- `--skip-dedup`: Skip frame deduplication
- `--skip-transcribe`: Skip audio transcription
- `--force`: Re-run all phases even if outputs exist

If `$ARGUMENTS` is empty or missing required arguments, print this usage guide and stop:

```
Usage: /bespoke-agentics:workflow-analyzer '<video-path>' '<client-name>' '<workflow-label>' [interval] [--skip-dedup] [--skip-transcribe] [--force]

Arguments:
  video-path       Path to video file (MP4, MOV, etc.)
  client-name      Client's name (quoted if spaces)
  workflow-label   Short workflow identifier (e.g., 'email-workflow')
  interval         Frame extraction interval in seconds (default: 5)

Flags:
  --skip-dedup       Skip perceptual frame deduplication
  --skip-transcribe  Skip ElevenLabs audio transcription
  --force            Re-run all phases, ignoring existing outputs

Example:
  /bespoke-agentics:workflow-analyzer './recording.mp4' 'Dejon' 'email-workflow' 5
```
</arguments>

<derived_variables>

Compute these from the arguments and use them consistently throughout:

```
CLIENT_SLUG     = lowercase kebab-case of client-name (e.g., "dejon", "sarah-mitchell")
WORKFLOW        = workflow-label value (e.g., "email-workflow")
PROJECT_DIR     = current working directory
FRAMES_DIR      = {PROJECT_DIR}/video-extraction
DOCS_DIR        = {PROJECT_DIR}/deliverables
```
</derived_variables>

<pipeline_architecture>

```
Phase 0: Preprocessing (extract -> dedup || transcribe)
    |
Phase 1: Parallel Frame Analysis (N chunks -> synthesis)
    |
Phase 2: Workflow Documentation (transcript analysis || application mapping -> report synthesis)
    |
Summary
```
</pipeline_architecture>

<pre_flight_checks>

Before starting any phase, verify:

1. **Video file exists**: Confirm the video-path file is present. If not, abort with a clear error.

2. **ffmpeg installed**: Run `which ffmpeg`. If missing, abort with: "ffmpeg is required. Install with: `brew install ffmpeg`"

3. **ElevenLabs API key** (unless `--skip-transcribe`): Check for `ELEVENLABS_API_KEY` in environment or `.env`. If missing, warn and auto-enable `--skip-transcribe`.

4. **Create output directories**: Ensure `{FRAMES_DIR}` and `{DOCS_DIR}` exist.

5. **Smart Resume Scan** (unless `--force`): Check for existing outputs and report what will be skipped.

Print a pre-flight summary:

```
=== Workflow Analysis Pipeline: {client-name} ===
Video:       {video-path}
Workflow:    {workflow-label}
Frames:      {FRAMES_DIR}/
Deliverables:{DOCS_DIR}/
Interval:    {interval}s
Skip Dedup:  {yes/no}
Skip Transcribe: {yes/no}
Force:       {yes/no}

Pre-flight: checkmark Video exists  checkmark ffmpeg  checkmark API key  checkmark Directories
```
</pre_flight_checks>

<smart_resume>

Before each phase, check if its outputs already exist. If they do (and `--force` is not set), skip that phase and report why.

### Phase 0 — Preprocessing
- **Check**: `{FRAMES_DIR}/manifest.json` exists AND has `dedup_applied: true` (or `--skip-dedup`)
- **Skip message**: "Phase 0: Skipping — manifest.json with {N} frames already exists"

### Phase 1 — Frame Analysis
- **Check**: All chunk analysis files AND `{DOCS_DIR}/screen-catalog.md` exist
- **Skip message**: "Phase 1: Skipping — all chunk analyses and synthesis files found"

### Phase 2 — Workflow Documentation
- **Check**: `{DOCS_DIR}/{CLIENT_SLUG}-workflow-analysis.md` exists
- **Skip message**: "Phase 2: Skipping — workflow analysis already exists"

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

### Step 1: Compute Chunk Boundaries

Read `{FRAMES_DIR}/manifest.json`. Get the total frame count from the `frames` array (only entries not marked as removed/duplicate).

Compute chunks (target 5, adjust if fewer frames):
```
chunk_size = ceil(total_frames / 5)
Chunk 1: frames 1 through chunk_size
Chunk 2: frames chunk_size+1 through chunk_size*2
...
Chunk 5: frames chunk_size*4+1 through total_frames
```

If total frames < 10, use fewer chunks (minimum 1).

### Step 2: Launch Parallel Frame Analysts

Launch **N Agent instances simultaneously** using the Agent tool. Each agent:

```
Agent: "Frame analysis chunk {N}"
Prompt: |
  You are a Workflow Frame Analyst processing chunk {N} of {total_chunks}.

  Your task is to analyze video frames from a client workflow recording for {client-name}.
  The goal is to identify every application, tool, screen, and action visible in the frames.

  Your assignment:
  - Frame range: {start} through {end}
  - Frames directory: {FRAMES_DIR}
  - Manifest: {FRAMES_DIR}/manifest.json
  - Transcript (if available): {FRAMES_DIR}/transcript.txt — use the portion covering timestamps for your frame range

  For each frame, use the Read tool to view the image and document:

  1. **Application identification**: What application or website is shown? (Name, version if visible)
  2. **Screen/view**: What specific screen, page, or view within the application?
  3. **Action being performed**: What is the user doing? (composing email, searching, copying data, etc.)
  4. **UI state indicators**: Inbox counts, folder structures, tabs open, notifications, loading states
  5. **Data visible**: Any visible data being worked with (email subjects, contact names, form fields — anonymize sensitive content)
  6. **Integration clues**: Evidence of data moving between applications (copy-paste, manual entry, exports)
  7. **Friction indicators**: Error messages, slow loads, excessive clicks, manual workarounds

  If transcript is available, cross-reference what {client-name} is saying at each timestamp with what's on screen.

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
  - **Transcript context**: ... (if available)
```

Wait for ALL agents to complete.

Verify: All `{DOCS_DIR}/frame-analysis-chunk-*.md` files exist.

### Step 3: Synthesize Frame Analyses

```
Agent: "Synthesize frame analyses into workflow catalog"
Prompt: |
  You are synthesizing frame analysis chunks into a unified workflow catalog for {client-name}'s {workflow-label}.

  Read all frame analysis chunks:
  {list all DOCS_DIR/frame-analysis-chunk-*.md files}

  Also read the transcript if available: {FRAMES_DIR}/transcript.txt

  Produce THREE synthesis documents:

  1. **{DOCS_DIR}/application-inventory.md** — Complete inventory of every application/tool identified:
     - Application name and type (email client, CRM, spreadsheet, browser, etc.)
     - First and last seen timestamps
     - Total estimated screen time
     - Primary actions performed in this application
     - Data types handled
     - How it connects to other applications in the workflow

  2. **{DOCS_DIR}/workflow-timeline.md** — Chronological workflow map:
     - Every step in sequence with timestamps
     - Application transitions (when {client-name} switches between tools)
     - Data flow between applications
     - Decision points
     - Repetitive patterns identified (same sequence of actions repeated)

  3. **{DOCS_DIR}/friction-catalog.md** — All friction points and challenges:
     - Explicitly mentioned pain points (with transcript quotes)
     - Observed friction (excessive steps, manual data transfer, context switching)
     - Error states or failures observed
     - Time sinks (estimated time per occurrence and frequency)
     - Workarounds observed

  Deduplicate across chunks — if the same application or pattern appears in multiple chunks, merge into a single entry with all timestamps.
```

Wait for synthesis to complete. Verify all 3 files exist.

Report: "Phase 1 complete. {N} applications cataloged, {N} workflow steps mapped, {N} friction points identified."
</phase_1>

<phase_2>
## Phase 2: Workflow Documentation & Automation Recommendations

### Step 1: Launch Parallel Analysis Agents

Launch **2 agents simultaneously**:

**Transcript Deep Analysis** (if transcript available):

```
Agent: "Deep transcript analysis for workflow insights"
Prompt: |
  Deeply analyze the transcript from {client-name}'s workflow recording.

  Read:
  - {FRAMES_DIR}/transcript.txt
  - {DOCS_DIR}/application-inventory.md (for context on what applications are discussed)

  Extract and document:

  1. **Explicit pain points**: Every frustration, complaint, or challenge {client-name} mentions.
     Quote them directly with timestamps.

  2. **Implicit needs**: Things {client-name} describes wanting or wishing for.
     Look for phrases like "I wish...", "It would be nice if...", "The problem is...", "This takes forever...", "I have to manually..."

  3. **Workflow rationale**: Why {client-name} does things in this particular order.
     Understanding the WHY behind each step is critical for automation recommendations.

  4. **Volume and frequency data**: Any mentions of how often tasks occur, how many emails/items are processed, peak times, etc.

  5. **People and roles**: Other people mentioned, their roles, what they need from {client-name}'s workflow.

  6. **Tool opinions**: Any preferences or frustrations with specific tools.

  Save to: {DOCS_DIR}/transcript-deep-analysis.md
```

**Automation Opportunity Mapping**:

```
Agent: "Map automation opportunities to AI agent capabilities"
Prompt: |
  You are an AI automation strategist. Analyze {client-name}'s workflow to identify every opportunity for Claude/AI agent automation.

  Read ALL of these:
  - {DOCS_DIR}/application-inventory.md
  - {DOCS_DIR}/workflow-timeline.md
  - {DOCS_DIR}/friction-catalog.md

  For each workflow step and friction point, assess:

  1. **Automation feasibility**: Can Claude or an AI agent handle this? (Full automation / Assisted automation / Human-in-the-loop / Not automatable)

  2. **Implementation approach**: What specific Claude/AI capability would be used?
     - Claude API for text processing, classification, drafting
     - Computer use for GUI automation
     - MCP servers for tool integration
     - Custom agents for multi-step workflows
     - Claude Code for developer workflow automation

  3. **Integration requirements**: What APIs, tools, or access would be needed?

  4. **Risk assessment**: What could go wrong? What guardrails are needed?

  5. **Impact estimate**: Time saved per occurrence x frequency = weekly/monthly impact

  Categorize all opportunities into:
  - **Quick Wins** (days to implement, high frequency tasks)
  - **Medium-Term** (weeks, requires integrations)
  - **Transformative** (months, end-to-end workflow redesign)

  Save to: {DOCS_DIR}/automation-opportunities.md
```

Wait for both agents to complete.

### Step 2: Synthesize Final Report

```
Agent: "Synthesize comprehensive workflow analysis report"
Prompt: |
  You are producing the final client deliverable for {client-name}'s workflow analysis.

  Read ALL upstream documents:
  - {DOCS_DIR}/application-inventory.md
  - {DOCS_DIR}/workflow-timeline.md
  - {DOCS_DIR}/friction-catalog.md
  - {DOCS_DIR}/transcript-deep-analysis.md (if available)
  - {DOCS_DIR}/automation-opportunities.md
  - {FRAMES_DIR}/transcript.txt (if available, for direct quotes)

  Produce TWO deliverables:

  ### Deliverable 1: Full Workflow Analysis Report
  Save to: {DOCS_DIR}/{CLIENT_SLUG}-workflow-analysis.md

  Structure:

  # {client-name} Workflow Analysis: {workflow-label}
  *Generated [current date]*

  ## Table of Contents

  ## 1. Executive Summary
  - Overview of the workflow analyzed
  - Key findings (3-5 bullet points)
  - Overall automation potential (High/Medium/Low with justification)
  - Estimated total time savings achievable

  ## 2. Applications & Tools Inventory
  For EVERY application identified, document in a structured table AND detailed descriptions:
  - Application name and type
  - Role in the workflow
  - How {client-name} uses it (specific actions observed)
  - Integration points with other tools
  - Estimated time spent
  - Frame references (timestamps)

  ## 3. Complete Workflow Map
  - Step-by-step sequence with timestamps
  - Decision points and branching logic
  - Data flow diagram (ASCII/text-based)
  - Manual transfer points between systems
  - Repetitive patterns with frequency estimates

  ## 4. Challenges & Pain Points
  ### 4.1 Explicitly Stated Challenges
  - Direct quotes from {client-name} with timestamps
  - Impact assessment for each

  ### 4.2 Observed Friction Points
  - Context switching overhead
  - Manual data transfer operations
  - Repetitive manual tasks
  - Error-prone steps
  - Waiting/loading time

  ### 4.3 Workflow Gaps
  - Missing integrations
  - Information silos
  - Lack of tracking/analytics
  - No standardized process documentation

  For each challenge: time impact (minutes per occurrence x frequency) and severity rating.

  ## 5. Automation & Agentic Enhancement Recommendations

  ### 5.1 Quick Wins (Implement within days)
  - Claude API-based solutions for text processing
  - Simple agent automations for repetitive tasks
  - Expected time savings per week

  ### 5.2 Medium-Term Improvements (Implement within weeks)
  - Custom Claude agent workflows
  - MCP server integrations for tool connectivity
  - AI-assisted decision making

  ### 5.3 Transformative Changes (Implement within months)
  - End-to-end agentic workflows
  - Custom AI agents for complete workflow segments
  - System architecture recommendations

  For EACH recommendation:
  - Problem it solves (reference Section 4)
  - How it works (specific Claude/AI capability)
  - Implementation approach (tools, APIs, integrations needed)
  - Expected impact (time saved, errors reduced)
  - Prerequisites and dependencies
  - Risk and guardrails needed

  ## 6. Prioritized Implementation Roadmap
  - Ordered by impact-to-effort ratio
  - Dependencies mapped
  - Suggested phases
  - Success metrics per phase
  - Estimated cumulative time savings at each phase

  ## 7. Appendix
  - Complete application inventory table
  - Full workflow timeline with frame references
  - Glossary of client-specific terms
  - Pipeline metadata (frames analyzed, transcript word count, video duration)

  ---

  ### Deliverable 2: Executive Summary
  Save to: {DOCS_DIR}/{CLIENT_SLUG}-workflow-summary.md

  A 1-2 page executive summary containing:
  - Who: {client-name} and their role context
  - What: The workflow analyzed
  - Key findings: Top 5 insights
  - Top 5 automation recommendations with expected impact
  - Recommended next steps
  - Suitable for sharing with stakeholders who won't read the full report
```

Wait for the synthesis agent to complete.

Verify both deliverables exist.

Report: "Phase 2 complete. Full workflow analysis and executive summary generated."
</phase_2>

<pipeline_summary>

After all phases complete, print a summary table:

```
===============================================
  Workflow Analysis Complete: {client-name}
  Workflow: {workflow-label}
===============================================

Phase 0 — Preprocessing
  [checkmark] {FRAMES_DIR}/manifest.json                    ({N} unique frames)
  [checkmark] {FRAMES_DIR}/transcript.txt                   ({N} words)

Phase 1 — Frame Analysis
  [checkmark] {DOCS_DIR}/frame-analysis-chunk-*.md           ({N} chunks)
  [checkmark] {DOCS_DIR}/application-inventory.md
  [checkmark] {DOCS_DIR}/workflow-timeline.md
  [checkmark] {DOCS_DIR}/friction-catalog.md

Phase 2 — Workflow Documentation
  [checkmark] {DOCS_DIR}/transcript-deep-analysis.md
  [checkmark] {DOCS_DIR}/automation-opportunities.md
  [checkmark] {DOCS_DIR}/{CLIENT_SLUG}-workflow-analysis.md   * PRIMARY DELIVERABLE
  [checkmark] {DOCS_DIR}/{CLIENT_SLUG}-workflow-summary.md    * EXECUTIVE SUMMARY

Total files generated: {N}
Primary deliverable: {DOCS_DIR}/{CLIENT_SLUG}-workflow-analysis.md
Executive summary:   {DOCS_DIR}/{CLIENT_SLUG}-workflow-summary.md
```

For any files that were skipped or failed, show the appropriate status:
- `[-]` for skipped (already existed)
- `[x]` for failed (with brief error reason)
</pipeline_summary>

<error_handling>
- If a subagent fails, log the error and continue with remaining pipeline steps where possible.
- If a **critical dependency** fails (e.g., frame extraction fails -> can't do Phase 1), halt that branch and report what's blocked.
- Phase 1 Step 3 (synthesis) can only run after ALL frame analyst chunks complete.
- Phase 2 Step 2 (final report) can only run after ALL Phase 2 Step 1 agents complete.
- Always produce whatever partial deliverables are possible and report the pipeline status.
- If transcription is unavailable, the pipeline should still work — frame analysis alone provides significant value. Note the limitation in the final report.
</error_handling>

<important_notes>
- Use the `Agent` tool for all subagent launches. Each agent runs autonomously.
- Launch agents in parallel where the plan specifies parallel execution (use multiple Agent tool calls in a single response).
- Substitute all `{variables}` with their computed values before passing to agents.
- The `CLIENT_SLUG` must be consistent across ALL file names — double-check before each agent launch.
- Frame analyst agents must use the `Read` tool to visually inspect frame PNG files.
- This command is workflow-agnostic — it works for email workflows, invoice processing, customer support, data entry, or any demonstrated process.
- Automation recommendations should focus on Claude and AI agent capabilities but can include other automation tools where appropriate.
</important_notes>

<success_criteria>
- All pre-flight checks pass
- Frames extracted and deduplicated
- Audio transcribed (unless skipped)
- Every unique screen/application identified and cataloged
- Complete step-by-step workflow documented with timestamps
- All challenges documented with time impact estimates
- Minimum 5 specific automation recommendations with implementation details
- Prioritized implementation roadmap with phases
- Full report and executive summary saved to {DOCS_DIR}/
- Pipeline summary printed with file status
</success_criteria>
