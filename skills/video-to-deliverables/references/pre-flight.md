# Pre-flight + smart resume

Before launching any phase, complete every check below. Print the pre-flight summary at the end.

## Checks

1. **Profile validation** — confirm `--profile` is one of `workflow`, `migration`, `meeting`, `training`, `skill-factory`, `custom`. If `custom`, confirm `--deliverables` is provided. If `skill-factory`, no extra required arg here — plugin identity is collected in Phase 2.

2. **Reuse-mode short-circuit** — if `--from-deliverables <dir>` is set:
   - Verify `<dir>` exists and contains `screen-catalog.md`, `component-library.md`, `system-architecture-map.md`.
   - Verify sibling `../video-extraction/` has `manifest.json`.
   - Set `DOCS_DIR = <dir>` and `FRAMES_DIR = <dir>/../video-extraction`.
   - Skip steps 3-7 below; jump straight to Phase 2. Phases 0 and 1 are considered "done".

3. **Video source normalization** — inspect `<video-source>`:
   - If `http://` or `https://` AND host matches `youtube.com` or `youtu.be`: treat as YouTube URL — continue to step 7 for download.
   - Otherwise: local path. Confirm the file exists. Set `VIDEO_PATH = <video-source>`. Abort with a clear error if missing.

4. **ffmpeg installed** — `which ffmpeg`. If missing: `ffmpeg is required. Install with: brew install ffmpeg`.

5. **ElevenLabs API key** — unless `--skip-transcribe`, check `ELEVENLABS_API_KEY` in env or `.env`. If missing, warn and auto-enable `--skip-transcribe`.

6. **Create output directories** — ensure `{FRAMES_DIR}` and `{DOCS_DIR}` exist.

7. **YouTube download** — only if step 3 identified a YouTube URL:

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/video-to-deliverables/scripts/fetch-youtube.sh "<video-source>" "{FRAMES_DIR}"
   ```

   On success: set `VIDEO_PATH = {FRAMES_DIR}/source.mp4`. The helper may also drop `{FRAMES_DIR}/auto-captions.vtt` — if present and `--skip-transcribe` is not set, use it as the transcript seed and still let the Phase 0 transcribe agent run to refine. If the user prefers to trust YouTube captions, set `--skip-transcribe`. On failure: abort with the returned error.

8. **Smart resume scan** — unless `--force`, check existing outputs and report what will be skipped (see "Smart resume" below).

## Pre-flight summary block

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

If `--profile skill-factory`, also print:

```
  Plugin slug:    {PLUGIN_SLUG} (provisional — final value chosen in Phase 2)
```

## Smart resume

Before each phase, check if its outputs already exist. If they do (and `--force` is not set), skip that phase and report why.

### Phase 0

- Check: `{FRAMES_DIR}/manifest.json` exists AND `dedup_applied: true` (or `--skip-dedup`).
- Skip message: `Phase 0: Skipping — manifest.json with {N} frames already exists`.

### Phase 1

- Check: all chunk analysis files AND synthesis files (`screen-catalog.md`, `component-library.md`, `system-architecture-map.md`) exist in `{DOCS_DIR}/`.
- Skip message: `Phase 1: Skipping — all chunk analyses and synthesis files found`.

### Phase 2

- Check: the primary deliverable for the selected profile exists (the per-profile reference file names this). For `skill-factory`, this is `{PLUGIN_DIR}/plugin.json` — but `PLUGIN_SLUG` isn't known until Phase 2 runs, so the check is "any directory matching `{PROJECT_DIR}/generated-plugin-*/plugin.json`". If one exists, describe it and ask the user whether to reuse or rebuild before auto-skipping.
- Skip message: `Phase 2: Skipping — {profile} deliverables already exist`.

### Reuse mode (`--from-deliverables`)

- Check: `--from-deliverables` was set AND pre-flight step 2 validated it. Phases 0 and 1 are considered complete — do NOT re-run, do NOT check outputs again.

If ALL phases would be skipped, print the summary and exit:

```
All pipeline outputs already exist. Use --force to re-run.
```
