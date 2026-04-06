---
name: dedupe-frames
description: "Remove near-duplicate frames from a video extraction directory using perceptual hashing (dhash). Runs after frame extraction and before frame analysis to reduce context window usage by eliminating visually identical frames. Typically removes 50-80% of frames from meeting recordings where the same screen is visible for extended periods."
args:
  - name: frames-dir
    description: "Path to the directory containing extracted frames and manifest.json (e.g., screencast/platform-overview-frames/)"
    required: true
  - name: threshold
    description: "Maximum Hamming distance between frame hashes to consider them duplicates. Default: 6. Lower = stricter (2 = near-exact only). Higher = more aggressive (10+ = catches moderate changes)."
    required: false
  - name: dry-run
    description: "If true, reports what would be removed without modifying any files. Use this first to calibrate the threshold."
    required: false
---

You are the Frame Deduplication agent. Your job is to eliminate near-duplicate frames from a video extraction before the frame analysis agents process them. This is a critical optimization step — meeting recordings typically contain 50-80% redundant frames (same screen, slight mouse movement, no meaningful change), and removing them prevents frame analysis agents from exhausting their context window on repetitive content.

## Primary Objective

Take a directory of extracted video frames (produced by the `extract-video-frames` skill) and remove frames that are visually identical or near-identical to their predecessor. Preserve the first frame of every distinct screen or view change. Update the manifest so downstream agents only process unique frames.

## How It Works

The script uses **dhash (difference hash)** — a perceptual hashing algorithm that:

1. Downscales each frame to a small grayscale image
2. Computes hash bits by comparing adjacent pixel brightness
3. Produces a fixed-size fingerprint (default: 512 bits) that represents the image's visual structure
4. Compares consecutive frames by **Hamming distance** (count of differing bits)

If two consecutive frames have a Hamming distance ≤ threshold, they look essentially the same and the later frame is dropped. When the distance exceeds the threshold, a meaningful visual change occurred (screen transition, new panel, scroll) and the frame is kept.

### Why dhash?

- **Deterministic** — same input always produces same output, no ML model or randomness
- **Fast** — processes 200+ frames in under a second
- **Robust** — handles minor compression artifacts, slight color shifts, cursor movement
- **Well-tested** — proven at scale across 200,000+ images in production systems

## Prerequisites

```bash
pip install imagehash Pillow --break-system-packages
```

## Usage

### Basic (recommended for meeting recordings)

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/scripts/dedupe-frames.py screencast/{meeting-name}-frames/
```

This uses the default threshold of 6, which works well for typical meeting recordings where you want to catch same-screen frames but preserve any meaningful screen change.

### Dry run first (see what would be removed)

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/scripts/dedupe-frames.py screencast/{meeting-name}-frames/ --dry-run
```

### Conservative (only remove near-exact duplicates)

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/scripts/dedupe-frames.py screencast/{meeting-name}-frames/ --threshold 2
```

### Aggressive (catch even moderate changes like scrolls within the same page)

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/scripts/dedupe-frames.py screencast/{meeting-name}-frames/ --threshold 10
```

### Keep originals (move dupes to .dupes/ instead of deleting)

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/scripts/dedupe-frames.py screencast/{meeting-name}-frames/ --keep-originals
```

## Threshold Tuning Guide

The threshold controls how aggressively duplicates are detected. Hamming distance is the number of differing bits between two frame hashes.

| Threshold | Behavior | Best For |
|---|---|---|
| 2 | Near-exact only. Catches identical frames with minor compression differences. | When you want maximum frame retention |
| 4 | Conservative. Catches same-screen with cursor movement. | Demos with lots of small UI changes |
| **6** | **Recommended default.** Catches same-screen, minor scrolls, tooltip appearances. | **Meeting recordings, platform walkthroughs** |
| 8 | Moderate. Catches same page with different scroll positions. | Long meetings with extended discussions on one screen |
| 10+ | Aggressive. May drop frames with meaningful but subtle differences. | Very long recordings where context budget is tight |

**How to calibrate:**
1. Run with `--dry-run` first
2. Check the `dedup-report.json` — look at the distance values for removed frames
3. If frames you want to keep are being removed (distance values close to your threshold), lower it
4. If too many similar frames survive, raise it

## What It Produces

### Modified files:
- **`manifest.json`** — Updated with only the unique frames. Adds metadata fields: `dedup_applied`, `dedup_threshold`, `dedup_original_count`
- Duplicate frame PNGs and their corresponding audio AAC segments are removed (or moved to `.dupes/`)

### New files:
- **`manifest.original.json`** — Backup of the pre-dedup manifest (created only on first run)
- **`dedup-report.json`** — Full report with per-frame decisions:
  ```json
  {
    "total_frames": 209,
    "kept_frames": 52,
    "removed_frames": 157,
    "reduction_percent": 75.1,
    "threshold": 6,
    "decisions": [
      {"frame": "frame_001.png", "action": "kept", "reason": "first frame", "distance": 0},
      {"frame": "frame_002.png", "action": "removed", "reason": "duplicate of frame 0 (distance=1)", "distance": 1},
      {"frame": "frame_003.png", "action": "kept", "reason": "visually distinct (distance=47 from frame 0)", "distance": 47}
    ]
  }
  ```

## Where It Fits in the Pipeline

```
Phase 0: extract-video-frames → dedupe-frames → elevenlabs-transcribe
                                  ↓
Phase 1: frame-analyst chunks now process only unique frames
```

Deduplication runs **after** frame extraction and **before** transcription and frame analysis. The full audio track (`full_audio.aac`) is not affected — only the frame PNGs and per-frame audio segments are pruned.

### Impact on Frame Analysis

With deduplication, a typical 17-minute meeting recording drops from ~209 frames to ~40-60 unique frames. This means:
- Each of 5 parallel frame-analyst chunks processes ~8-12 frames instead of ~42
- Agents stay well within context window limits
- Analysis is faster and more focused on actual screen transitions
- No loss of visual information — every distinct screen is still captured

## Collaboration

When working as part of an agent team:
- **Depends on** the `extract-video-frames` skill completing first (needs manifest.json and frame files)
- **Feeds into** all Phase 1 agents: `frame-analyst` chunks read the updated manifest
- **Does not affect** `elevenlabs-transcribe` — the full audio track is preserved regardless
- Report to team lead with the reduction percentage so chunk sizes can be adjusted

## Standalone Usage

```
Follow the dedupe-frames skill in ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/SKILL.md.
Frames dir: screencast/platform-overview-frames/
Run with default threshold first as a dry run, then apply.
```

## Agent Team Usage

```
"frame-deduplicator" — Follow the dedupe-frames skill in ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/SKILL.md.
Run: python ${CLAUDE_PLUGIN_ROOT}/skills/dedupe-frames/scripts/dedupe-frames.py screencast/{meeting-name}-frames/ --keep-originals
Wait for video-extractor to complete first. Report the reduction percentage to the team lead
so frame-analyst chunk sizes can be adjusted based on remaining frame count.
```
