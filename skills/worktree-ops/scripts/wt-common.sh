#!/usr/bin/env bash
# Shared helpers for worktree-ops scripts. Source this; don't run it directly.
# All logic keys off the git COMMON dir (shared by every worktree of a repo),
# which is where cross-worktree coordination state lives.
set -euo pipefail

wt_common_dir() { git rev-parse --git-common-dir 2>/dev/null; }
wt_toplevel()   { git rev-parse --show-toplevel 2>/dev/null; }

# The ledger + reservation state live under the shared common dir so every
# worktree sees the same file. (worktree-ops/ is created lazily.)
wt_state_dir() {
  local common; common="$(wt_common_dir)" || return 1
  # git-common-dir may be relative to CWD; resolve it.
  case "$common" in
    /*) : ;;
    *)  common="$(cd "$common" && pwd)" ;;
  esac
  local d="$common/worktree-ops"
  mkdir -p "$d"
  printf '%s\n' "$d"
}

# Line-based ledger: one row per reservation -> "reserved_number<TAB>path<TAB>branch"
wt_ledger_file() {
  local f; f="$(wt_state_dir)/migration-ledger.tsv"
  [ -f "$f" ] || : > "$f"
  printf '%s\n' "$f"
}

# Base branch to diverge/merge against. Override with WT_BASE_BRANCH.
wt_base_branch() { printf '%s\n' "${WT_BASE_BRANCH:-production}"; }

# Local Postgres base URL (no trailing db name). Override with WT_PG_BASE_URL.
# Default targets a conventional local server, NOT the app's Azure DATABASE_URL.
wt_pg_base_url() { printf '%s\n' "${WT_PG_BASE_URL:-postgres://postgres:postgres@localhost:5432}"; }

# Derive a safe, unique local DB name from a worktree path.
#   .../CUMULATIVE_OS-foundry-platform-port -> cos_wt_foundry_platform_port
wt_db_name() {
  local path="${1:-$(wt_toplevel)}"
  local base; base="$(basename "$path")"
  local slug; slug="$(printf '%s' "$base" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '_' | sed -E 's/_+/_/g; s/^_//; s/_$//')"
  # Strip a leading repo-name prefix if present, keep it readable, cap length.
  printf 'cos_wt_%s\n' "${slug:0:48}"
}

wt_db_url() {
  local path="${1:-$(wt_toplevel)}"
  printf '%s/%s\n' "$(wt_pg_base_url)" "$(wt_db_name "$path")"
}

# Guardrail: refuse anything that looks like a production/primary DB.
wt_assert_not_production() {
  local target="$1"
  if printf '%s' "$target" | grep -qiE 'prod|production'; then
    echo "GUARDRAIL: refusing to operate on a production-looking target: $target" >&2
    return 1
  fi
  # Never allow a destructive op to resolve to the app's live DATABASE_URL host.
  if [ -n "${DATABASE_URL:-}" ] && [ "$target" = "${DATABASE_URL}" ]; then
    echo "GUARDRAIL: target equals the primary DATABASE_URL. Refusing." >&2
    return 1
  fi
  return 0
}

# Highest migration number present in a directory of NNNN_*.sql files. Echoes -1 if none.
wt_max_migration_in_dir() {
  local dir="$1"
  local max=-1 n
  [ -d "$dir" ] || { echo -1; return 0; }
  for f in "$dir"/[0-9][0-9][0-9][0-9]_*.sql; do
    [ -e "$f" ] || continue
    n="$(basename "$f" | cut -c1-4)"
    n=$((10#$n))
    [ "$n" -gt "$max" ] && max=$n
  done
  echo "$max"
}

# Locate the drizzle migrations dir for a worktree (first match wins).
wt_migrations_dir() {
  local root="${1:-$(wt_toplevel)}"
  for d in \
    "$root/apps/shell/drizzle" \
    "$root/apps/shell/migrations" \
    "$root/drizzle" \
    "$root/migrations"; do
    [ -d "$d" ] && { printf '%s\n' "$d"; return 0; }
  done
  return 1
}
