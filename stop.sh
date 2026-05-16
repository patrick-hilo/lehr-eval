#!/usr/bin/env bash
# Lehr-Evaluation: stoppt den von start.sh gestarteten Server.

set -euo pipefail

cd "$(dirname "$0")"

PID_FILE=".lehr-eval.pid"

cyan="\033[36m"
green="\033[32m"
yellow="\033[33m"
red="\033[31m"
reset="\033[0m"

info() { printf "${cyan}→${reset} %s\n" "$*"; }
ok()   { printf "${green}✓${reset} %s\n" "$*"; }
warn() { printf "${yellow}!${reset} %s\n" "$*"; }
fail() { printf "${red}✗${reset} %s\n" "$*" >&2; }

stopped_any=0

if [ -f "$PID_FILE" ]; then
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    info "Stoppe Server (PID $pid)..."
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      if ! kill -0 "$pid" 2>/dev/null; then break; fi
      sleep 0.2
    done
    if kill -0 "$pid" 2>/dev/null; then
      warn "Prozess reagiert nicht — sende SIGKILL."
      kill -9 "$pid" 2>/dev/null || true
    fi
    ok "Server gestoppt."
    stopped_any=1
  fi
  rm -f "$PID_FILE"
fi

# Fallback: alle uvicorn-Prozesse fuer dieses Repo abraeumen
matches="$(pgrep -f "uvicorn.*lehr_eval.app:create_app" 2>/dev/null || true)"
if [ -n "$matches" ]; then
  info "Raeume verbleibende uvicorn-Prozesse ab: $matches"
  pkill -f "uvicorn.*lehr_eval.app:create_app" 2>/dev/null || true
  stopped_any=1
fi

if [ "$stopped_any" = 0 ]; then
  warn "Es lief kein Server."
fi
