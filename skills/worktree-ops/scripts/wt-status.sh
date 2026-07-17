#!/usr/bin/env bash
# Inventory every worktree: branch, base divergence, dirty/unpushed, test-DB
# presence, migration range, and cross-worktree migration collisions.
# Usage: wt-status.sh [--json]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wt-common.sh
. "$HERE/wt-common.sh"

JSON=0; [ "${1:-}" = "--json" ] && JSON=1
BASE="$(wt_base_branch)"

# Collect worktree paths from porcelain output.
paths=()
while IFS= read -r line; do
  case "$line" in
    worktree\ *) paths+=("${line#worktree }") ;;
  esac
done < <(git worktree list --porcelain)

# First pass: record each worktree's max migration number to detect collisions.
declare -a maxnums
i=0
for p in "${paths[@]}"; do
  mdir="$(wt_migrations_dir "$p" 2>/dev/null || true)"
  if [ -n "$mdir" ]; then maxnums[$i]="$(wt_max_migration_in_dir "$mdir")"; else maxnums[$i]=-1; fi
  i=$((i+1))
done

# Count how many worktrees share each max number (>1 with the same "next" collides).
collision_for() {
  local n="$1"; local c=0
  [ "$n" -lt 0 ] && { echo 0; return; }
  for m in "${maxnums[@]}"; do [ "$m" = "$n" ] && c=$((c+1)); done
  echo "$c"
}

emit_row_json() { # path branch ahead behind dirty unpushed hasdb maxnum collides
  printf '{"path":"%s","branch":"%s","ahead":%s,"behind":%s,"dirty":%s,"unpushed":%s,"test_db":"%s","migration_max":%s,"next_migration":%s,"collides":%s}' \
    "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9" "${10}"
}

[ "$JSON" = 1 ] && echo -n '['
printed=0
i=0
for p in "${paths[@]}"; do
  branch="$(git -C "$p" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '(detached)')"
  # ahead/behind vs base
  ahead=0; behind=0
  if git -C "$p" rev-parse --verify -q "$BASE" >/dev/null 2>&1; then
    read -r ahead behind < <(git -C "$p" rev-list --left-right --count "HEAD...$BASE" 2>/dev/null | awk '{print $1" "$2}') || true
    ahead="${ahead:-0}"; behind="${behind:-0}"
  fi
  dirty=false; [ -n "$(git -C "$p" status --porcelain 2>/dev/null)" ] && dirty=true
  # unpushed: commits on HEAD not on any remote-tracking branch
  unpushed=false
  upstream="$(git -C "$p" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
  if [ -n "$upstream" ]; then
    uc="$(git -C "$p" rev-list --count "$upstream..HEAD" 2>/dev/null || echo 0)"
    [ "${uc:-0}" -gt 0 ] && unpushed=true
  else
    unpushed=true  # no upstream at all
  fi
  dbname="$(wt_db_name "$p")"
  hasdb="no"
  if command -v psql >/dev/null 2>&1; then
    if psql "$(wt_pg_base_url)/postgres" -tAc "SELECT 1 FROM pg_database WHERE datname='$dbname'" 2>/dev/null | grep -q 1; then
      hasdb="yes"
    fi
  else
    hasdb="?"
  fi
  maxn="${maxnums[$i]}"
  nextn=$((maxn + 1)); [ "$maxn" -lt 0 ] && nextn=0
  ccount="$(collision_for "$maxn")"
  collides=false; [ "$ccount" -gt 1 ] && collides=true

  if [ "$JSON" = 1 ]; then
    [ "$printed" = 1 ] && echo -n ','
    emit_row_json "$p" "$branch" "$ahead" "$behind" "$dirty" "$unpushed" "$hasdb" "$maxn" "$nextn" "$collides"
    printed=1
  else
    flags=""
    [ "$dirty" = true ] && flags="${flags}dirty "
    [ "$unpushed" = true ] && flags="${flags}unpushed "
    [ "$collides" = true ] && flags="${flags}⚠collides(next=$nextn) "
    printf '• %s\n    branch=%s  base(%s)=+%s/-%s  test_db=%s  migr_max=%s  %s\n' \
      "$p" "$branch" "$BASE" "$ahead" "$behind" "$hasdb" "$maxn" "$flags"
  fi
  i=$((i+1))
done
[ "$JSON" = 1 ] && echo ']'
exit 0
