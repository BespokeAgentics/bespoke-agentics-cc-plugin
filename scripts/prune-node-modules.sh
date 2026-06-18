#!/usr/bin/env bash
#
# prune-node-modules.sh — find & delete stale node_modules on macOS (BSD userland)
#
# Staleness unit: the PARENT directory of each node_modules ("the project").
# A node_modules is STALE if its parent's "last activity" is older than --days.
# last activity = max(
#     newest mtime of any file under parent EXCLUDING node_modules/.git/build-dirs,
#     git last-commit time (if parent is a git repo)
# )
#
# DEFAULT IS DRY-RUN. You must pass --apply (or --delete) to remove anything.

set -u
# No `set -e`: we continue past per-directory permission errors and report them.

# ---------------------------------------------------------------- Defaults
DEFAULT_DIR="$HOME/Documents/Projects"
ROOT_DIR="$DEFAULT_DIR"
DAYS=30
APPLY=0                 # 0 = dry-run (default), 1 = actually delete
USE_TRASH=0             # 0 = rm -rf (default), 1 = route through `trash`
LOG_FILE=""

# Directories whose mtimes do NOT count as "touched" (pruned from the scan).
PRUNE_NAMES=(node_modules .git dist build .next .nuxt .svelte-kit .turbo \
             coverage out .output .cache .parcel-cache)

# du / git / find guards. Prefer a real timeout binary if present.
TIMEOUT_BIN=""
for t in /opt/homebrew/bin/timeout /opt/homebrew/bin/gtimeout timeout gtimeout; do
  if command -v "$t" >/dev/null 2>&1; then TIMEOUT_BIN="$t"; break; fi
done
DU_TIMEOUT=60      # cap du -sk on one node_modules
SCAN_TIMEOUT=30    # cap the per-parent file scan

# ---------------------------------------------------------------- Helpers
prog=$(basename "$0")

usage() {
  cat <<EOF
$prog — find and delete stale node_modules directories (macOS / BSD)

USAGE:
  $prog [--dir PATH] [--days N] [--apply|--delete] [--trash] [--log FILE] [--help]

OPTIONS:
  --dir PATH    Root to scan.        (default: $DEFAULT_DIR)
  --days N      Staleness threshold. (default: $DAYS)
  --apply       Actually delete.     (default: DRY-RUN, deletes nothing)
  --delete      Alias for --apply.
  --trash       Use 'trash' (recoverable) instead of 'rm -rf' (permanent).
  --log FILE    Append a record of each deletion to FILE.
  --help        This help.

"Touched" = max( newest file mtime under the project excluding
node_modules/.git/build-output dirs, git last-commit time ).
Dry-run by default. Refuses to run on \$HOME or /. Never follows symlinks.
EOF
}

err()  { printf '%s\n' "$*" >&2; }
info() { printf '%s\n' "$*"; }
human_date() { date -r "$1" '+%Y-%m-%d %H:%M' 2>/dev/null || echo "?"; }

run_guarded() {  # run "$@" under a timeout if available
  local secs="$1"; shift
  if [ -n "$TIMEOUT_BIN" ]; then "$TIMEOUT_BIN" "$secs" "$@"; else "$@"; fi
}

kb_to_human() {
  awk -v k="$1" 'BEGIN{split("KB MB GB TB PB",u," ");i=1;v=k;
    while(v>=1024&&i<5){v/=1024;i++} printf("%.1f %s",v,u[i])}'
}

# Build the shared find prune expression from PRUNE_NAMES.
build_prune_expr() {
  PRUNE_EXPR=()
  local n
  for n in "${PRUNE_NAMES[@]}"; do PRUNE_EXPR+=( -name "$n" -prune -o ); done
}

# ---------------------------------------------------------------- Parse args
while [ $# -gt 0 ]; do
  case "$1" in
    --dir)    ROOT_DIR="${2:?--dir needs a value}"; shift 2 ;;
    --dir=*)  ROOT_DIR="${1#*=}"; shift ;;
    --days)   DAYS="${2:?--days needs a value}"; shift 2 ;;
    --days=*) DAYS="${1#*=}"; shift ;;
    --apply|--delete) APPLY=1; shift ;;
    --trash)  USE_TRASH=1; shift ;;
    --log)    LOG_FILE="${2:?--log needs a value}"; shift 2 ;;
    --log=*)  LOG_FILE="${1#*=}"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) err "Unknown argument: $1"; err "Try '$prog --help'."; exit 2 ;;
  esac
done

case "$DAYS" in ''|*[!0-9]*) err "ERROR: --days must be a non-negative integer."; exit 2 ;; esac

# ---------------------------------------------------------------- Safety checks
case "$ROOT_DIR" in "~"|"~/"*) ROOT_DIR="$HOME${ROOT_DIR#\~}";; esac
[ -d "$ROOT_DIR" ] || { err "ERROR: --dir not a directory: $ROOT_DIR"; exit 2; }
RESOLVED_DIR=$(cd "$ROOT_DIR" 2>/dev/null && pwd -P)
[ -n "$RESOLVED_DIR" ] || { err "ERROR: cannot cd into --dir: $ROOT_DIR"; exit 2; }
RESOLVED_HOME=$(cd "$HOME" 2>/dev/null && pwd -P)
if [ "$RESOLVED_DIR" = "/" ] || [ "$RESOLVED_DIR" = "$RESOLVED_HOME" ]; then
  err "ERROR: refusing to operate on '$RESOLVED_DIR' (it is / or \$HOME)."; exit 2
fi
ROOT_DIR="$RESOLVED_DIR"

TRASH_BIN=""
if [ "$USE_TRASH" -eq 1 ]; then
  TRASH_BIN=$(command -v trash || true)
  [ -n "$TRASH_BIN" ] || { err "ERROR: --trash requested but 'trash' not found."; exit 2; }
fi
if [ -n "$LOG_FILE" ]; then
  ( : >> "$LOG_FILE" ) 2>/dev/null || { err "ERROR: --log not writable: $LOG_FILE"; exit 2; }
fi

NOW=$(date +%s)
CUTOFF=$(( NOW - DAYS * 86400 ))
build_prune_expr

# ---------------------------------------------------------------- Banner
MODE="DRY-RUN (nothing will be deleted)"; [ "$APPLY" -eq 1 ] && MODE="APPLY (deletions WILL happen)"
DEL="rm -rf (permanent, frees space now)"; [ "$USE_TRASH" -eq 1 ] && DEL="trash (recoverable; frees space only when emptied)"
info "============================================================"
info "  node_modules pruner"
info "  Root:       $ROOT_DIR"
info "  Threshold:  $DAYS days  (cutoff = $(human_date "$CUTOFF"))"
info "  Mode:       $MODE"
info "  Delete via: $DEL"
[ -n "$LOG_FILE" ] && info "  Log:        $LOG_FILE"
[ -z "$TIMEOUT_BIN" ] && info "  (no timeout binary found; du/scan guards disabled)"
info "============================================================"; info ""

# ---------------------------------------------------------------- Staleness check
# echoes best-known activity epoch; exit 0 = STALE (delete), 1 = ACTIVE (skip)
parent_last_activity() {
  local parent="$1" git_ct=0 file_recent="" newest=0 f m
  if [ -e "$parent/.git" ]; then
    git_ct=$(run_guarded 10 git -C "$parent" log -1 --format=%ct 2>/dev/null || echo 0)
    case "$git_ct" in ''|*[!0-9]*) git_ct=0 ;; esac
  fi
  if [ "$git_ct" -ge "$CUTOFF" ]; then printf '%s' "$git_ct"; return 1; fi

  # Any non-pruned file newer than cutoff? (head closes pipe early; SCAN_TIMEOUT caps it)
  file_recent=$(run_guarded "$SCAN_TIMEOUT" \
    find "$parent" "${PRUNE_EXPR[@]}" -type f -newermt "@$CUTOFF" -print 2>/dev/null | head -1)
  if [ -n "$file_recent" ]; then
    if [ "$git_ct" -gt 0 ]; then printf '%s' "$git_ct"; else printf '%s' "$CUTOFF"; fi
    return 1
  fi

  # STALE: compute newest mtime for the report (runs only on the stale minority).
  while IFS= read -r -d '' f; do
    m=$(stat -f '%m' "$f" 2>/dev/null || echo 0); [ "$m" -gt "$newest" ] && newest="$m"
  done < <(run_guarded "$SCAN_TIMEOUT" \
    find "$parent" "${PRUNE_EXPR[@]}" -type f -print0 2>/dev/null)
  [ "$git_ct" -gt "$newest" ] && newest="$git_ct"
  printf '%s' "$newest"; return 0
}

# ---------------------------------------------------------------- Main loop
total_nm=0 stale_nm=0 active_nm=0 err_nm=0 freed_kb=0
declare -a ACTIVE_REPORT=() ERROR_REPORT=()

while IFS= read -r -d '' nm; do
  total_nm=$((total_nm+1)); parent=$(dirname "$nm")
  [ -d "$nm" ] || { err_nm=$((err_nm+1)); ERROR_REPORT+=("missing/unreadable: $nm"); continue; }

  activity=$(parent_last_activity "$parent"); status=$?
  if [ "$status" -ne 0 ]; then
    active_nm=$((active_nm+1)); ACTIVE_REPORT+=("$(human_date "$activity")  $parent"); continue
  fi

  size_kb=$(run_guarded "$DU_TIMEOUT" du -sk "$nm" 2>/dev/null | awk '{print $1}')
  case "$size_kb" in ''|*[!0-9]*) size_kb=0 ;; esac
  freed_kb=$((freed_kb+size_kb)); human=$(kb_to_human "$size_kb"); last=$(human_date "$activity")

  if [ "$APPLY" -eq 1 ]; then
    if [ "$USE_TRASH" -eq 1 ]; then
      if "$TRASH_BIN" -v "$nm" >/dev/null 2>&1; then
        info "TRASHED  [$human]  (last activity $last)  $nm"
        [ -n "$LOG_FILE" ] && printf '%s\tTRASHED\t%s\t%s\t%s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$human" "$last" "$nm" >> "$LOG_FILE"
      else err_nm=$((err_nm+1)); freed_kb=$((freed_kb-size_kb)); ERROR_REPORT+=("trash failed: $nm"); fi
    else
      if rm -rf -- "$nm" 2>/dev/null; then
        info "DELETED  [$human]  (last activity $last)  $nm"
        [ -n "$LOG_FILE" ] && printf '%s\tDELETED\t%s\t%s\t%s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$human" "$last" "$nm" >> "$LOG_FILE"
      else err_nm=$((err_nm+1)); freed_kb=$((freed_kb-size_kb)); ERROR_REPORT+=("rm -rf failed: $nm"); fi
    fi
  else
    info "WOULD DELETE  [$human]  (last activity $last)  $nm"
  fi
  stale_nm=$((stale_nm+1))
done < <(find "$ROOT_DIR" -type d -name node_modules -prune -print0 2>/dev/null)

# ---------------------------------------------------------------- Reports
if [ "${#ACTIVE_REPORT[@]}" -gt 0 ]; then
  info ""; info "------------------------------------------------------------"
  info "Skipped as RECENTLY ACTIVE (within $DAYS days):"
  printf '%s\n' "${ACTIVE_REPORT[@]}" | sort -r | sed 's/^/  /'
fi
if [ "${#ERROR_REPORT[@]}" -gt 0 ]; then
  info ""; info "------------------------------------------------------------"
  info "ERRORS / SKIPPED:"; printf '  %s\n' "${ERROR_REPORT[@]}"
fi
info ""; info "============================================================"
info "  SUMMARY"
info "  node_modules found:    $total_nm"
info "  stale (targeted):      $stale_nm"
info "  active (skipped):      $active_nm"
info "  errors/unreadable:     $err_nm"
if [ "$APPLY" -eq 1 ]; then
  info "  space freed:           $(kb_to_human "$freed_kb")"
else
  info "  space that WOULD free: $(kb_to_human "$freed_kb")"
  info ""; info "  DRY-RUN: nothing deleted. Re-run with --apply to delete."
fi
info "============================================================"
exit 0
