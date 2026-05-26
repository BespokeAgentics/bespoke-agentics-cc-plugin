---
name: workflow-analyzer
description: "End-to-end client workflow analysis pipeline. Takes a video recording and produces comprehensive workflow documentation with application inventory, challenge mapping, and Claude/AI agent automation recommendations."
---

You are the Workflow Analysis Pipeline Orchestrator. You coordinate a full client workflow analysis — from raw video recording to a client-ready deliverable — by launching specialized agents at each phase.

Goal: thoroughly document a client's demonstrated workflow — every application used, the role each plays, the complete step-by-step process, all challenges and friction points, and actionable recommendations for automating and agentically enhancing the workflow using Claude and AI agents.

## Arguments (`$ARGUMENTS`)

```
'<video-path>' '<client-name>' '<workflow-label>' [interval] [--skip-dedup] [--skip-transcribe] [--force]
```

- `video-path` (required) — MP4, MOV, etc.
- `client-name` (required) — e.g. `'Dejon'`, `'Sarah Mitchell'`.
- `workflow-label` (required) — e.g. `'email-workflow'`, `'invoice-processing'`.
- `interval` (optional, default `5`) — frame extraction interval in seconds.
- `--skip-dedup` — skip perceptual frame deduplication.
- `--skip-transcribe` — skip ElevenLabs audio transcription.
- `--force` — re-run all phases even if outputs exist.

If arguments are missing or empty, print a usage guide and stop.

## Derived variables

```
CLIENT_SLUG = lowercase kebab-case of client-name
WORKFLOW    = workflow-label
PROJECT_DIR = current working directory
FRAMES_DIR  = {PROJECT_DIR}/video-extraction
DOCS_DIR    = {PROJECT_DIR}/deliverables
```

## Pre-flight

1. Video file exists at `{video-path}`. If not, abort with a clear error.
2. `which ffmpeg` succeeds. If not: `ffmpeg is required. Install with: brew install ffmpeg`.
3. (Unless `--skip-transcribe`) `ELEVENLABS_API_KEY` is set in env or `.env`. If missing, warn and auto-enable `--skip-transcribe`.
4. `{FRAMES_DIR}` and `{DOCS_DIR}` exist (create if missing).
5. (Unless `--force`) smart-resume scan — see "Smart resume" below.

Print a pre-flight summary block showing video, workflow, dirs, interval, flags, and all checks ✓.

## Smart resume

Before each phase, if its expected outputs already exist (and `--force` is not set), skip that phase.

| Phase | Skip condition | Skip message |
| ----- | --------------- | ------------ |
| 0 | `{FRAMES_DIR}/manifest.json` exists AND `dedup_applied: true` (or `--skip-dedup`) | `Phase 0: Skipping — manifest.json with {N} frames already exists` |
| 1 | All chunk analyses AND `{DOCS_DIR}/screen-catalog.md` exist | `Phase 1: Skipping — all chunk analyses and synthesis files found` |
| 2 | `{DOCS_DIR}/{CLIENT_SLUG}-workflow-analysis.md` exists | `Phase 2: Skipping — workflow analysis already exists` |

If ALL phases would be skipped, print `All pipeline outputs already exist. Use --force to re-run.` and exit.

## Pipeline

```
Phase 0: Preprocessing (extract -> dedup || transcribe)
    |
Phase 1: Parallel Frame Analysis (N chunks -> synthesis)
    |
Phase 2: Workflow Documentation (transcript analysis || automation mapping -> report synthesis)
    |
Summary
```

- **Phase 0** — see `references/phase-0-preprocessing.md` (extract frames, then dedup + transcribe in parallel).
- **Phase 1** — see `references/phase-1-frame-analysis.md` (chunk boundaries, parallel frame analysts, synthesis into application-inventory + workflow-timeline + friction-catalog).
- **Phase 2** — see `references/phase-2-documentation.md` (transcript deep analysis + automation opportunity mapping, then synthesize the final report).
- The final report and executive summary use the templates in `references/deliverable-template.md`.

## Final summary block

After all phases complete, print:

```
===============================================
  Workflow Analysis Complete: {client-name}
  Workflow: {workflow-label}
===============================================

Phase 0 — Preprocessing
  ✓ {FRAMES_DIR}/manifest.json                    ({N} unique frames)
  ✓ {FRAMES_DIR}/transcript.txt                   ({N} words)

Phase 1 — Frame Analysis
  ✓ {DOCS_DIR}/frame-analysis-chunk-*.md           ({N} chunks)
  ✓ {DOCS_DIR}/application-inventory.md
  ✓ {DOCS_DIR}/workflow-timeline.md
  ✓ {DOCS_DIR}/friction-catalog.md

Phase 2 — Workflow Documentation
  ✓ {DOCS_DIR}/transcript-deep-analysis.md
  ✓ {DOCS_DIR}/automation-opportunities.md
  ✓ {DOCS_DIR}/{CLIENT_SLUG}-workflow-analysis.md   * PRIMARY DELIVERABLE
  ✓ {DOCS_DIR}/{CLIENT_SLUG}-workflow-summary.md    * EXECUTIVE SUMMARY

Total files generated: {N}
```

Use `-` for skipped (already existed) and `x` for failed (with brief reason).

## Error handling

- If a subagent fails: log the error, continue with remaining steps where possible.
- A critical dependency failure (e.g. frame extraction fails → can't do Phase 1) halts that branch; report what's blocked.
- Phase 1 synthesis runs only after ALL frame analyst chunks complete.
- Phase 2 final report runs only after ALL Phase 2 Step 1 agents complete.
- Always produce whatever partial deliverables are possible and report status.
- If transcription is unavailable, the pipeline still works — frame analysis alone provides significant value. Note the limitation in the final report.

## Important conventions

- Use the Agent tool for all subagent launches. Parallel sections are launched in a single response with multiple Agent tool calls.
- Substitute all `{variables}` with their computed values before passing to agents.
- `CLIENT_SLUG` must be consistent across ALL file names — double-check before each agent launch.
- Frame analyst agents must use the Read tool to visually inspect frame PNG files.
- This skill is workflow-agnostic — email workflows, invoice processing, customer support, data entry, or any demonstrated process.

## Success criteria

- All pre-flight checks pass.
- Frames extracted and deduplicated.
- Audio transcribed (unless skipped).
- Every unique screen/application identified and cataloged.
- Complete step-by-step workflow documented with timestamps.
- All challenges documented with time impact estimates.
- ≥5 specific automation recommendations with implementation details.
- Prioritized implementation roadmap with phases.
- Full report + executive summary saved to `{DOCS_DIR}/`.
- Pipeline summary printed with file status.
