---
name: "bespokeagentics:highlight-reel"
description: "Turn a long app-demo screencast into a short, narrated, subtitled highlight video. Extracts frames + narration, grounds every feature shown in this repo's real source (file:line) so the voiceover is technically accurate, proposes the highlight moments, runs an AskUserQuestion interview to confirm the cut / duration / voice / audio, writes a narration script + subtitles, synthesizes a voiceover with ElevenLabs TTS, and renders the reel with ffmpeg. The creation companion to video-to-deliverables (docs) — this outputs a new .mp4. For .mp4/.mov/.webm/.gif demos of the app open in this session."
argument-hint: "'<video-path>' [reel-label] [interval] [--duration <sec>] [--voice <id>] [--audio duck|keep|mute] [--no-subs] [--no-ground] [--no-tts] [--out <dir>] [--skip-dedup] [--skip-transcribe] [--force]"
allowed-tools: Skill(screencast-highlight-reel), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Screencast → Highlight Reel

Run the `screencast-highlight-reel` skill: read a long app-demo screencast, ground what it
shows in this repo's source, interview the user to lock the cut, then write a narration +
render a short, narrated, subtitled highlight video.

## Arguments

Parse from `$ARGUMENTS`:

```
'<video-path>' [reel-label] [interval] [--duration <sec>] [--voice <id>] [--audio duck|keep|mute] [--no-subs] [--no-ground] [--no-tts] [--out <dir>] [--skip-dedup] [--skip-transcribe] [--force]
```

- `<video-path>` (required) — local screencast (`.mp4`, `.mov`, `.webm`, `.gif`).
- `reel-label` (optional) — output filename slug; else derived from the confirmed theme.
- `interval` (optional, default `4`) — seconds between extracted frames for analysis.
- `--duration <sec>` — target length of the finished reel (steers moment selection).
- `--voice <id>` — ElevenLabs `voice_id` for the voiceover (else env `ELEVENLABS_VOICE_ID`, else stock default).
- `--audio duck|keep|mute` (default `duck`) — how to treat the original screencast audio under the voiceover.
- `--no-subs` — don't burn subtitles (still writes the `.srt`).
- `--no-ground` — skip codebase grounding (narration will be less technically specific).
- `--no-tts` — captions-only render, no synthesized voiceover (no API key needed).
- `--out <dir>` (default `./highlight-reel`) — where deliverables are written.
- `--skip-dedup` / `--skip-transcribe` / `--force` — passthrough to preprocessing.

## Process

Invoke the `screencast-highlight-reel` skill and forward `$ARGUMENTS`. The skill will:

1. **Preprocess** — extract frames, dedup, transcribe the narration (word timestamps).
2. **Moment analysis** — parallel frame agents read frames + transcript → a salience-scored
   `moment-catalog.md` (what happens, when, which feature, how highlight-worthy).
3. **Ground** — parallel `Explore` agents map each demonstrated feature to real `file:line`
   → `feature-source-map.md`, so the voiceover can state verified facts (unless `--no-ground`).
4. **Propose + interview** — draft a ranked cut, then an AskUserQuestion gate confirms which
   moments, order, target length, tone/voice, and audio/caption treatment. Nothing renders first.
5. **Narrate** — write the grounded narration script + `reel-plan.json` (the edit-decision list).
6. **Voiceover** — `tts.py` synthesizes one clip per beat via ElevenLabs (unless `--no-tts`).
7. **Render** — `assemble_reel.py` cuts each moment, mixes the voiceover over the ducked/kept/muted
   original, freeze-extends any clip shorter than its narration, concatenates, and burns subtitles.

## Output

`{OUT_DIR}/<reel-slug>.mp4` (the narrated highlight reel) + `<reel-slug>.srt`, plus intermediate
artifacts under `{OUT_DIR}/` (`video-extraction/`, `analysis/` with the moment catalog, source map,
candidate highlights, interview answers, narration script; `voiceover/`; and `reel-plan.json`).
Because `reel-plan.json` is the single source of truth, edits (reword a beat, retime, reorder) are a
quick re-run — no re-analysis. Wiki-ingested when a vault exists.
