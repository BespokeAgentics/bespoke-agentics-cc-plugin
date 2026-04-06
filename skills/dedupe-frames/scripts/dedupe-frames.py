#!/usr/bin/env python3
"""
Frame Deduplication Script
==========================
Removes near-duplicate frames from a video frame extraction directory.
Uses perceptual hashing (dhash) to compare consecutive frames and drops
frames that are visually identical or nearly identical to their predecessor.

Usage:
    python dedupe-frames.py <frames-dir> [--threshold 6] [--hash-size 16] [--dry-run]

Arguments:
    frames-dir      Directory containing extracted frames and manifest.json
    --threshold     Max Hamming distance to consider frames as duplicates (default: 6)
                    Lower = stricter (fewer duplicates caught). Higher = more aggressive.
                    Recommended: 4-8 for meeting recordings. 2 for near-exact only.
    --hash-size     Hash size in bits per dimension (default: 16, producing 512-bit hash)
                    Larger = more precise comparison. 8 = 128-bit, 16 = 512-bit.
    --dry-run       Show what would be removed without actually removing anything
    --keep-originals Move duplicates to a .dupes/ subfolder instead of deleting

Requires: pip install imagehash Pillow

Output:
    - Updates manifest.json with only the unique frames
    - Saves original manifest as manifest.original.json
    - Writes dedup-report.json with statistics and per-frame decisions
    - Optionally moves duplicate frames to .dupes/ subfolder
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

try:
    import imagehash
    from PIL import Image
except ImportError:
    print("ERROR: Required packages not installed. Run:")
    print("  pip install imagehash Pillow --break-system-packages")
    sys.exit(1)


def compute_hash(image_path: str, hash_size: int = 16) -> imagehash.ImageHash:
    """Compute dhash (difference hash) for an image file."""
    img = Image.open(image_path)
    return imagehash.dhash(img, hash_size=hash_size)


def dedupe_frames(
    frames_dir: str,
    threshold: int = 6,
    hash_size: int = 16,
    dry_run: bool = False,
    keep_originals: bool = False,
) -> dict:
    """
    Deduplicate frames in a directory based on perceptual hash similarity.

    Strategy: Sequential comparison — each frame is compared to the last
    *kept* frame. If the Hamming distance is <= threshold, the frame is
    considered a duplicate and removed. This preserves the first frame of
    every visually distinct screen/view.

    Returns a report dict with statistics and per-frame decisions.
    """
    frames_path = Path(frames_dir)
    manifest_path = frames_path / "manifest.json"

    if not manifest_path.exists():
        print(f"ERROR: No manifest.json found in {frames_dir}")
        sys.exit(1)

    # Load manifest
    with open(manifest_path) as f:
        manifest = json.load(f)

    # Back up original manifest
    original_manifest_path = frames_path / "manifest.original.json"
    if not original_manifest_path.exists():
        with open(original_manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"Backed up original manifest to {original_manifest_path.name}")

    frames = manifest.get("frames", [])
    if not frames:
        print("ERROR: No frames found in manifest")
        sys.exit(1)

    print(f"Processing {len(frames)} frames with threshold={threshold}, hash_size={hash_size}")
    print(f"Hash bits: {hash_size * hash_size * 2} (dhash row + col)")
    print()

    # Compute hashes for all frames
    hashes = []
    for i, frame in enumerate(frames):
        frame_file = frame.get("path") or frame.get("frame_file") or frame.get("file")
        frame_path = frames_path / frame_file
        if not frame_path.exists():
            print(f"  WARNING: Frame not found: {frame_file}")
            hashes.append(None)
            continue
        h = compute_hash(str(frame_path), hash_size)
        hashes.append(h)
        if (i + 1) % 50 == 0:
            print(f"  Hashed {i + 1}/{len(frames)} frames...")

    print(f"  Hashed all {len(frames)} frames")
    print()

    # Sequential deduplication
    kept_indices = []
    removed_indices = []
    decisions = []
    last_kept_hash = None
    last_kept_idx = None

    for i, (frame, h) in enumerate(zip(frames, hashes)):
        frame_file = frame.get("path") or frame.get("frame_file") or frame.get("file")

        if h is None:
            decisions.append({
                "frame": frame_file,
                "index": i,
                "action": "skipped",
                "reason": "file not found",
            })
            continue

        if last_kept_hash is None:
            # Always keep the first frame
            kept_indices.append(i)
            last_kept_hash = h
            last_kept_idx = i
            decisions.append({
                "frame": frame_file,
                "index": i,
                "action": "kept",
                "reason": "first frame",
                "distance": 0,
            })
            continue

        distance = last_kept_hash - h
        if distance <= threshold:
            removed_indices.append(i)
            decisions.append({
                "frame": frame_file,
                "index": i,
                "action": "removed",
                "reason": f"duplicate of frame {last_kept_idx} (distance={distance})",
                "distance": distance,
                "duplicate_of": last_kept_idx,
            })
        else:
            kept_indices.append(i)
            last_kept_hash = h
            last_kept_idx = i
            decisions.append({
                "frame": frame_file,
                "index": i,
                "action": "kept",
                "reason": f"visually distinct (distance={distance} from frame {kept_indices[-2] if len(kept_indices) > 1 else 0})",
                "distance": distance,
            })

    # Report
    reduction_pct = (len(removed_indices) / len(frames) * 100) if frames else 0
    report = {
        "total_frames": len(frames),
        "kept_frames": len(kept_indices),
        "removed_frames": len(removed_indices),
        "reduction_percent": round(reduction_pct, 1),
        "threshold": threshold,
        "hash_size": hash_size,
        "hash_bits": hash_size * hash_size * 2,
        "decisions": decisions,
    }

    print(f"Results:")
    print(f"  Total frames:   {len(frames)}")
    print(f"  Kept:           {len(kept_indices)}")
    print(f"  Removed:        {len(removed_indices)}")
    print(f"  Reduction:      {reduction_pct:.1f}%")
    print()

    if dry_run:
        print("DRY RUN — no files modified")
        # Save report even in dry run
        report_path = frames_path / "dedup-report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {report_path.name}")
        return report

    # Move or remove duplicate frames and their audio segments
    if keep_originals:
        dupes_dir = frames_path / ".dupes"
        dupes_dir.mkdir(exist_ok=True)

    for idx in removed_indices:
        frame = frames[idx]
        frame_file = frame.get("path") or frame.get("frame_file") or frame.get("file")
        audio_file = frame.get("audio_path") or frame.get("audio_file")

        frame_path = frames_path / frame_file
        if frame_path.exists():
            if keep_originals:
                shutil.move(str(frame_path), str(frames_path / ".dupes" / frame_file))
            else:
                frame_path.unlink()

        # Also handle corresponding audio segment if it exists
        if audio_file:
            audio_path = frames_path / audio_file
            if audio_path.exists():
                if keep_originals:
                    shutil.move(str(audio_path), str(frames_path / ".dupes" / audio_file))
                else:
                    audio_path.unlink()

    # Update manifest with only kept frames
    kept_frames = [frames[i] for i in kept_indices]

    # Preserve all other manifest fields, just update frames
    updated_manifest = dict(manifest)
    updated_manifest["frames"] = kept_frames
    updated_manifest["total_frames"] = len(kept_frames)
    updated_manifest["dedup_applied"] = True
    updated_manifest["dedup_threshold"] = threshold
    updated_manifest["dedup_original_count"] = len(frames)

    with open(manifest_path, "w") as f:
        json.dump(updated_manifest, f, indent=2)
    print(f"Updated manifest.json ({len(kept_frames)} frames)")

    # Save dedup report
    report_path = frames_path / "dedup-report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Dedup report saved to {report_path.name}")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Remove near-duplicate frames from a video extraction directory"
    )
    parser.add_argument(
        "frames_dir",
        help="Directory containing extracted frames and manifest.json",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=6,
        help="Max Hamming distance for duplicates (default: 6). Lower=stricter.",
    )
    parser.add_argument(
        "--hash-size",
        type=int,
        default=16,
        help="Hash size per dimension (default: 16, producing 512-bit hash).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without modifying files.",
    )
    parser.add_argument(
        "--keep-originals",
        action="store_true",
        help="Move duplicates to .dupes/ instead of deleting.",
    )

    args = parser.parse_args()
    dedupe_frames(
        args.frames_dir,
        threshold=args.threshold,
        hash_size=args.hash_size,
        dry_run=args.dry_run,
        keep_originals=args.keep_originals,
    )


if __name__ == "__main__":
    main()
