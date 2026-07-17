#!/usr/bin/env bash
# Cross-worktree Drizzle migration coordination.
# Ledger (shared git common dir) reserves globally-unique migration numbers so
# parallel branches don't both grab NNNN and collide at merge time.
# Usage: wt-migrations.sh <audit|reserve|claim|release> [worktree-path]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wt-common.sh
. "$HERE/wt-common.sh"

ACTION="${1:-audit}"
WT="${2:-$(wt_toplevel)}"
LEDGER="$(wt_ledger_file)"
BASE="$(wt_base_branch)"

# Highest number that exists on disk across ALL worktrees OR is reserved in the ledger.
global_high() {
  local hi=-1 n
  while IFS= read -r line; do
    case "$line" in worktree\ *) p="${line#worktree }"
      md="$(wt_migrations_dir "$p" 2>/dev/null || true)"
      [ -n "$md" ] && { n="$(wt_max_migration_in_dir "$md")"; [ "$n" -gt "$hi" ] && hi=$n; } ;;
    esac
  done < <(git worktree list --porcelain)
  # include ledger reservations
  if [ -s "$LEDGER" ]; then
    while IFS=$'\t' read -r rnum rpath rbranch; do
      [ -n "${rnum:-}" ] && [ "$rnum" -gt "$hi" ] 2>/dev/null && hi=$rnum
    done < "$LEDGER"
  fi
  echo "$hi"
}

ledger_get() { # path -> reserved number (empty if none)
  local path="$1"
  [ -s "$LEDGER" ] || return 0
  awk -F'\t' -v p="$path" '$2==p{print $1}' "$LEDGER" | tail -1
}

ledger_remove() { # path
  local path="$1" tmp
  [ -s "$LEDGER" ] || return 0
  tmp="$(mktemp)"
  awk -F'\t' -v p="$path" '$2!=p' "$LEDGER" > "$tmp"
  mv "$tmp" "$LEDGER"
}

reserve() {
  local existing; existing="$(ledger_get "$WT")"
  if [ -n "$existing" ]; then
    echo "$existing"; echo "(already reserved for $WT)" >&2; return 0
  fi
  local hi; hi="$(global_high)"
  local next=$((hi + 1))
  local branch; branch="$(git -C "$WT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
  printf '%04d\t%s\t%s\n' "$next" "$WT" "$branch" >> "$LEDGER"
  printf '%04d\n' "$next"
  echo "✓ reserved migration #$(printf '%04d' "$next") for $WT ($branch)" >&2
}

# Rename the most-recently-generated migration in this worktree to the reserved
# number and repair drizzle meta/_journal.json so the sequence stays contiguous.
claim() {
  local reserved; reserved="$(ledger_get "$WT")"
  [ -n "$reserved" ] || { echo "no reservation for $WT — run 'reserve' first" >&2; exit 1; }
  local md; md="$(wt_migrations_dir "$WT")" || { echo "no migrations dir" >&2; exit 1; }
  # newest NNNN_*.sql by number
  local newest; newest="$(ls -1 "$md"/[0-9][0-9][0-9][0-9]_*.sql 2>/dev/null | sort | tail -1)"
  [ -n "$newest" ] || { echo "no generated migration found in $md" >&2; exit 1; }
  local cur; cur="$(basename "$newest" | cut -c1-4)"
  if [ "$cur" = "$reserved" ]; then
    echo "✓ newest migration already at reserved #$reserved" ; return 0
  fi
  local rest; rest="$(basename "$newest" | cut -c5-)"   # _slug.sql
  local target="$md/${reserved}${rest}"
  echo "→ renaming $(basename "$newest") -> $(basename "$target")"
  git -C "$WT" mv "$newest" "$target" 2>/dev/null || mv "$newest" "$target"

  # Repair _journal.json: replace the idx/tag that referenced the old number.
  local journal="$md/meta/_journal.json"
  if [ -f "$journal" ]; then
    local oldtag newtag
    oldtag="$(basename "$newest" .sql)"
    newtag="$(basename "$target" .sql)"
    local tmp; tmp="$(mktemp)"
    sed "s/\"${oldtag}\"/\"${newtag}\"/g; s/\"idx\": *$((10#$cur))/\"idx\": $((10#$reserved))/g" "$journal" > "$tmp"
    mv "$tmp" "$journal"
    echo "✓ patched meta/_journal.json (tag + idx)"
    echo "  NOTE: verify the snapshot file in meta/ is renamed if drizzle keyed it by idx." >&2
  fi
  echo "✓ claimed reserved migration #$reserved"
}

audit() {
  echo "== Migration audit (base=$BASE) =="
  # gather (number, path, branch) rows for on-disk maxes
  local rows; rows="$(mktemp)"
  while IFS= read -r line; do
    case "$line" in worktree\ *) p="${line#worktree }"
      md="$(wt_migrations_dir "$p" 2>/dev/null || true)"
      [ -n "$md" ] || continue
      n="$(wt_max_migration_in_dir "$md")"
      br="$(git -C "$p" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
      printf '%s\t%s\t%s\n' "$n" "$p" "$br" >> "$rows" ;;
    esac
  done < <(git worktree list --porcelain)

  echo "-- highest migration number per worktree (ascending = suggested merge order) --"
  sort -n "$rows" | while IFS=$'\t' read -r n p br; do
    printf '  #%04d  %-40s  %s\n' "$n" "$br" "$p"
  done

  echo "-- collisions (same 'max' => both would generate the same next number) --"
  local collided=0
  cut -f1 "$rows" | sort -n | uniq -d | while read -r dup; do
    [ -z "$dup" ] && continue
    echo "  ⚠ number $dup shared by:"
    awk -F'\t' -v d="$dup" '$1==d{printf "      %s (%s)\n",$3,$2}' "$rows"
  done
  if ! cut -f1 "$rows" | sort -n | uniq -d | grep -q .; then
    echo "  none — every worktree sits at a distinct migration head."
  fi

  echo "-- ledger reservations --"
  if [ -s "$LEDGER" ]; then
    sort -n "$LEDGER" | while IFS=$'\t' read -r rn rp rb; do printf '  reserved #%s  %-30s  %s\n' "$rn" "$rb" "$rp"; done
  else
    echo "  (empty)"
  fi
  rm -f "$rows"
}

case "$ACTION" in
  audit)   audit ;;
  reserve) reserve ;;
  claim)   claim ;;
  release) ledger_remove "$WT"; echo "✓ released reservation for $WT" ;;
  *) echo "unknown action: $ACTION"; exit 2 ;;
esac
