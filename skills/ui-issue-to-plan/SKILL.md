---
name: ui-issue-to-plan
description: "Turn a narrated screen recording of a UI issue into a grounded, code-aware implementation plan. Use this whenever someone hands you an .mp4/.mov/.webm/.gif screencast where they talk through a bug, glitch, layout problem, or a change/feature they want in the UI of the project open in THIS session — triggers on 'here's a video of the bug', 'I recorded the issue', 'screen recording of the broken dropdown', 'walkthrough of what I want to change', 'Loom of the problem', 'turn this video into a task/plan', or just an attached UI screencast plus 'fix this'. It extracts and reads the frames to identify the exact UI components being pointed at, transcribes the narration, maps the observed components to REAL source files in the current repo (file:line), runs an AskUserQuestion interview to pin down precisely what to fix/create/update, then writes an implementation plan to ./plans/. Distinct from video-to-deliverables/workflow-analyzer (which document a video in isolation) — this one is grounded in the session's actual codebase."
---

You are the UI-Issue-to-Plan Orchestrator. A user has recorded themselves narrating a problem
or desired change in the UI of the project that is **open in this session**. Your job is to turn
that screencast into a precise, code-grounded implementation plan: read the screens, transcribe
the narration, find the real source files behind what's on screen, interview the user to lock the
intent, and write the plan.

The thing that makes this skill valuable is **grounding**: the video is of *this* repo, so every
finding should point back to actual code (`file:line`) wherever possible — not generic advice.

## Arguments (`$ARGUMENTS`)

```
'<video-path>' [issue-label] [interval] [--out <dir>] [--no-ground] [--skip-dedup] [--skip-transcribe] [--force]
```

- `video-path` (required) — local screencast: `.mp4`, `.mov`, `.webm`, `.gif`.
- `issue-label` (optional) — short name for the issue, e.g. `'filter-dropdown-reset'`. Becomes the
  output filename slug. If omitted, derive a slug from the synthesized intent in Phase 4.
- `interval` (optional, default `2`) — seconds between extracted frames. UI changes are quick, so
  the default is denser than the generic video pipeline.
- `--out <dir>` (optional, default `./plans`) — where the final plan is written.
- `--no-ground` — skip Phase 2 (codebase grounding); produce the plan from video + narration only.
- `--skip-dedup` — skip perceptual frame deduplication.
- `--skip-transcribe` — skip ElevenLabs audio transcription.
- `--force` — re-run all phases even if outputs exist.

If `video-path` is missing or empty, print a short usage guide and stop.

## Derived variables

```
ISSUE_SLUG   = kebab-case of issue-label (else "" — derived in Phase 4 from the validated intent)
PROJECT_DIR  = current working directory (the repo to ground against)
WORK_DIR     = {PROJECT_DIR}/ui-issue-analysis
FRAMES_DIR   = {WORK_DIR}/frames
ANALYSIS_DIR = {WORK_DIR}/analysis
OUT_DIR      = value of --out, else {PROJECT_DIR}/plans
INTERVAL     = explicit arg, else 2
```

## Pre-flight

1. Video file exists at `{video-path}`. If not, abort with a clear error.
2. `which ffmpeg` succeeds. If not: `ffmpeg is required. Install with: brew install ffmpeg`.
3. (Unless `--skip-transcribe`) `ELEVENLABS_API_KEY` is set in env or `.env`. If missing, **warn,
   auto-enable `--skip-transcribe`, and continue** — frame analysis alone still works. Note that
   you will ask the user to describe the issue in chat during Phase 3 to compensate.
4. (Unless `--no-ground`) confirm `{PROJECT_DIR}` looks like a code repo to ground against — check
   for any of: `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `*.csproj`, `pom.xml`,
   `src/`, `app/`, `.git/`. If none are found, warn that grounding will be limited (the video may
   not be of the current repo) and ask the user to confirm before continuing.
5. Create `{WORK_DIR}`, `{FRAMES_DIR}`, `{ANALYSIS_DIR}`, `{OUT_DIR}` if missing.
6. (Unless `--force`) smart-resume scan — see "Smart resume".

Print a pre-flight summary block: video, issue label, dirs, interval, flags, repo-detected ✓/⚠, and all checks.

## Smart resume

Before each phase, if its expected outputs already exist (and `--force` is not set), skip that phase.

| Phase | Skip condition | Skip message |
| ----- | -------------- | ------------ |
| 0 | `{FRAMES_DIR}/manifest.json` exists AND `dedup_applied: true` (or `--skip-dedup`) | `Phase 0: Skipping — manifest.json with {N} frames already exists` |
| 1 | `{ANALYSIS_DIR}/observed-ui-map.md` AND `{ANALYSIS_DIR}/issue-summary.md` exist | `Phase 1: Skipping — observed UI map and issue summary found` |
| 2 | `{ANALYSIS_DIR}/component-source-map.md` exists (or `--no-ground`) | `Phase 2: Skipping — component-source map found` |

Phase 3 (interview) and Phase 4 (plan) are never auto-skipped — they are the point of the run. If
`{OUT_DIR}/{ISSUE_SLUG}.md` already exists and `--force` is not set, ask whether to overwrite.

## Pipeline

```
Phase 0: Preprocessing        (extract -> dedup || transcribe)
    |
Phase 1: UI + Narration       (N frame chunks -> observed-ui-map + issue-summary)
    |
Phase 2: Codebase Grounding   (observed UI -> real source files: component-source-map)
    |
Phase 3: Interview            (digest -> AskUserQuestion: confirm asks, clarify, ground, prioritize)
    |
Phase 4: Plan Synthesis       (validated state + template -> ./plans/{slug}.md)
    |
Summary
```

- **Phase 0** — `references/preprocessing.md` (extract frames, then dedup + transcribe in parallel).
- **Phase 1** — `references/frame-analysis.md` (chunk frames, launch parallel `ui-frame-analyst`
  agents, synthesize `observed-ui-map.md` + `issue-summary.md`).
- **Phase 2** — `references/codebase-grounding.md` (extract on-screen anchors, launch parallel
  `Explore` agents over the repo, synthesize `component-source-map.md`). Skip if `--no-ground`.
- **Phase 3** — `references/interview-protocol.md` (print the findings digest, then run the
  AskUserQuestion batches that elicit the clear vision of what to fix/create/update).
- **Phase 4** — `references/plan-synthesis.md` (assemble the plan from validated state using
  `assets/templates/implementation-plan.md`; wiki-ingest if a vault exists).

## Final summary block

After all phases complete, print:

```
===============================================
  UI Issue → Plan Complete
  Issue: {issue-label or derived slug}
===============================================

Phase 0 — Preprocessing
  ✓ {FRAMES_DIR}/manifest.json                      ({N} unique frames)
  ✓ {ANALYSIS_DIR}/transcript.json                  ({N} words)   [or: transcription skipped]

Phase 1 — UI + Narration Analysis
  ✓ {ANALYSIS_DIR}/observed-ui-map.md
  ✓ {ANALYSIS_DIR}/issue-summary.md                 ({N} candidate asks)

Phase 2 — Codebase Grounding
  ✓ {ANALYSIS_DIR}/component-source-map.md          ({N} components grounded, {N} unresolved)

Phase 3 — Interview
  ✓ {ANALYSIS_DIR}/interview-answers.md             ({N} asks confirmed)

Phase 4 — Plan
  ✓ {OUT_DIR}/{ISSUE_SLUG}.md                       * IMPLEMENTATION PLAN

Total files generated: {N}
```

Use `-` for skipped (already existed) and `x` for failed (with a brief reason).

## Error handling

- Use the Agent tool for all subagent launches. Parallel sections launch in a single response with
  multiple Agent tool calls.
- If frame extraction fails, Phase 1 cannot proceed — halt and report what's blocked.
- Phase 1 synthesis runs only after ALL frame-analyst chunks complete. Phase 2 synthesis runs only
  after ALL grounding agents complete.
- If transcription is unavailable, the pipeline still works — say so, and lean on the Phase 3
  interview to capture intent. Flag "narration not transcribed" in the final plan.
- If grounding resolves nothing (e.g. the video isn't of this repo), still produce a plan from the
  video + narration, and flag that source files are unconfirmed.
- Always produce whatever partial output is possible and report status.

## Important conventions

- Substitute all `{variables}` with computed values before passing to agents.
- `ISSUE_SLUG` must be consistent across all file names — fix it once (in Phase 4 if derived) and reuse.
- Frame-analyst agents MUST use the Read tool to visually inspect frame PNG files — they are reading
  pixels, not filenames.
- This skill is framework-agnostic (React, Svelte, Vue, Angular, server-rendered, native) — ground
  against whatever the repo actually is.
- The interview is mandatory and comes AFTER analysis + grounding, so questions are concrete ("I see
  you're pointing at the date-range picker in `Header.tsx:42` — fix its alignment, or change its
  reset behavior?") instead of open-ended.

## Success criteria

- Frames extracted, deduplicated, and (unless skipped) narration transcribed.
- Every UI component the narrator references is identified with its on-screen label and state.
- Observed components grounded to real source files (`file:line`) wherever the repo allows.
- The AskUserQuestion interview confirms each ask, resolves blocking ambiguities, and sets priority.
- A single implementation plan written to `{OUT_DIR}/{ISSUE_SLUG}.md` whose "Affected source files"
  point at real files, with a runnable verification section.
- If a `wiki/` vault exists, the plan is ingested and logged per the wiki-first mandate.
- Pipeline summary printed with file status.
