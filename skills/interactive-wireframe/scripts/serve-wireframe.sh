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
#   serve-wireframe.sh feedback <dir>           print browser comments newer than
#                                               the cursor; exit 1 when none
#   serve-wireframe.sh await-feedback <dir> [--timeout N]
#                                               block until a comment arrives
#                                               (exit 0) or timeout (exit 124)
#   serve-wireframe.sh reply <dir> '<text>' [--to <fb-id>]
#                                               append a reply the page renders
#
# The server also accepts POST /__feedback from the wireframe's in-page feedback
# kit and appends each JSON body to <dir>/.feedback.jsonl. Replies live in
# <dir>/.replies.jsonl, which the page polls. See references/live-feedback.md.
#
# State lives in <dir>/.serve.json + .serve.log; feedback in .feedback.jsonl,
# .feedback.cursor, .replies.jsonl (add all to .gitignore, or let the skill
# do it).

set -euo pipefail

DEFAULT_PORT=8791
MAX_PORT=8799
SKIPPED_PORT=8787   # wrangler dev's default — never auto-probed

CMD="${1:-start}"; shift || true

DIR=""
PORT=""
FILE=""
TEXT=""
REPLY_TO=""
TIMEOUT=300
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="${2:?--port needs a value}"; shift 2 ;;
    --port=*) PORT="${1#*=}"; shift ;;
    --to) REPLY_TO="${2:?--to needs a value}"; shift 2 ;;
    --to=*) REPLY_TO="${1#*=}"; shift ;;
    --timeout) TIMEOUT="${2:?--timeout needs a value}"; shift 2 ;;
    --timeout=*) TIMEOUT="${1#*=}"; shift ;;
    -*) echo "unknown flag: $1" >&2; exit 2 ;;
    *) if [ "$CMD" = "url" ] && [ -z "$FILE" ]; then FILE="$1"
       elif [ -z "$DIR" ]; then DIR="$1"
       elif [ "$CMD" = "reply" ] && [ -z "$TEXT" ]; then TEXT="$1"
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
port_free() {  # authoritative: can we actually bind it? SO_REUSEADDR mirrors the
               # server's own bind, so a TIME_WAIT port left by `stop` counts free.
  "$PY" - "$1" <<'PY' >/dev/null 2>&1
import socket, sys
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind(("127.0.0.1", int(sys.argv[1]))); sys.exit(0)
except OSError:
    sys.exit(1)
finally:
    s.close()
PY
}

port_holder() {  # informational; may print nothing if lsof is unavailable —
                 # must never fail (pipefail + set -e would abort the port scan)
  command -v lsof >/dev/null 2>&1 || return 0
  lsof -nP -iTCP:"$1" -sTCP:LISTEN 2>/dev/null | awk 'NR==2 {print $1" (pid "$2")"}' || true
}

alive() { [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null; }

read_state() {  # sets SPID / SPORT / SV from the state file, empty if absent/stale
  SPID=""; SPORT=""; SV=1
  [ -f "$STATE" ] || return 0
  SPID="$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1])).get("pid",""))' "$STATE" 2>/dev/null || true)"
  SPORT="$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1])).get("port",""))' "$STATE" 2>/dev/null || true)"
  SV="$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1])).get("v",1))' "$STATE" 2>/dev/null || echo 1)"
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
  # A live pre-v2 server has no POST /__feedback endpoint — replace it so the
  # in-page feedback kit works after an upgrade without a manual stop.
  if alive "$SPID" && [ "${SV:-1}" -lt 2 ]; then
    echo "  restarting pid $SPID — old server has no /__feedback endpoint"
    kill "$SPID" 2>/dev/null || true
    if [ -n "$SPORT" ]; then
      for _ in $(seq 1 25); do
        if port_free "$SPORT"; then break; fi
        sleep 0.2
      done
    fi
    SPID=""
  fi
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
  # POST /__feedback appends the (validated-JSON, <=64KB) body as one line of
  # <dir>/.feedback.jsonl — the in-page feedback kit's transport. Single-threaded
  # TCPServer, so appends are serialized without a lock.
  nohup "$PY" -c '
import sys, os, json, functools, http.server, socketserver
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()
    def do_POST(self):
        if self.path != "/__feedback":
            self.send_error(404); return
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if not 0 < n <= 65536:
            self.send_error(413); return
        body = self.rfile.read(n)
        try:
            json.loads(body)
        except Exception:
            self.send_error(400); return
        with open(os.path.join(self.directory, ".feedback.jsonl"), "ab") as f:
            f.write(body.rstrip(b"\n") + b"\n")
        self.send_response(204); self.end_headers()
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

  printf '{"pid":%s,"port":%s,"dir":"%s","v":2}\n' "$NEWPID" "$CHOSEN" "$DIR" >"$STATE"
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

feedback)
  # Print entries appended since the cursor, then advance it.
  # Exit 0 = printed something, 1 = nothing new. Truncation-safe.
  "$PY" - "$DIR/.feedback.jsonl" "$DIR/.feedback.cursor" <<'PY'
import os, sys
fb, cur = sys.argv[1], sys.argv[2]
if not os.path.exists(fb):
    sys.exit(1)
off = 0
try:
    off = int(open(cur).read().strip() or 0)
except Exception:
    pass
size = os.path.getsize(fb)
if size < off:
    off = 0            # file was truncated or recreated
if size == off:
    sys.exit(1)
with open(fb, "rb") as f:
    f.seek(off)
    data = f.read()
sys.stdout.write(data.decode("utf-8", "replace"))
open(cur, "w").write(str(size))
PY
  ;;

await-feedback)
  # Block until a new comment arrives (exit 0, entries printed) or timeout
  # (exit 124). Designed to run as a background task that wakes the agent.
  end=$(( $(date +%s) + TIMEOUT ))
  while :; do
    if "$0" feedback "$DIR"; then exit 0; fi
    if [ "$(date +%s)" -ge "$end" ]; then exit 124; fi
    sleep 1
  done
  ;;

reply)
  # Append a reply the page's thread panel renders (poll ~2s). Prints the id.
  if [ -z "$TEXT" ]; then
    echo "reply needs text: serve-wireframe.sh reply <dir> '<text>' [--to <fb-id>]" >&2
    exit 2
  fi
  "$PY" - "$DIR/.replies.jsonl" "$TEXT" "$REPLY_TO" <<'PY'
import json, sys, time, random, string
rid = "re-" + format(int(time.time() * 1000), "x") + "-" + "".join(
    random.choices(string.ascii_lowercase + string.digits, k=2))
e = {"id": rid,
     "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
     "text": sys.argv[2]}
if sys.argv[3]:
    e["to"] = sys.argv[3]
open(sys.argv[1], "a").write(json.dumps(e) + "\n")
print(rid)
PY
  ;;

*)
  echo "usage: serve-wireframe.sh {start|status|stop|url|feedback|await-feedback|reply} [<dir>] [--port N] [--timeout N] [--to <fb-id>]" >&2
  exit 2 ;;
esac
