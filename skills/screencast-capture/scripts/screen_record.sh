#!/usr/bin/env bash
# screen_record.sh — OS screen-recording backend for the screencast-capture skill (macOS / avfoundation).
#
# Records a chosen MONITOR to a native-resolution H.264 MP4 while the agent drives the browser via
# the Claude-in-Chrome MCP tools. Unlike the gif_creator path (tab pixels, hard-capped ~1200px,
# 256-color dithering) this captures the real display: native resolution, configurable bitrate/quality,
# and monitor selection. Video only — no mic/system audio (the reel's narration is added later).
#
# Subcommands:
#   devices                                        list avfoundation screen-capture devices (monitor -> index)
#   check   <idx> [dir]                            ~1.5s test capture; verify Screen-Recording permission + non-black
#   start   <idx> <out.mp4> [fps] [crf] [crop]     start a background recording (self-detaches; writes a pidfile)
#   stop    <out.mp4>                              graceful stop (SIGINT so ffmpeg finalizes the moov atom), verify
#
# <idx>  — avfoundation video device index of the screen (see `devices`; e.g. "Capture screen 0" -> its [N]).
# [crop] — ffmpeg crop "W:H:X:Y" in captured-display pixels; omit to record the whole display.
#          On a HiDPI/Retina display (devicePixelRatio 2) multiply CSS coords by 2 for the crop rect.
#
# Clean shutdown matters: SIGKILL leaves a headerless, unplayable MP4. This uses SIGINT + a wait so
# ffmpeg writes the trailer. The recording process is nohup-detached so it survives across separate
# tool calls (start now, drive the browser, stop later).
set -uo pipefail

FFMPEG="${FFMPEG:-ffmpeg}"
FFPROBE="${FFPROBE:-ffprobe}"
statedir() { echo "${TMPDIR:-/tmp}/screencast-capture"; }

need() { command -v "$1" >/dev/null 2>&1 || { echo "$1 not found (brew install ffmpeg)" >&2; exit 3; }; }
need "$FFMPEG"; need "$FFPROBE"

# The avfoundation device-open HANGS (does not error) when Screen-Recording permission is missing,
# and ffmpeg's own -t does not bound it. Guard capture-open with coreutils timeout/gtimeout when present.
TIMEOUT_BIN="$(command -v timeout || command -v gtimeout || true)"
ff_to() { local secs="$1"; shift; if [ -n "$TIMEOUT_BIN" ]; then "$TIMEOUT_BIN" -k 3 "$secs" "$@"; else "$@"; fi; }

cmd="${1:-}"; shift 2>/dev/null || true

case "$cmd" in
  devices)
    # avfoundation prints devices to stderr then exits non-zero — expected.
    "$FFMPEG" -hide_banner -f avfoundation -list_devices true -i "" 2>&1 \
      | grep -Ei 'video devices|capture screen|facetime|camera' || true
    ;;

  check)
    IDX="${1:?display index (see 'devices')}"; DIR="${2:-$(statedir)}"
    mkdir -p "$DIR"; T="$DIR/perm_test_${IDX}.mp4"; LOG="$DIR/check_${IDX}.log"; rm -f "$T"
    # NB: capture rc directly (not via `if ! cmd`, which clobbers $? under the `!`).
    ff_to 10 "$FFMPEG" -hide_banner -nostdin -y -f avfoundation -capture_cursor 1 \
      -framerate 15 -t 1.5 -i "${IDX}:none" -pix_fmt yuv420p "$T" >"$LOG" 2>&1
    rc=$?
    if [ "$rc" != 0 ]; then
      if [ "$rc" = 124 ] || [ "$rc" = 137 ]; then   # 124 = SIGTERM timeout, 137 = SIGKILL escalation
        echo "FAIL: capture timed out opening screen ${IDX} — macOS Screen-Recording permission is not granted." >&2
        echo "      Grant it: System Settings ▸ Privacy & Security ▸ Screen Recording ▸ enable the app that runs" >&2
        echo "      Claude Code (Terminal / iTerm / VS Code / Claude), then fully quit + reopen it and retry." >&2
        exit 5
      fi
      echo "FAIL: capture errored for screen ${IDX} (rc=$rc; see $LOG)" >&2; tail -4 "$LOG" >&2; exit 4
    fi
    [ -s "$T" ] || { echo "FAIL: no output for screen ${IDX} (see $LOG)"; exit 4; }
    # Mean luma of a mid-clip frame. A denied Screen-Recording permission yields black/near-black.
    Y="$("$FFMPEG" -hide_banner -nostdin -i "$T" -vf "select=gte(n\,10),signalstats,metadata=print" \
          -frames:v 1 -f null - 2>&1 | grep -oE 'YAVG=[0-9.]+' | head -1 | cut -d= -f2)"
    echo "screen ${IDX}: test clip $T  meanY=${Y:-unknown}"
    if [ -n "${Y:-}" ] && awk "BEGIN{exit !($Y < 3.0)}"; then
      echo "FAIL: frames are black — grant Screen Recording permission to the host app in" >&2
      echo "      System Settings ▸ Privacy & Security ▸ Screen Recording, then retry." >&2
      exit 5
    fi
    echo "OK: screen ${IDX} captures a non-black image"
    ;;

  start)
    IDX="${1:?display index}"; OUT="${2:?output mp4}"; FPS="${3:-30}"; CRF="${4:-18}"; CROP="${5:-}"
    DIR="$(statedir)"; mkdir -p "$DIR" "$(dirname "$OUT")"
    PIDF="$DIR/record.pid"; LOG="$DIR/record.log"
    if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF" 2>/dev/null)" 2>/dev/null; then
      echo "FAIL: already recording (pid $(cat "$PIDF")); run 'stop' first" >&2; exit 6
    fi
    if [ -n "$CROP" ]; then VF=(-vf "crop=${CROP},format=yuv420p"); else VF=(-pix_fmt yuv420p); fi
    rm -f "$OUT"
    # -capture_mouse_clicks flashes clicks; -capture_cursor draws the pointer — both nice for a demo.
    nohup "$FFMPEG" -hide_banner -nostdin -y -f avfoundation \
      -capture_cursor 1 -capture_mouse_clicks 1 -framerate "$FPS" -i "${IDX}:none" \
      "${VF[@]}" -c:v libx264 -preset veryfast -crf "$CRF" -movflags +faststart \
      "$OUT" >"$LOG" 2>&1 &
    echo $! > "$PIDF"
    sleep 1.2
    if ! kill -0 "$(cat "$PIDF")" 2>/dev/null; then
      echo "FAIL: ffmpeg exited immediately (bad index/crop?); see $LOG" >&2
      tail -6 "$LOG" >&2; rm -f "$PIDF"; exit 4
    fi
    # A live pid is not enough: without Screen-Recording permission ffmpeg stays alive but STUCK at
    # device-open, writing nothing. Confirm bytes are actually landing before declaring success.
    sz=0
    for _ in 1 2 3; do sleep 1; sz="$(stat -f%z "$OUT" 2>/dev/null || echo 0)"; [ "${sz:-0}" -ge 2000 ] && break; done
    if [ "${sz:-0}" -lt 2000 ]; then
      kill -INT "$(cat "$PIDF")" 2>/dev/null; sleep 0.5; kill -9 "$(cat "$PIDF")" 2>/dev/null; rm -f "$PIDF"
      echo "FAIL: no data after ~3s — screen ${IDX} is not being captured (Screen-Recording permission?). See $LOG" >&2
      tail -6 "$LOG" >&2; exit 5
    fi
    echo "recording: pid=$(cat "$PIDF") -> $OUT  (screen $IDX, ${FPS}fps, crf $CRF${CROP:+, crop $CROP})"
    ;;

  stop)
    OUT="${1:-}"; DIR="$(statedir)"; PIDF="$DIR/record.pid"; LOG="$DIR/record.log"
    [ -f "$PIDF" ] || { echo "no active recording (no pidfile at $PIDF)" >&2; exit 2; }
    PID="$(cat "$PIDF" 2>/dev/null)"
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
      kill -INT "$PID" 2>/dev/null                     # graceful — ffmpeg writes the trailer
      for _ in $(seq 1 60); do kill -0 "$PID" 2>/dev/null || break; sleep 0.2; done
      if kill -0 "$PID" 2>/dev/null; then kill -TERM "$PID" 2>/dev/null; sleep 1; fi
    fi
    rm -f "$PIDF"
    if [ -n "$OUT" ]; then
      [ -s "$OUT" ] || { echo "FAIL: output missing/empty: $OUT (see $LOG)" >&2; tail -6 "$LOG" >&2; exit 4; }
      DUR="$("$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)"
      WH="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$OUT" 2>/dev/null)"
      echo "stopped: $OUT  ${WH}  duration=${DUR}s"
    else
      echo "stopped."
    fi
    ;;

  *)
    echo "usage: screen_record.sh devices | check <idx> [dir] | start <idx> <out.mp4> [fps] [crf] [crop] | stop <out.mp4>" >&2
    exit 2 ;;
esac
