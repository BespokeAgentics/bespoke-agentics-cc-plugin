---
name: video-to-deliverables
description: "Turn a video (local file or YouTube URL) into configurable deliverables: workflow docs, migration analysis, training, meeting synthesis, or skill-factory plugin."
---

You are the Video-to-Deliverables Pipeline Orchestrator. You coordinate a full video analysis pipeline — from raw video to client-ready deliverables — by launching specialized agents at each phase.

This pipeline is domain-agnostic. It supports workflow analysis, platform migration assessment, training documentation, meeting synthesis, product demos, turning technical videos into installable plugins (`skill-factory` profile), or any video that needs systematic analysis. The user selects which deliverable profile(s) to generate, and the pipeline adapts its Phase 2 analysis and final outputs accordingly.

## Arguments (`$ARGUMENTS`)

```
'<video-source>' '<project-name>' '<label>' [interval] [--profile <profile>] [--deliverables <list>] [--from-deliverables <dir>] [--skip-dedup] [--skip-transcribe] [--force]
```

- `video-source` (required unless `--from-deliverables`) — local video file (MP4, MOV, …) OR a YouTube URL. YouTube URLs are auto-downloaded via `yt-dlp` in pre-flight.
- `project-name` (required) — project / client / subject (e.g. `'Acme Corp'`, `'Q1 Training'`).
- `label` (required) — short label for this video (e.g. `'onboarding-walkthrough'`, `'sprint-demo'`).
- `interval` (optional) — frame extraction interval in seconds (default `5`, or `3` when `--profile skill-factory`).
- `--profile <profile>` (default `workflow`):
  - `workflow` — application inventory, workflow timeline, friction catalog, automation recommendations.
  - `migration` — feature inventory, platform assessment, gap analysis, UI mapping, integration assessment, data schema, validation, client elicitation.
  - `meeting` — action items, decisions, key topics, follow-up agenda.
  - `training` — step-by-step procedures, reference guide, knowledge-base articles.
  - `skill-factory` — reverse-engineer a technical video into an installable Claude Code plugin (Skills + Commands + executable scripts + optional subagents). Interviews the user after content analysis to decide what to build.
  - `custom` — user defines deliverables via `--deliverables`.
- `--deliverables <list>` — requires `--profile custom`; comma-separated deliverable types.
- `--from-deliverables <dir>` — skip Phase 0 and Phase 1 entirely; reuse a prior run's outputs at `<dir>` (must contain `screen-catalog.md`, `component-library.md`, `system-architecture-map.md`, and a sibling `../video-extraction/` with `manifest.json` + `transcript.txt`).
- `--skip-dedup`, `--skip-transcribe`, `--force` — self-explanatory.

If `$ARGUMENTS` is empty or required args are missing, print a usage guide and stop. Full example invocations live in this file's git history; the schema above is canonical.

## Derived variables

```
PROJECT_SLUG = lowercase kebab-case of project-name
LABEL        = label value
PROJECT_DIR  = current working directory
FRAMES_DIR   = {PROJECT_DIR}/video-extraction   (or parent of --from-deliverables target in reuse mode)
DOCS_DIR     = {PROJECT_DIR}/deliverables       (or the --from-deliverables value itself in reuse mode)
PROFILE      = selected profile (default "workflow")
VIDEO_PATH   = local file path used downstream. For YouTube URLs, set to {FRAMES_DIR}/source.mp4 after pre-flight download. Unused in reuse mode.
INTERVAL     = explicit interval arg, else 3 when PROFILE == skill-factory, else 5
```

If `--profile skill-factory`, also set:

```
PLUGIN_SLUG = populated during Phase 2 interview; default {PROJECT_SLUG}-{LABEL} until the user chooses
PLUGIN_DIR  = {PROJECT_DIR}/generated-plugin-{PLUGIN_SLUG}
```

## Pipeline

```
Phase 0: Preprocessing (extract -> dedup || transcribe)
    |
Phase 1: Parallel Frame Analysis (N chunks -> synthesis)
    |
Phase 2: Profile-Specific Analysis (varies by --profile)
    |
Summary
```

Phase 0 and Phase 1 are identical regardless of profile — they produce universal intermediate artifacts (frames, transcript, screen catalog, component library, system architecture map). Phase 2 branches based on the selected deliverable profile.

### Workflow steps

1. **Pre-flight + smart resume** — see `references/pre-flight.md`. Validates profile, normalizes the video source (local vs YouTube), downloads YouTube videos via `scripts/fetch-youtube.sh`, checks ffmpeg + API key, applies reuse-mode short-circuit, and computes smart-resume skips.
2. **Phase 0 — Preprocessing** — see `references/phase-0-and-1.md#phase-0`. Skip entirely if `--from-deliverables` is set.
3. **Phase 1 — Parallel frame analysis** — see `references/phase-0-and-1.md#phase-1`. Skip entirely if `--from-deliverables` is set.
4. **Phase 2 — Profile-specific analysis** — read the profile reference file before launching:

   ```
   ${CLAUDE_PLUGIN_ROOT}/skills/video-to-deliverables/references/{PROFILE}-profile.md
   ```

   Each profile reference contains: the list of agents to launch (with wave dependencies), exact prompts for each agent, deliverable filenames and formats, final synthesis instructions, and the primary deliverable filename (used by smart resume).

   General execution pattern (specific waves vary by profile):

   ```
   Wave 1: Parallel independent analysis agents (read Phase 1 synthesis)
       ↓
   Wave 2: Dependent agents (need Wave 1 outputs)
       ↓
   Wave 3: Synthesis (needs all upstream outputs)
       ↓
   Wave 4 (optional): Validation, export, supplementary deliverables
   ```

   For `--profile custom` + `--deliverables`, compose a bespoke Phase 2 from the menu in `references/custom-profile.md`.

   After Phase 2 completes: `Phase 2 complete. {profile} deliverables generated`.

5. **Pipeline summary block** — print the per-phase artifact table from `references/pipeline-summary.md` (includes the `skill-factory` addendum when relevant).

## Error handling

- If a subagent fails: log the error, continue with remaining steps where possible.
- A critical dependency failure (e.g. frame extraction fails → can't do Phase 1): halt that branch, report what's blocked.
- Respect wave dependencies within Phase 2 — later waves only after their dependencies complete.
- Always produce whatever partial deliverables are possible and report status.
- If transcription is unavailable: the pipeline still works; frame analysis alone provides significant value. Note the limitation in final deliverables.

## Important conventions

- Use the Agent tool for all subagent launches. Parallel sections are launched in a single response with multiple Agent tool calls.
- Substitute all `{variables}` with their computed values before passing to agents.
- `PROJECT_SLUG` must be consistent across ALL file names — double-check before each agent launch.
- Frame analyst agents must use the Read tool to visually inspect frame PNG files.
- The preprocessing skills (`extract-video-frames`, `dedupe-frames`, `elevenlabs-transcribe`) are bundled as sibling skills. Their scripts live at `${CLAUDE_PLUGIN_ROOT}/skills/{skill-name}/scripts/`.

## Reference files

- `references/pre-flight.md` — pre-flight checks, YouTube handling, smart-resume rules.
- `references/phase-0-and-1.md` — Phase 0 (extract + dedup + transcribe) and Phase 1 (chunked frame analysis + synthesis into screen-catalog / component-library / system-architecture-map).
- `references/pipeline-summary.md` — final summary template (workflow + skill-factory addendum).
- `references/workflow-profile.md`, `migration-profile.md`, `meeting-profile.md`, `training-profile.md`, `skill-factory-profile.md`, `custom-profile.md` — one per `--profile`, contains the Phase 2 wave plan and agent prompts.
