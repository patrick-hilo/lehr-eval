#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${DB_PATH:-/var/lib/lehr-eval/eval.db}"
BACKUP_DIR="${BACKUP_DIR:?set BACKUP_DIR to separate school storage}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DESTINATION="${BACKUP_DIR}/eval-${STAMP}.db"
TEMP_DESTINATION="${DESTINATION}.tmp"

if [[ ! -f "$DB_PATH" ]]; then
  echo "SQLite database not found: ${DB_PATH}" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

sqlite_quote() {
  printf "%s" "$1" | sed 's/"/""/g'
}

rm -f "$TEMP_DESTINATION"
sqlite3 "$DB_PATH" ".backup \"$(sqlite_quote "$TEMP_DESTINATION")\""
CHECK_RESULT="$(sqlite3 "$TEMP_DESTINATION" "pragma integrity_check;")"
if [[ "$CHECK_RESULT" != "ok" ]]; then
  rm -f "$TEMP_DESTINATION"
  echo "SQLite backup integrity_check failed: ${CHECK_RESULT}" >&2
  exit 1
fi
mv "$TEMP_DESTINATION" "$DESTINATION"
