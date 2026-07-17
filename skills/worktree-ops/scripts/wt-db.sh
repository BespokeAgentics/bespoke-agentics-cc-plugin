#!/usr/bin/env bash
# Manage a worktree's ISOLATED local Postgres database.
# The isolated DB is ALWAYS local + per-worktree; destructive actions never
# resolve to the primary DATABASE_URL (see wt_assert_not_production).
# Usage: wt-db.sh <ensure-server|provision|migrate|seed|reset|url|drop|status> [worktree-path]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wt-common.sh
. "$HERE/wt-common.sh"

ACTION="${1:-status}"
WT="${2:-$(wt_toplevel)}"
DBNAME="$(wt_db_name "$WT")"
DBURL="$(wt_db_url "$WT")"
ADMINURL="$(wt_pg_base_url)/postgres"

need_psql() { command -v psql >/dev/null 2>&1 || { echo "psql not found on PATH (brew install libpq)."; exit 1; }; }

ensure_server() {
  if psql "$ADMINURL" -tAc 'SELECT 1' >/dev/null 2>&1; then
    echo "✓ local Postgres reachable at $(wt_pg_base_url)"
    return 0
  fi
  echo "… local Postgres not reachable; attempting to start one"
  # Prefer the repo's docker-compose if it defines a postgres service.
  local compose="$WT/infra/docker-compose.yml"
  if command -v docker >/dev/null 2>&1 && [ -f "$compose" ] && grep -qiE 'image:\s*.*postgres' "$compose"; then
    docker compose -f "$compose" up -d 2>/dev/null || docker-compose -f "$compose" up -d
  elif command -v brew >/dev/null 2>&1 && brew services list 2>/dev/null | grep -qi postgres; then
    brew services start "$(brew services list | awk '/postgres/{print $1; exit}')"
  else
    echo "No local Postgres and no way to start one automatically."
    echo "Start one, e.g.:  docker run -d --name wt-pg -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16"
    echo "Then re-run. (Override the target with WT_PG_BASE_URL.)"
    exit 1
  fi
  # wait for readiness
  for _ in $(seq 1 30); do
    psql "$ADMINURL" -tAc 'SELECT 1' >/dev/null 2>&1 && { echo "✓ Postgres up"; return 0; }
    sleep 1
  done
  echo "Postgres did not become ready in time."; exit 1
}

# Write/replace a KEY in the worktree's .env.local without disturbing other lines.
set_env_local() { # key value
  local env="$WT/.env.local"; local key="$1"; local val="$2"
  touch "$env"
  if grep -qE "^${key}=" "$env"; then
    # portable in-place edit
    local tmp; tmp="$(mktemp)"
    grep -vE "^${key}=" "$env" > "$tmp"
    printf '%s=%s\n' "$key" "$val" >> "$tmp"
    mv "$tmp" "$env"
  else
    printf '%s=%s\n' "$key" "$val" >> "$env"
  fi
}

wire_env() {
  # Point the app + migrator + tests at the isolated DB. This is what makes
  # `bun run dev` in this worktree unable to touch the shared dev database.
  set_env_local DATABASE_URL "$DBURL"
  set_env_local MIGRATION_DATABASE_URL "$DBURL"
  set_env_local TEST_DATABASE_URL "$DBURL"
  echo "✓ wired $WT/.env.local -> $DBNAME"
}

provision() {
  need_psql; ensure_server
  if psql "$ADMINURL" -tAc "SELECT 1 FROM pg_database WHERE datname='$DBNAME'" | grep -q 1; then
    echo "✓ database already exists: $DBNAME"
  else
    createdb "$(wt_pg_base_url)/$DBNAME" 2>/dev/null || psql "$ADMINURL" -c "CREATE DATABASE \"$DBNAME\""
    echo "✓ created database: $DBNAME"
  fi
  wire_env
}

migrate() {
  need_psql
  local shell_dir="$WT/apps/shell"
  [ -d "$shell_dir" ] || shell_dir="$WT"
  echo "→ migrating isolated DB ($DBNAME) via drizzle-kit"
  ( cd "$shell_dir" && MIGRATION_DATABASE_URL="$DBURL" DATABASE_URL="$DBURL" bunx drizzle-kit migrate )
}

seed() {
  local shell_dir="$WT/apps/shell"
  [ -d "$shell_dir" ] || { echo "no apps/shell; skip seed"; return 0; }
  echo "→ seeding isolated DB ($DBNAME)"
  ( cd "$shell_dir" && DATABASE_URL="$DBURL" POSTGRES_SEED_ALLOWED=1 bun run db:seed )
}

reset() {
  wt_assert_not_production "$DBURL"
  local shell_dir="$WT/apps/shell"
  [ -d "$shell_dir" ] || { echo "no apps/shell; skip reset"; return 0; }
  echo "→ resetting isolated DB ($DBNAME) via repo db:test:reset"
  ( cd "$shell_dir" && TEST_DATABASE_URL="$DBURL" DATABASE_URL="$DBURL" POSTGRES_RESET_ALLOWED=1 bun run db:test:reset )
}

drop() {
  need_psql
  wt_assert_not_production "$DBURL"
  psql "$ADMINURL" -c "DROP DATABASE IF EXISTS \"$DBNAME\" WITH (FORCE)" >/dev/null 2>&1 \
    || psql "$ADMINURL" -c "DROP DATABASE IF EXISTS \"$DBNAME\""
  echo "✓ dropped database: $DBNAME"
}

status() {
  need_psql
  if psql "$ADMINURL" -tAc "SELECT 1 FROM pg_database WHERE datname='$DBNAME'" 2>/dev/null | grep -q 1; then
    echo "provisioned: yes"
  else
    echo "provisioned: no"
  fi
  echo "db_name: $DBNAME"
  echo "url: $DBURL"
}

case "$ACTION" in
  ensure-server) ensure_server ;;
  provision)     provision ;;
  migrate)       migrate ;;
  seed)          seed ;;
  reset)         reset ;;
  url)           echo "$DBURL" ;;
  drop)          drop ;;
  status)        status ;;
  *) echo "unknown action: $ACTION"; exit 2 ;;
esac
