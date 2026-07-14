# Phase 4–6 — Narration, Voiceover, Render

Everything up to here produced *decisions*. These phases produce the *deliverable*. The single
artifact that ties it together is `{OUT_DIR}/reel-plan.json` — the edit-decision list both scripts
consume.

## Phase 4 — Narration script + `reel-plan.json`

For each confirmed moment (from `interview-answers.md`), write a narration **beat**. Rules:

- **Concise**: ≈1–2 sentences, ideally ≤ ~30 spoken words (~8–12 seconds). Long beats force the
  renderer to freeze-extend the clip and produce wall-of-text captions.
- **Grounded**: a beat may state a *technical* fact ("all four panels come from one query") only if
  it traces to a high/medium-confidence row in `feature-source-map.md`. Otherwise describe what's
  visibly happening on screen. Never invent internals.
- **In the chosen tone** (from the interview).
- **Self-contained per moment**: the reel is cut, so a beat can't rely on a sentence from a moment
  that got dropped.
- **Trim the window** to the interesting part. The catalog window may include lead-in/lead-out dead
  time — tighten `in`/`out` to where the action is. Aim for the target length overall.

Then assemble `reel-plan.json`. **Schema** (consumed by `assemble_reel.py`):

```json
{
  "source": "/abs/path/to/{VIDEO_PATH}",
  "output": "{OUT_DIR}/{REEL_SLUG}.mp4",
  "resolution": "1920x1080",
  "fps": 30,
  "original_audio": "duck",
  "duck_db": -18,
  "voiceover_gain_db": 0,
  "tail_pad_seconds": 0.4,
  "subtitles": true,
  "segments": [
    {
      "id": "seg1",
      "in": 12.5,
      "out": 27.0,
      "narration": "The dashboard opens with every KPI already populated — one API call, no spinner.",
      "title": "Dashboard metrics"
    },
    {
      "id": "seg2",
      "in": 48.0,
      "out": 61.0,
      "narration": "Search is instant and fuzzy, matching across records as you type.",
      "title": "Global search"
    }
  ]
}
```

Field notes:
- `source` — absolute path to the ORIGINAL screencast (segments are cut from it, not from frames).
- `output` — final mp4 path; the `.srt` sidecar is written next to it automatically.
- `resolution` / `fps` — optional; omit to inherit the source. Set explicitly to standardize
  (e.g. force `1920x1080`). Odd dimensions are rounded up (libx264 requirement).
- `original_audio` — `duck` (lower under voiceover, default), `keep` (full), or `mute`. Mirror the
  interview answer / `--audio`.
- `subtitles` — `true` burns captions from the narration; the `.srt` is always written regardless.
- `segments[].id` — used to name the voiceover file (`{VOICE_DIR}/{id}.mp3`); keep them unique.
- `narration` — omit or leave `""` for a segment you want silent (kept as a visual beat, no caption).
- `voiceover` / `voiceover_seconds` — **you do not write these**; `tts.py` fills them in (Phase 5).
  In `--no-tts` mode they stay absent and the renderer just uses the original audio + burned captions.

Write the human-readable script alongside as `{ANALYSIS_DIR}/narration-script.md` (moment → beat →
grounding ref) so the user can review/edit the wording before rendering.

## Phase 5 — Voiceover (TTS) — skip if `--no-tts`

Requires `ELEVENLABS_API_KEY` in `.env` (same key the transcribe step used).

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/screencast-highlight-reel/scripts/tts.py \
  --plan {OUT_DIR}/reel-plan.json \
  --out-dir {VOICE_DIR} \
  --update-plan {OUT_DIR}/reel-plan.json \
  [--voice <voice_id>] [--model eleven_multilingual_v2]
```

- Synthesizes one mp3 per segment that has non-empty `narration` → `{VOICE_DIR}/{id}.mp3`.
- Folds `voiceover` (path) and `voiceover_seconds` (measured duration) back into each segment in
  `reel-plan.json`, so the renderer knows exactly how long each narration runs.
- `--voice` resolves from the flag, else env `ELEVENLABS_VOICE_ID`, else a stock default voice.
- Single-line mode also exists for spot regeneration:
  `uv run tts.py --text "..." --out {VOICE_DIR}/seg2.mp3 [--voice <id>]`.

If TTS fails or the key is missing: tell the user, drop to `--no-tts` semantics (captions-only), and
continue to render — a subtitled reel is still a useful deliverable.

## Phase 6 — Render

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/screencast-highlight-reel/scripts/assemble_reel.py {OUT_DIR}/reel-plan.json
```

What the renderer does per segment, then across the reel:
1. Cuts `[in, out]` from `source` (accurate seek).
2. Normalizes to uniform `resolution` / `fps` / SAR / `yuv420p` (letterboxes rather than stretches).
3. Builds audio: a silent bed + original audio (kept / ducked by `duck_db` / muted) + the voiceover,
   mixed with levels preserved (`amix … normalize=0`).
4. If a voiceover beat is **longer than its clip**, freezes the last frame (`tpad`) so narration is
   never cut off; `tail_pad_seconds` of quiet is held after the beat ends.
5. Concatenates all segments (concat demuxer — that's why step 2's normalization matters).
6. Writes `{REEL_SLUG}.srt` from the beat timings and, if `subtitles: true`, burns it in (libass).

Useful flags:
- `--check` — verify ffmpeg/ffprobe + required filters before a run (also used in pre-flight).
- `--srt-only` — regenerate just the subtitle file (fast; no re-render) after tweaking narration.

Output: `{OUT_DIR}/{REEL_SLUG}.mp4` + `{OUT_DIR}/{REEL_SLUG}.srt`. Present the mp4 to the user and
report length, moments included, and the artifact locations.

## Regeneration loop (cheap edits)

Because `reel-plan.json` is the single source of truth, iterating is cheap:
- Reword a beat → re-run `tts.py` for that one id (single-line mode) → re-render.
- Retime a moment → edit `in`/`out` → re-render.
- Reorder → reorder `segments[]` → re-render.
No re-analysis needed unless the user wants different moments (re-enter at Phase 3).
