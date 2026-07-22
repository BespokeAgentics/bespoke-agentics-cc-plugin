#!/usr/bin/env bash
# ============================================================================
# install-tts-hook.sh — installs the Claude Code TTS lifecycle announcer.
# Writes ~/.claude/hooks/tts-announce-stop.sh and wires it into Stop,
# StopFailure, and Notification in ~/.claude/settings.json. Idempotent.
#
# Optional ElevenLabs setup — configures engine + voice + key into
# settings.json "env" when you either pass the key at run time:
#     ELEVENLABS_API_KEY='xi-...' bash install-tts-hook.sh
# or force it (key set separately) with:
#     bash install-tts-hook.sh --elevenlabs
# Voice defaults to ImnfuV8oxhB7ya99oJfc; override with ELEVENLABS_VOICE_ID.
#
# After install, mute anytime with:  bash ~/.claude/hooks/tts-announce-stop.sh --mute
# Respects CLAUDE_CONFIG_DIR.
# ============================================================================
set -euo pipefail

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
HOOK_DIR="$CLAUDE_DIR/hooks"
HOOK="$HOOK_DIR/tts-announce-stop.sh"
SETTINGS="$CLAUDE_DIR/settings.json"
EVENTS="Stop StopFailure Notification"

WANT_EL=0
case "${1:-}" in --elevenlabs) WANT_EL=1 ;; esac
[ -n "${ELEVENLABS_API_KEY:-}" ] && WANT_EL=1
EL_VOICE_ID="${ELEVENLABS_VOICE_ID:-ImnfuV8oxhB7ya99oJfc}"

mkdir -p "$HOOK_DIR"
echo "→ writing hook script: $HOOK"
cat > "$HOOK" <<'TTS_SCRIPT_EOF'
#!/usr/bin/env bash
# ============================================================================
# tts-announce-stop.sh  —  Claude Code lifecycle announcer (text-to-speech)
# ----------------------------------------------------------------------------
# One hook script, wired to several Claude Code events. It reads the event's
# JSON on stdin, figures out WHICH event fired (from .hook_event_name), builds
# a short spoken line prefixed with the project / branch / task it came from,
# and speaks it — with a DISTINCT VOICE per category and a CROSS-PROCESS QUEUE
# so multiple sessions never talk over each other.
#
# Categories & default voices (macOS `say`):
#   done      Stop            calm      voice: Samantha   priority 5
#   failure   StopFailure     alert     voice: Daniel     priority 1   cue "error"
#   needs-you Notification    urgent    voice: Karen      priority 0   cue "attention"
#   subagent  SubagentStop    calm      voice: Samantha   priority 6   (opt-in)
#   headsup   PreCompact /    note      voice: Moira      priority 7   (opt-in)
#             SessionStart
#
# The queue is a filesystem mutex (atomic mkdir) + a priority ticket line, so
# only ONE announcement plays at a time across ALL sessions on the machine;
# a needs-you jumps ahead of queued "done" messages. Everything runs detached,
# so the turn is never delayed. Exit 0 always (never blocks Claude).
#
# ---- Install (global) -----------------------------------------------------
# Wire the SAME command under hooks.Stop, hooks.StopFailure, hooks.Notification
# in ~/.claude/settings.json:
#   bash "$HOME/.claude/hooks/tts-announce-stop.sh"
# (Use install-tts-hook.sh — it does this idempotently. The filename keeps the
#  -stop suffix for backward compatibility; the script now handles many events.)
#
# ---- Config (env vars; CLI flags override) --------------------------------
#   Engine / summary (as before):
#     CLAUDE_TTS_ENGINE say|elevenlabs        CLAUDE_TTS_RATE  words-per-min
#     CLAUDE_TTS_SUMMARIZER auto|anthropic|openai|claude-cli|heuristic
#     CLAUDE_TTS_MAX_WORDS (18)   ANTHROPIC_API_KEY / OPENAI_API_KEY
#   Voices (macOS `say`; run `say -v '?'` to list installed voices):
#     CLAUDE_TTS_VOICE           single voice for EVERYTHING (overrides below)
#     CLAUDE_TTS_VOICE_DONE (Samantha)   CLAUDE_TTS_VOICE_FAILURE (Daniel)
#     CLAUDE_TTS_VOICE_NEEDSYOU (Karen)  CLAUDE_TTS_VOICE_HEADSUP (Moira)
#     CLAUDE_TTS_CUE_FAILURE (error)     CLAUDE_TTS_CUE_NEEDSYOU (attention)
#     CLAUDE_TTS_CUE_DONE ('')           CLAUDE_TTS_CUE_HEADSUP (note)
#   Source prefix:
#     CLAUDE_TTS_PROJECT_LABEL auto|git|folder|off   CLAUDE_TTS_SAY_BRANCH 1|0|nonmain
#     CLAUDE_TTS_SAY_TASK 1|0    CLAUDE_TTS_TASK_MAX_WORDS (8)
#   Events:
#     CLAUDE_TTS_NOTIFY_TYPES  which Notification types to speak
#        (default: permission_prompt idle_prompt agent_needs_input elicitation_dialog)
#     CLAUDE_TTS_ANNOUNCE_SUBAGENTS 1  CLAUDE_TTS_ANNOUNCE_PRECOMPACT 1
#     CLAUDE_TTS_ANNOUNCE_SESSIONSTART 1
#   Queue:
#     CLAUDE_TTS_QUEUE_DIR       (default: $TMPDIR/claude-tts-queue)
#     CLAUDE_TTS_QUEUE_MAX_WAIT  seconds to wait for a turn before dropping (90)
#     CLAUDE_TTS_LOCK_STALE      seconds before a held lock is force-broken (120)
#     CLAUDE_TTS_DEBOUNCE_SECONDS  collapse repeats of the same event+project (0=off)
#   ElevenLabs (optional): ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL
#     per-category ids: ELEVENLABS_VOICE_{DONE,FAILURE,NEEDSYOU,HEADSUP}
#   Misc: CLAUDE_TTS_DEBUG 1   CLAUDE_TTS_LOG (~/.claude/tts-announce.log)
#
#   Disable / mute (silence with no restart — checked on every fire):
#     bash tts-announce-stop.sh --mute      # touch the flag file, silence now
#     bash tts-announce-stop.sh --unmute    # remove it, announcements back on
#     bash tts-announce-stop.sh --status    # muted or active?
#     CLAUDE_TTS_DISABLE=1                   # env kill switch (per shell/session)
#     CLAUDE_TTS_MUTE_FILE                   # flag path (default: ~/.claude/tts-mute)
#
#   CLI flags: --event NAME (force event), --engine, --rate, --summarizer,
#              --max-words, --voice, --test (cycle categories),
#              --mute / --unmute / --status
# ============================================================================

set -uo pipefail

# recursion guard (only matters if the claude-cli summarizer is ever used)
if [ "${CLAUDE_TTS_ACTIVE:-}" = "1" ]; then exit 0; fi
SELF="$0"

# ---- defaults (env) --------------------------------------------------------
ENGINE="${CLAUDE_TTS_ENGINE:-say}"
RATE="${CLAUDE_TTS_RATE:-}"
SUMMARIZER="${CLAUDE_TTS_SUMMARIZER:-auto}"
MAX_WORDS="${CLAUDE_TTS_MAX_WORDS:-18}"
ANTHROPIC_MODEL="${ANTHROPIC_TTS_MODEL:-claude-3-5-haiku-latest}"
OPENAI_MODEL="${OPENAI_TTS_MODEL:-gpt-4o-mini}"
ELEVEN_VOICE_ID="${ELEVENLABS_VOICE_ID:-21m00Tcm4TlvDq8ikWAM}"
ELEVEN_MODEL="${ELEVENLABS_MODEL:-eleven_flash_v2_5}"   # low latency (~75ms), good for short lines
LOG="${CLAUDE_TTS_LOG:-$HOME/.claude/tts-announce.log}"

NOTIFY_TYPES="${CLAUDE_TTS_NOTIFY_TYPES:-permission_prompt idle_prompt agent_needs_input elicitation_dialog}"
QUEUE_DIR="${CLAUDE_TTS_QUEUE_DIR:-${TMPDIR:-/tmp}/claude-tts-queue}"
LOCK="${QUEUE_DIR}.lock"
DBDIR="${QUEUE_DIR}.debounce"
QUEUE_MAX_WAIT="${CLAUDE_TTS_QUEUE_MAX_WAIT:-90}"
LOCK_STALE="${CLAUDE_TTS_LOCK_STALE:-120}"
DEBOUNCE="${CLAUDE_TTS_DEBOUNCE_SECONDS:-0}"

EVENT_OVERRIDE=""
VOICE_OVERRIDE="${CLAUDE_TTS_VOICE:-}"
WORKER_MODE=0
WORKER_FILE=""
TEST_MODE=0
ACTION=""
MUTE_FILE="${CLAUDE_TTS_MUTE_FILE:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}/tts-mute}"

CUR_TICKET=""
I_HOLD_LOCK=0

# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
_now() { date +%s 2>/dev/null || echo 0; }

log() {
  [ "${CLAUDE_TTS_DEBUG:-0}" = "1" ] || return 0
  mkdir -p "$(dirname "$LOG")" 2>/dev/null || true
  printf '%s  %s\n' "$(date '+%Y-%m-%dT%H:%M:%S' 2>/dev/null || _now)" "$*" >> "$LOG" 2>/dev/null || true
}

clean_text() {
  perl -0777 -pe '
    s/```.*?```//gs; s/~~~.*?~~~//gs; s/`([^`]*)`/$1/g;
    s/!\[[^\]]*\]\([^)]*\)//g; s/\[([^\]]+)\]\([^)]*\)/$1/g;
    s/^\s{0,3}#{1,6}\s*//mg; s/^\s*[-*+]\s+//mg; s/^\s*\d+\.\s+//mg;
    s/\*\*([^*]+)\*\*/$1/g; s/__([^_]+)__/$1/g; s/\*([^*]+)\*/$1/g;
    s/https?:\/\/\S+//g; s/[#>*_~|`]/ /g; s/\s+/ /g;
  '
}
trim() { sed -E 's/^[^[:alnum:]]+//; s/[[:space:]]+$//; s/^[[:space:]]+//'; }
humanize() { sed -E 's#[/_.-]+# #g; s/  +/ /g; s/^ +//; s/ +$//'; }

# ---------------------------------------------------------------------------
# summarizers (Stop / SubagentStop)
# ---------------------------------------------------------------------------
_sys_prompt() {
  printf '%s' "You announce, in ONE natural spoken sentence of at most ${MAX_WORDS} words, what an AI coding assistant just did this turn, based on its final message to the user. Start with a past-tense verb. Plain speech only: no markdown, lists, quotes, code, file paths, or emoji. If the message is only a question or trivial, reply with a short natural phrase such as 'Claude has a question for you.'"
}
summarize_anthropic() {
  local input="$1" body out text
  [ -n "${ANTHROPIC_API_KEY:-}" ] || return 1
  command -v curl >/dev/null 2>&1 || return 1
  body="$(jq -n --arg m "$ANTHROPIC_MODEL" --arg s "$(_sys_prompt)" --arg u "$input" \
    '{model:$m,max_tokens:60,system:$s,messages:[{role:"user",content:$u}]}')" || return 1
  out="$(curl -sS --max-time 8 https://api.anthropic.com/v1/messages \
      -H "x-api-key: ${ANTHROPIC_API_KEY}" -H "anthropic-version: 2023-06-01" \
      -H "content-type: application/json" -d "$body" 2>/dev/null)" || return 1
  text="$(printf '%s' "$out" | jq -r '.content[0].text // empty' 2>/dev/null)"
  [ -n "$text" ] || return 1; printf '%s' "$text"
}
summarize_openai() {
  local input="$1" body out text
  [ -n "${OPENAI_API_KEY:-}" ] || return 1
  command -v curl >/dev/null 2>&1 || return 1
  body="$(jq -n --arg m "$OPENAI_MODEL" --arg s "$(_sys_prompt)" --arg u "$input" \
    '{model:$m,max_tokens:60,messages:[{role:"system",content:$s},{role:"user",content:$u}]}')" || return 1
  out="$(curl -sS --max-time 8 https://api.openai.com/v1/chat/completions \
      -H "Authorization: Bearer ${OPENAI_API_KEY}" -H "content-type: application/json" \
      -d "$body" 2>/dev/null)" || return 1
  text="$(printf '%s' "$out" | jq -r '.choices[0].message.content // empty' 2>/dev/null)"
  [ -n "$text" ] || return 1; printf '%s' "$text"
}
summarize_claude_cli() {
  local input="$1" text
  command -v claude >/dev/null 2>&1 || return 1
  text="$(CLAUDE_TTS_ACTIVE=1 claude -p \
     "In one spoken sentence of at most ${MAX_WORDS} words, no markdown, say what you just did based on this final message:

${input}" 2>/dev/null)" || return 1
  [ -n "$text" ] || return 1; printf '%s' "$text"
}
heuristic_summary() {
  local cleaned first
  cleaned="$(printf '%s' "$1" | clean_text | trim)"
  [ -z "$cleaned" ] && { printf '%s' "Claude finished the response."; return 0; }
  first="$(printf '%s' "$cleaned" | grep -oE '^[^.!?]+[.!?]' | head -1)"
  [ -z "$first" ] && first="$cleaned"
  printf '%s' "$first" | awk '{ for(i=1;i<=NF && i<=30;i++) printf "%s%s",(i>1?" ":""),$i }'
}
make_summary() {
  local input summary=""
  input="$(printf '%s' "$1" | head -c 4000)"
  case "$SUMMARIZER" in
    anthropic)  summary="$(summarize_anthropic  "$input")" || summary="" ;;
    openai)     summary="$(summarize_openai     "$input")" || summary="" ;;
    claude-cli) summary="$(summarize_claude_cli "$input")" || summary="" ;;
    heuristic)  summary="" ;;
    auto|*)     summary="$(summarize_anthropic "$input")" || summary=""
                [ -z "$summary" ] && { summary="$(summarize_openai "$input")" || summary=""; } ;;
  esac
  [ -n "$summary" ] && summary="$(printf '%s' "$summary" | clean_text | trim)"
  [ -z "$summary" ] && summary="$(heuristic_summary "$1")"
  printf '%s' "$summary"
}

# ---------------------------------------------------------------------------
# source identification (project / branch / task)
# ---------------------------------------------------------------------------
project_label() {
  local cwd="$1" mode="${CLAUDE_TTS_PROJECT_LABEL:-auto}" top name=""
  [ "$mode" = "off" ] && return 0
  [ -n "$cwd" ] || cwd="$PWD"
  if [ "$mode" = "auto" ] || [ "$mode" = "git" ]; then
    if command -v git >/dev/null 2>&1; then
      top="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || true)"
      [ -n "$top" ] && name="$(basename "$top")"
    fi
  fi
  if [ -z "$name" ]; then
    [ "$mode" = "git" ] && return 0
    name="$(basename "$cwd" 2>/dev/null || true)"
  fi
  [ -n "$name" ] && printf '%s' "$name" | humanize
}
branch_label() {
  local cwd="$1" mode="${CLAUDE_TTS_SAY_BRANCH:-1}" br
  case "$mode" in 0|off|no|false) return 0 ;; esac
  command -v git >/dev/null 2>&1 || return 0
  [ -n "$cwd" ] || cwd="$PWD"
  br="$(git -C "$cwd" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  [ -n "$br" ] || return 0
  [ "$br" = "HEAD" ] && return 0
  [ "$mode" = "nonmain" ] && case "$br" in main|master|trunk) return 0 ;; esac
  printf '%s' "$br" | humanize
}
session_task() {
  local tpath="$1" raw
  [ "${CLAUDE_TTS_SAY_TASK:-1}" = "1" ] || return 0
  [ -n "$tpath" ] && [ -f "$tpath" ] || return 0
  command -v jq >/dev/null 2>&1 || return 0
  raw="$(head -n 50 "$tpath" 2>/dev/null | jq -rc '
      select(.type=="user" and (.isMeta != true)) | (.message.content // empty) |
      if type=="string" then . elif type=="array" then ([.[]|select(.type=="text")|.text]|join(" "))
      else empty end' 2>/dev/null | grep -m1 . || true)"
  raw="$(printf '%s' "$raw" | head -c 500 | clean_text | trim)"
  [ -n "$raw" ] || return 0
  printf '%s' "$raw" | awk -v n="${CLAUDE_TTS_TASK_MAX_WORDS:-8}" \
    '{ for(i=1;i<=NF && i<=n;i++) printf "%s%s",(i>1?" ":""),$i }'
}
# build_line <cwd> <transcript> <summary> <include_task 0|1> -> prefixed text
build_line() {
  local cwd="$1" transcript="$2" summary="$3" want_task="${4:-1}"
  local project branch task loc pre
  project="$(project_label "$cwd")"
  branch="$(branch_label  "$cwd")"
  task=""; [ "$want_task" = "1" ] && task="$(session_task "$transcript")"
  loc="$project"
  if [ -n "$branch" ]; then
    if [ -n "$loc" ]; then loc="$loc on $branch"; else loc="branch $branch"; fi
  fi
  pre="$loc"
  if [ -n "$task" ]; then
    if [ -n "$pre" ]; then pre="$pre, $task"; else pre="$task"; fi
  fi
  if [ -n "$pre" ]; then printf '%s: %s' "$pre" "$summary"; else printf '%s' "$summary"; fi
}

# ---------------------------------------------------------------------------
# category -> voice / priority / cue
# ---------------------------------------------------------------------------
voice_for() {
  [ -n "$VOICE_OVERRIDE" ] && { printf '%s' "$VOICE_OVERRIDE"; return; }
  if [ "$ENGINE" = "elevenlabs" ]; then
    case "$1" in
      needsyou) printf '%s' "${ELEVENLABS_VOICE_NEEDSYOU:-$ELEVEN_VOICE_ID}";;
      failure)  printf '%s' "${ELEVENLABS_VOICE_FAILURE:-$ELEVEN_VOICE_ID}";;
      headsup)  printf '%s' "${ELEVENLABS_VOICE_HEADSUP:-$ELEVEN_VOICE_ID}";;
      *)        printf '%s' "${ELEVENLABS_VOICE_DONE:-$ELEVEN_VOICE_ID}";;
    esac; return
  fi
  case "$1" in
    needsyou) printf '%s' "${CLAUDE_TTS_VOICE_NEEDSYOU:-Karen}";;
    failure)  printf '%s' "${CLAUDE_TTS_VOICE_FAILURE:-Daniel}";;
    headsup)  printf '%s' "${CLAUDE_TTS_VOICE_HEADSUP:-Moira}";;
    *)        printf '%s' "${CLAUDE_TTS_VOICE_DONE:-Samantha}";;
  esac
}
priority_for() {
  case "$1" in
    needsyou) echo 0;; failure) echo 1;; done) echo 5;;
    subagent) echo 6;; headsup) echo 7;; *) echo 5;;
  esac
}
cue_for() {
  case "$1" in
    needsyou) printf '%s' "${CLAUDE_TTS_CUE_NEEDSYOU-attention}";;
    failure)  printf '%s' "${CLAUDE_TTS_CUE_FAILURE-error}";;
    headsup)  printf '%s' "${CLAUDE_TTS_CUE_HEADSUP-note}";;
    *)        printf '%s' "${CLAUDE_TTS_CUE_DONE-}";;
  esac
}

# ---------------------------------------------------------------------------
# speaking back-ends
# ---------------------------------------------------------------------------
speak_say() {
  # No arrays: keep this safe under `set -u` on macOS's default bash 3.2.
  local text="$1" voice="$2"
  command -v say >/dev/null 2>&1 || return 1
  if   [ -n "$voice" ] && [ -n "$RATE" ]; then say -v "$voice" -r "$RATE" "$text" 2>/dev/null && return 0
  elif [ -n "$voice" ];                   then say -v "$voice" "$text"          2>/dev/null && return 0
  elif [ -n "$RATE" ];                    then say -r "$RATE" "$text"           2>/dev/null && return 0
  else                                         say "$text"                       2>/dev/null && return 0
  fi
  say "$text" 2>/dev/null              # retry w/o voice/rate if the voice was invalid
}
speak_elevenlabs() {
  local text="$1" vid="$2" body code tmp
  [ -n "${ELEVENLABS_API_KEY:-}" ] || return 1
  command -v afplay >/dev/null 2>&1 || return 1
  command -v curl   >/dev/null 2>&1 || return 1
  [ -n "$vid" ] || vid="$ELEVEN_VOICE_ID"
  tmp="$(mktemp "${TMPDIR:-/tmp}/claude-tts-audio.XXXXXX" 2>/dev/null)" || return 1
  body="$(jq -n --arg t "$text" --arg m "$ELEVEN_MODEL" \
    '{text:$t,model_id:$m,voice_settings:{stability:0.5,similarity_boost:0.75}}')" || { rm -f "$tmp"; return 1; }
  code="$(curl -sS --max-time 20 -o "$tmp" -w '%{http_code}' \
      "https://api.elevenlabs.io/v1/text-to-speech/${vid}" \
      -H "xi-api-key: ${ELEVENLABS_API_KEY}" -H "content-type: application/json" \
      -d "$body" 2>/dev/null)" || { rm -f "$tmp"; return 1; }
  if [ "$code" = "200" ] && [ -s "$tmp" ]; then afplay "$tmp"; rm -f "$tmp"; return 0; fi
  log "elevenlabs HTTP ${code:-?}: $(head -c 200 "$tmp" 2>/dev/null | tr '\n' ' ')"
  rm -f "$tmp"; return 1
}
speak() {  # <text> <voice>
  local text="$1" voice="${2:-}"
  [ -n "$text" ] || return 0
  if [ "$ENGINE" = "elevenlabs" ]; then
    speak_elevenlabs "$text" "$voice" && return 0
    log "elevenlabs failed -> say"
    speak_say "$text" "" || log "no local TTS engine"
    return 0
  fi
  speak_say "$text" "$voice" || log "no local TTS engine (say missing)"
}

# ---------------------------------------------------------------------------
# cross-process speech QUEUE  (atomic-mkdir mutex + priority ticket line)
# ---------------------------------------------------------------------------
_enqueue() {                              # $1=priority -> echoes ticket path
  mkdir -p "$QUEUE_DIR" 2>/dev/null || true
  local t="$QUEUE_DIR/${1}.$(_now).$$.${RANDOM}"
  printf '%s' "$$" > "$t" 2>/dev/null || true
  printf '%s' "$t"
}
_clean_tickets() {                        # drop tickets from dead pids or too old
  local f base epoch pid now; now="$(_now)"
  for f in "$QUEUE_DIR"/*; do
    [ -e "$f" ] || continue
    base="${f##*/}"; epoch="$(printf '%s' "$base" | cut -d. -f2)"
    pid="$(cat "$f" 2>/dev/null || true)"
    if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then rm -f "$f" 2>/dev/null || true; continue; fi
    if [ -n "$epoch" ] && [ "$(( now - epoch ))" -ge "$(( QUEUE_MAX_WAIT + 30 ))" ]; then rm -f "$f" 2>/dev/null || true; fi
  done
}
_front_is_me() {                          # $1=my ticket path
  local first
  first="$(ls -1 "$QUEUE_DIR" 2>/dev/null | LC_ALL=C sort | head -n1)"
  [ -n "$first" ] && [ "$QUEUE_DIR/$first" = "$1" ]
}
_break_lock_if_stale() {
  [ -d "$LOCK" ] || return 0
  local pid ts now; now="$(_now)"
  pid="$(cat "$LOCK/pid" 2>/dev/null || true)"
  ts="$(cat "$LOCK/ts" 2>/dev/null || true)"
  if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then rm -rf "$LOCK" 2>/dev/null || true; return 0; fi
  if [ -n "$ts" ] && [ "$(( now - ts ))" -ge "$LOCK_STALE" ]; then rm -rf "$LOCK" 2>/dev/null || true; fi
}
_cleanup_announce() {
  [ "${I_HOLD_LOCK:-0}" = "1" ] && { rm -rf "$LOCK" 2>/dev/null || true; I_HOLD_LOCK=0; }
  [ -n "${CUR_TICKET:-}" ] && { rm -f "$CUR_TICKET" 2>/dev/null || true; CUR_TICKET=""; }
}
_dbkey() { printf '%s' "$DBDIR/$(printf '%s' "$1" | tr -c 'A-Za-z0-9_.-' '_')"; }
_debounced() {                            # $1=key -> 0 (skip) if seen within window
  [ "${DEBOUNCE:-0}" -gt 0 ] 2>/dev/null || return 1
  local kf last now; now="$(_now)"
  kf="$(_dbkey "$1")"
  last="$(cat "$kf" 2>/dev/null || true)"     # timestamp stored as content (portable)
  case "$last" in ''|*[!0-9]*) return 1 ;; esac
  [ "$(( now - last ))" -lt "$DEBOUNCE" ]
}
_mark_debounce() {
  [ "${DEBOUNCE:-0}" -gt 0 ] 2>/dev/null || return 0
  mkdir -p "$DBDIR" 2>/dev/null || true
  printf '%s' "$(_now)" > "$(_dbkey "$1")" 2>/dev/null || true
}

# announce <text> <voice> <priority> <dedup-key>
announce() {
  local text="$1" voice="$2" prio="$3" key="$4" start now
  [ -n "$text" ] || return 0
  if _debounced "$key"; then log "debounced: $key"; return 0; fi

  CUR_TICKET="$(_enqueue "$prio")"; I_HOLD_LOCK=0
  trap _cleanup_announce EXIT INT TERM
  start="$(_now)"
  while :; do
    _clean_tickets
    _break_lock_if_stale
    if _front_is_me "$CUR_TICKET" && mkdir "$LOCK" 2>/dev/null; then
      I_HOLD_LOCK=1
      printf '%s' "$$"      > "$LOCK/pid" 2>/dev/null || true
      printf '%s' "$(_now)" > "$LOCK/ts"  2>/dev/null || true
      log "speak [$prio] $text"
      speak "$text" "$voice"
      _mark_debounce "$key"
      _cleanup_announce
      trap - EXIT INT TERM
      return 0
    fi
    now="$(_now)"
    if [ "$(( now - start ))" -ge "$QUEUE_MAX_WAIT" ]; then
      _cleanup_announce; trap - EXIT INT TERM
      log "queue wait > ${QUEUE_MAX_WAIT}s, dropped: $text"
      return 1
    fi
    sleep "0.$(( (RANDOM % 3) + 2 ))"     # 0.2–0.4s poll w/ jitter
  done
}

# ---------------------------------------------------------------------------
# per-event friendly text
# ---------------------------------------------------------------------------
friendly_error() {
  case "$1" in
    rate_limit) echo "rate limited";;
    overloaded) echo "the service is overloaded";;
    authentication_failed) echo "authentication failed";;
    oauth_org_not_allowed) echo "an authorization problem";;
    billing_error) echo "a billing error";;
    invalid_request) echo "an invalid request";;
    model_not_found) echo "the model was not found";;
    server_error) echo "a server error";;
    max_output_tokens) echo "the output length limit";;
    "") echo "an error";;
    *) echo "an error, $1";;
  esac
}
friendly_notif() {
  case "$1" in
    permission_prompt) echo "needs your permission";;
    idle_prompt) echo "is waiting for you";;
    agent_needs_input) echo "needs your input";;
    elicitation_dialog) echo "needs some input";;
    *) echo "needs your attention";;
  esac
}
_in_list() { case " $2 " in *" $1 "*) return 0;; *) return 1;; esac; }

# ---------------------------------------------------------------------------
# the detached worker
# ---------------------------------------------------------------------------
worker() {
  local json_file="$1" input event cwd transcript
  local last agent_id agent_type ntype etype src trig
  local category summary want_task voice prio cue text key
  input="$(cat "$json_file" 2>/dev/null || echo '{}')"

  if ! command -v jq >/dev/null 2>&1; then
    announce "Claude finished." "$(voice_for done)" "$(priority_for done)" "nojq"
    return 0
  fi

  event="${EVENT_OVERRIDE:-$(printf '%s' "$input" | jq -r '.hook_event_name // "Stop"' 2>/dev/null)}"
  cwd="$(printf '%s' "$input"        | jq -r '.cwd // empty'             2>/dev/null)"
  transcript="$(printf '%s' "$input" | jq -r '.transcript_path // empty' 2>/dev/null)"

  category="done"; summary=""; want_task=1

  case "$event" in
    Stop)
      last="$(printf '%s' "$input" | jq -r '.last_assistant_message // empty' 2>/dev/null)"
      agent_id="$(printf '%s' "$input" | jq -r '.agent_id // empty' 2>/dev/null)"
      if [ -n "$agent_id" ] && [ "${CLAUDE_TTS_ANNOUNCE_SUBAGENTS:-0}" != "1" ]; then
        log "skip subagent stop on Stop event ($agent_id)"; return 0
      fi
      category="done"; want_task=1
      if [ -z "$last" ]; then summary="Claude finished."; else summary="$(make_summary "$last")"; fi
      ;;
    SubagentStop)
      [ "${CLAUDE_TTS_ANNOUNCE_SUBAGENTS:-0}" = "1" ] || { log "SubagentStop off"; return 0; }
      agent_type="$(printf '%s' "$input" | jq -r '.agent_type // "subagent"' 2>/dev/null)"
      last="$(printf '%s' "$input" | jq -r '.last_assistant_message // empty' 2>/dev/null)"
      category="subagent"; want_task=0
      if [ -n "$last" ]; then summary="$agent_type subagent: $(make_summary "$last")"
      else summary="$agent_type subagent finished."; fi
      ;;
    StopFailure)
      etype="$(printf '%s' "$input" | jq -r '.error_type // empty' 2>/dev/null)"
      category="failure"; want_task=0
      summary="stopped, $(friendly_error "$etype")."
      ;;
    Notification)
      ntype="$(printf '%s' "$input" | jq -r '.notification_type // empty' 2>/dev/null)"
      _in_list "$ntype" "$NOTIFY_TYPES" || { log "skip notification type: $ntype"; return 0; }
      category="needsyou"; want_task=0
      summary="$(printf '%s' "$input" | jq -r '.message // empty' 2>/dev/null | clean_text | trim)"
      [ -n "$summary" ] || summary="Claude $(friendly_notif "$ntype")."
      ;;
    PreCompact)
      [ "${CLAUDE_TTS_ANNOUNCE_PRECOMPACT:-0}" = "1" ] || { log "PreCompact off"; return 0; }
      trig="$(printf '%s' "$input" | jq -r '.trigger // empty' 2>/dev/null)"
      [ "$trig" = "manual" ] && { log "skip manual precompact"; return 0; }
      category="headsup"; want_task=0; summary="compacting context."
      ;;
    SessionStart)
      [ "${CLAUDE_TTS_ANNOUNCE_SESSIONSTART:-0}" = "1" ] || { log "SessionStart off"; return 0; }
      src="$(printf '%s' "$input" | jq -r '.source // "started"' 2>/dev/null)"
      category="headsup"; want_task=0; summary="session $src."
      ;;
    *)
      last="$(printf '%s' "$input" | jq -r '.last_assistant_message // empty' 2>/dev/null)"
      category="done"; want_task=1
      if [ -z "$last" ]; then summary="Claude finished."; else summary="$(make_summary "$last")"; fi
      ;;
  esac

  [ -n "$summary" ] || return 0

  text="$(build_line "$cwd" "$transcript" "$summary" "$want_task")"
  cue="$(cue_for "$category")"
  [ -n "$cue" ] && text="$cue. $text"
  voice="$(voice_for "$category")"
  prio="$(priority_for "$category")"
  key="$event:$(project_label "$cwd")"

  announce "$text" "$voice" "$prio" "$key"
}

# ---------------------------------------------------------------------------
# arg parsing
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    __worker)     WORKER_MODE=1; WORKER_FILE="${2:-}"; shift 2 ;;
    --event)      EVENT_OVERRIDE="${2:-}"; shift 2 ;;
    --engine)     ENGINE="${2:-say}"; shift 2 ;;
    --rate)       RATE="${2:-}"; shift 2 ;;
    --summarizer) SUMMARIZER="${2:-auto}"; shift 2 ;;
    --max-words)  MAX_WORDS="${2:-18}"; shift 2 ;;
    --voice)      VOICE_OVERRIDE="${2:-}"; shift 2 ;;
    --test)       TEST_MODE=1; shift ;;
    --mute|--off)   ACTION=mute; shift ;;
    --unmute|--on)  ACTION=unmute; shift ;;
    --status)       ACTION=status; shift ;;
    *)            shift ;;
  esac
done

# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------
# mute management (no restart needed; each hook fire re-checks the flag file)
case "$ACTION" in
  mute)   mkdir -p "$(dirname "$MUTE_FILE")" 2>/dev/null || true; : > "$MUTE_FILE" 2>/dev/null || true
          echo "TTS announcements MUTED. Re-enable with:  bash \"$SELF\" --unmute"; exit 0 ;;
  unmute) rm -f "$MUTE_FILE" 2>/dev/null || true
          echo "TTS announcements ON."; exit 0 ;;
  status) if [ "${CLAUDE_TTS_DISABLE:-0}" = "1" ]; then echo "muted (CLAUDE_TTS_DISABLE=1)"
          elif [ -e "$MUTE_FILE" ]; then echo "muted (flag: $MUTE_FILE)"
          else echo "active (engine=$ENGINE)"; fi; exit 0 ;;
esac

if [ "$TEST_MODE" = "1" ]; then
  # Speak one sample per category through the queue (so you hear every voice,
  # one at a time). Uses the current directory for a realistic project prefix.
  for c in done failure needsyou headsup; do
    case "$c" in
      done)     s="finished the task and pushed the changes." ;;
      failure)  s="stopped, rate limited." ;;
      needsyou) s="needs your permission to run git push." ;;
      headsup)  s="compacting context." ;;
    esac
    t="$(build_line "$PWD" "" "$s" 0)"
    cu="$(cue_for "$c")"; [ -n "$cu" ] && t="$cu. $t"
    announce "$t" "$(voice_for "$c")" "$(priority_for "$c")" "test:$c"
  done
  exit 0
fi

if [ "$WORKER_MODE" = "1" ]; then
  worker "$WORKER_FILE"
  rm -f "$WORKER_FILE" 2>/dev/null || true
  exit 0
fi

# Kill switch: stay silent when disabled. Checked on every fire, so toggling the
# flag file takes effect immediately with no restart. --test still works.
if [ "${CLAUDE_TTS_DISABLE:-0}" = "1" ] || [ -e "$MUTE_FILE" ]; then exit 0; fi

# Normal hook invocation: read JSON, detach, return immediately.
INPUT="$(cat)"
TMP="$(mktemp "${TMPDIR:-/tmp}/claude-tts-json.XXXXXX" 2>/dev/null)" || exit 0
printf '%s' "$INPUT" > "$TMP"

export CLAUDE_TTS_ENGINE="$ENGINE" CLAUDE_TTS_RATE="$RATE" CLAUDE_TTS_SUMMARIZER="$SUMMARIZER" \
       CLAUDE_TTS_MAX_WORDS="$MAX_WORDS" CLAUDE_TTS_VOICE="$VOICE_OVERRIDE" \
       ANTHROPIC_TTS_MODEL="$ANTHROPIC_MODEL" OPENAI_TTS_MODEL="$OPENAI_MODEL" \
       ELEVENLABS_VOICE_ID="$ELEVEN_VOICE_ID" ELEVENLABS_MODEL="$ELEVEN_MODEL" \
       CLAUDE_TTS_LOG="$LOG"
[ -n "$EVENT_OVERRIDE" ] && export CLAUDE_TTS_EVENT="$EVENT_OVERRIDE"

nohup bash "$SELF" ${EVENT_OVERRIDE:+--event "$EVENT_OVERRIDE"} __worker "$TMP" >/dev/null 2>&1 &
disown 2>/dev/null || true
exit 0
TTS_SCRIPT_EOF
chmod +x "$HOOK"

CMD="bash \"$HOOK\""
mkdir -p "$CLAUDE_DIR"
[ -s "$SETTINGS" ] || echo '{}' > "$SETTINGS"

have_jq() { command -v jq >/dev/null 2>&1; }

echo "→ wiring events into: $SETTINGS"
if have_jq; then
  for EV in $EVENTS; do
    TMP="$(mktemp)"
    jq --arg cmd "$CMD" --arg ev "$EV" '
      .hooks = (.hooks // {}) | .hooks[$ev] = (.hooks[$ev] // []) |
      if (.hooks[$ev] | tostring | test("tts-announce-stop")) then .
      else .hooks[$ev] += [ { "hooks": [ { "type": "command", "command": $cmd } ] } ] end
    ' "$SETTINGS" > "$TMP" && mv "$TMP" "$SETTINGS"
    echo "  ✓ $EV"
  done
elif command -v python3 >/dev/null 2>&1; then
  python3 - "$SETTINGS" "$CMD" "$EVENTS" <<'PY'
import json,sys,os
path,cmd,events=sys.argv[1],sys.argv[2],sys.argv[3].split()
d=json.load(open(path)) if os.path.exists(path) and os.path.getsize(path) else {}
h=d.setdefault("hooks",{})
for ev in events:
    a=h.setdefault(ev,[])
    if "tts-announce-stop" not in json.dumps(a):
        a.append({"hooks":[{"type":"command","command":cmd}]})
json.dump(d,open(path,"w"),indent=2); open(path,"a").write("\n")
print("  ✓ "+", ".join(events))
PY
else
  echo "ERROR: need jq or python3 to edit settings.json" >&2; exit 1
fi

if [ "$WANT_EL" = "1" ]; then
  echo "→ configuring ElevenLabs (engine + voice) in settings.json env"
  if have_jq; then
    TMP="$(mktemp)"
    jq --arg vid "$EL_VOICE_ID" --arg key "${ELEVENLABS_API_KEY:-}" '
      .env = (.env // {}) |
      .env.CLAUDE_TTS_ENGINE = "elevenlabs" |
      .env.ELEVENLABS_VOICE_ID = $vid |
      (if $key != "" then .env.ELEVENLABS_API_KEY = $key else . end)
    ' "$SETTINGS" > "$TMP" && mv "$TMP" "$SETTINGS"
  else
    python3 - "$SETTINGS" "$EL_VOICE_ID" "${ELEVENLABS_API_KEY:-}" <<'PY'
import json,sys,os
path,vid,key=sys.argv[1],sys.argv[2],sys.argv[3]
d=json.load(open(path)) if os.path.exists(path) and os.path.getsize(path) else {}
env=d.setdefault("env",{})
env["CLAUDE_TTS_ENGINE"]="elevenlabs"; env["ELEVENLABS_VOICE_ID"]=vid
if key: env["ELEVENLABS_API_KEY"]=key
json.dump(d,open(path,"w"),indent=2); open(path,"a").write("\n")
PY
  fi
  echo "  ✓ engine=elevenlabs voice=$EL_VOICE_ID"
  [ -n "${ELEVENLABS_API_KEY:-}" ] && echo "  ✓ API key stored in settings.json env" \
    || echo "  NOTE: no ELEVENLABS_API_KEY given — add it to settings.json env or your shell profile."
fi

echo
echo "✅ Installed. Restart Claude Code (or start a new session) so it reloads settings."
echo "   Test now:   bash \"$HOOK\" --test"
echo "   Mute/unmute (no restart):   bash \"$HOOK\" --mute   |   --unmute"
if [ "$WANT_EL" = "1" ]; then
  echo "   Engine: ElevenLabs, voice $EL_VOICE_ID (model eleven_flash_v2_5)."
  echo "   If the API rejects the voice, add it to your ElevenLabs account, then retry."
fi
