#!/usr/bin/env bash
# serve-wireframe.sh — serve a wireframe directory over local HTTP so it can be
# driven by browser automation.
#
# Why a server at all: browser-automation `navigate` rewrites `file:///…` to
# `https://file:///…` and fails. Double-clicking the HTML is fine for a human;
# anything scripted needs HTTP.
#
# Why not 8787: it is `wrangler dev`'s default and collides constantly. This
# script deliberately starts at 8791 and never probes 8787 unless you ask for it
# explicitly with `--port 8787`.
#
# Responses are sent `Cache-Control: no-store` — the wireframe is rewritten
# between interview rounds and a 304 from a stale cache silently invalidates
# everything measured afterwards.
#
#   serve-wireframe.sh start <dir> [--port N]   bind (or reuse) and print URLs
#   serve-wireframe.sh status [<dir>]           is it up, and where
#   serve-wireframe.sh stop [<dir>]             shut it down
#   serve-wireframe.sh url <file> [<dir>]       URL for one file, nothing else
#
# State lives in <dir>/.serve.json + .serve.log (add them to .gitignore, or let
# the skill do it).

set -euo pipefail

DEFAULT_PORT=8791
MAX_PORT=8799
SKIPPED_PORT=8787   # wrangler dev's default — never auto-probed

CMD="${1:-start}"; shift || true

DIR=""
PORT=""
FILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="${2:?--port needs a value}"; shift 2 ;;
    --port=*) PORT="${1#*=}"; shift ;;
    -*) echo "unknown flag: $1" >&2; exit 2 ;;
    *) if [ -z "$DIR" ] && [ "$CMD" != "url" ]; then DIR="$1"
       elif [ "$CMD" = "url" ] && [ -z "$FILE" ]; then FILE="$1"
       elif [ -z "$DIR" ]; then DIR="$1"
       fi; shift ;;
  esac
done
DIR="${DIR:-.}"

if [ ! -d "$DIR" ]; then echo "not a directory: $DIR" >&2; exit 2; fi
DIR="$(cd "$DIR" && pwd)"
STATE="$DIR/.serve.json"
LOG="$DIR/.serve.log"

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "python3 not found — required to serve. Install it, or serve \"$DIR\" yourself" >&2
  echo "on a local port and pass that URL to the browser step." >&2
  exit 3
fi

# ── helpers ────────────────────────────────────────────────────────────────
port_free() {  # authoritative: can we actually bind it?
  "$PY" - "$1" <<'PY' >/dev/null 2>&1
import socket, sys
s = socket.socket()
try:
    s.bind(("127.0.0.1", int(sys.argv[1]))); sys.exit(0)
except OSError:
    sys.exit(1)
finally:
    s.close()
PY
}

port_holder() {  # informational; may print nothing if lsof is unavailable
  command -v lsof >/dev/null 2>&1 || return 0
  lsof -nP -iTCP:"$1" -sTCP:LISTEN 2>/dev/null | awk 'NR==2 {print $1" (pid "$2")"}'
}

alive() { [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null; }

read_state() {  # sets SPID / SPORT from the state file, empty if absent/stale
  SPID=""; SPORT=""
  [ -f "$STATE" ] || return 0
  SPID="$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1])).get("pid",""))' "$STATE" 2>/dev/null || true)"
  SPORT="$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1])).get("port",""))' "$STATE" 2>/dev/null || true)"
}

list_urls() {
  local base="$1" found=0
  while IFS= read -r f; do
    found=1; echo "    $base/$(basename "$f")"
  done < <(find "$DIR" -maxdepth 1 -name '*.html' | sort)
  [ "$found" = 1 ] || echo "    (no .html in $DIR yet)"
}

# ── commands ───────────────────────────────────────────────────────────────
case "$CMD" in

start)
  read_state
  # Reuse a live server, but never silently ignore an explicit --port: if the
  # caller named a port and something else is already serving this dir, say so
  # rather than printing a URL on a port they did not ask for.
  if alive "$SPID"; then
    if [ -n "$PORT" ] && [ "$PORT" != "$SPORT" ]; then
      echo "  ✗ a server for this dir is already running on $SPORT (pid $SPID)," >&2
      echo "    but --port $PORT was requested. Run 'stop' first, or drop --port." >&2
      exit 1
    fi
    echo "  reusing live server — pid $SPID on $SPORT"
    echo "  ✓ http://127.0.0.1:$SPORT/"
    list_urls "http://127.0.0.1:$SPORT"
    exit 0
  fi

  if [ -n "$PORT" ]; then
    if ! port_free "$PORT"; then
      h="$(port_holder "$PORT")"
      echo "  ✗ port $PORT is in use${h:+ by $h}" >&2
      echo "    free it, or re-run without --port to auto-select." >&2
      exit 1
    fi
    CHOSEN="$PORT"
  else
    CHOSEN=""
    p=$DEFAULT_PORT
    echo "  $SKIPPED_PORT skipped (wrangler dev default)"
    while [ "$p" -le "$MAX_PORT" ]; do
      if port_free "$p"; then CHOSEN="$p"; echo "  $p free → bound"; break; fi
      h="$(port_holder "$p")"; echo "  $p busy${h:+ → $h}"
      p=$((p+1))
    done
    if [ -z "$CHOSEN" ]; then
      echo "  ✗ no free port in $DEFAULT_PORT–$MAX_PORT. Pass --port N." >&2
      exit 1
    fi
  fi

  # Inline server: SimpleHTTPRequestHandler + no-store, bound to loopback only.
  nohup "$PY" -c '
import sys, functools, http.server, socketserver
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()
port, root = int(sys.argv[1]), sys.argv[2]
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", port), functools.partial(H, directory=root)) as s:
    s.serve_forever()
' "$CHOSEN" "$DIR" >"$LOG" 2>&1 &
  NEWPID=$!

  # Confirm it actually came up rather than reporting a URL that 404s the tab.
  # 5s, not 2s: a pyenv/asdf `python3` shim can take over a second to exec, and
  # a premature "failed to start" is worse than a slightly slower start.
  ok=0
  for _ in $(seq 1 25); do
    if ! alive "$NEWPID"; then break; fi
    if ! port_free "$CHOSEN"; then ok=1; break; fi
    sleep 0.2
  done
  if [ "$ok" != 1 ]; then
    echo "  ✗ server failed to start; last output:" >&2
    tail -5 "$LOG" >&2 || true
    exit 1
  fi

  printf '{"pid":%s,"port":%s,"dir":"%s"}\n' "$NEWPID" "$CHOSEN" "$DIR" >"$STATE"
  echo
  echo "  ✓ http://127.0.0.1:$CHOSEN/"
  list_urls "http://127.0.0.1:$CHOSEN"
  echo "    pid $NEWPID · log $LOG · no-store (safe to rebuild + reload)"
  ;;

status)
  read_state
  if alive "$SPID"; then
    echo "  up — pid $SPID · http://127.0.0.1:$SPORT/"
    list_urls "http://127.0.0.1:$SPORT"
  else
    echo "  down${SPID:+ (stale state file: pid $SPID not running)}"
    exit 1
  fi
  ;;

stop)
  read_state
  if alive "$SPID"; then kill "$SPID" 2>/dev/null || true; echo "  stopped pid $SPID (port $SPORT)"
  else echo "  nothing running"; fi
  rm -f "$STATE"
  ;;

url)
  read_state
  alive "$SPID" || { echo "server is not running — run 'start $DIR' first" >&2; exit 1; }
  echo "http://127.0.0.1:$SPORT/${FILE:-}"
  ;;

*)
  echo "usage: serve-wireframe.sh {start|status|stop|url} [<dir>] [--port N]" >&2
  exit 2 ;;
esac
