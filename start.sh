#!/usr/bin/env bash
# Lehr-Evaluation: one-command Server-Start + Admin-Panel oeffnen.
#
# Usage:
#   ./start.sh
#
# Optional env vars:
#   LEHR_EVAL_PORT             (default: 8000)
#   LEHR_EVAL_ADMIN_PASSWORD   (default: secret)

set -euo pipefail

cd "$(dirname "$0")"

PORT="${LEHR_EVAL_PORT:-8000}"
HOST="127.0.0.1"
URL="http://${HOST}:${PORT}/admin/login"
PASSWORD="${LEHR_EVAL_ADMIN_PASSWORD:-secret}"
LOG_FILE=".lehr-eval.log"
PID_FILE=".lehr-eval.pid"

cyan="\033[36m"
green="\033[32m"
yellow="\033[33m"
red="\033[31m"
bold="\033[1m"
reset="\033[0m"

info()  { printf "${cyan}→${reset} %s\n" "$*"; }
ok()    { printf "${green}✓${reset} %s\n" "$*"; }
warn()  { printf "${yellow}!${reset} %s\n" "$*"; }
fail()  { printf "${red}✗${reset} %s\n" "$*" >&2; }

# --- Pre-checks ---
if ! command -v uv >/dev/null 2>&1; then
  fail "'uv' wurde nicht gefunden."
  echo "   Installiere uv:"
  echo "     macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "     Windows:     powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\""
  exit 1
fi

# --- Stop a previous instance, if any ---
if [ -f "$PID_FILE" ]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
    warn "Frueherer Server lief noch (PID $old_pid) — wird gestoppt."
    kill "$old_pid" 2>/dev/null || true
    sleep 1
  fi
  rm -f "$PID_FILE"
fi

# Defensive: auch verwaiste lehr_eval-uvicorn-Prozesse abraeumen,
# z. B. wenn frueher manuell gestartet wurde und der PID-File fehlt.
stale="$(pgrep -f "uvicorn.*lehr_eval.app:create_app" 2>/dev/null || true)"
if [ -n "$stale" ]; then
  warn "Stale lehr_eval-Server gefunden ($stale) — werden gestoppt."
  pkill -f "uvicorn.*lehr_eval.app:create_app" 2>/dev/null || true
  sleep 1
fi

# Port-Check: ist Port noch belegt, schlage anderen Port vor.
if command -v lsof >/dev/null 2>&1; then
  occupant="$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null | head -1 || true)"
  if [ -n "$occupant" ]; then
    fail "Port $PORT ist von Prozess $occupant belegt."
    echo "   Setze einen anderen Port:  LEHR_EVAL_PORT=8001 ./start.sh"
    echo "   Oder beende den Prozess:    kill $occupant"
    exit 1
  fi
fi

# --- Sync deps ---
info "Installiere Abhaengigkeiten via 'uv sync'..."
uv sync --quiet

# --- Start server ---
info "Starte Server auf ${URL}..."
LEHR_EVAL_ADMIN_PASSWORD="$PASSWORD" \
LEHR_EVAL_BASE_URL="http://${HOST}:${PORT}" \
LEHR_EVAL_DATABASE_PATH="${LEHR_EVAL_DATABASE_PATH:-data/lehr-eval.db}" \
  uv run uvicorn --app-dir src lehr_eval.app:create_app \
    --factory --host "$HOST" --port "$PORT" \
    > "$LOG_FILE" 2>&1 &

SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"

# --- Wait for it to come up ---
for _ in $(seq 1 25); do
  if curl -sf "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    fail "Server konnte nicht starten. Logs in $LOG_FILE:"
    tail -n 20 "$LOG_FILE" || true
    rm -f "$PID_FILE"
    exit 1
  fi
  sleep 0.3
done

ok "Server laeuft (PID $SERVER_PID)."
echo
printf "  ${bold}Admin-Login:${reset} %s\n" "$URL"
printf "  ${bold}Passwort:${reset}    %s\n" "$PASSWORD"
echo
printf "  Logs: %s    Stop: ./stop.sh\n" "$LOG_FILE"
echo

# --- Open browser ---
if command -v open >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
else
  warn "Konnte keinen Browser oeffnen — bitte manuell aufrufen."
fi
