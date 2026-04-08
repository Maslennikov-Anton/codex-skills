#!/usr/bin/env bash
set -euo pipefail

PORT="${SSHCFG_CDP_PORT:-9222}"
PIDS="$(pgrep -f "/usr/lib/ssh-configurator/ssh-configurator.*--remote-debugging-port=${PORT}" || true)"

if [[ -n "$PIDS" ]]; then
  kill $PIDS
  sleep 1
fi

REMAINING="$(pgrep -f "/usr/lib/ssh-configurator/ssh-configurator.*--remote-debugging-port=${PORT}" || true)"

if [[ -n "$REMAINING" ]]; then
  kill -9 $REMAINING
fi

FINAL="$(pgrep -f "/usr/lib/ssh-configurator/ssh-configurator.*--remote-debugging-port=${PORT}" || true)"
if [[ -n "$FINAL" ]]; then
  echo "failed_to_close port=$PORT pids=$FINAL" >&2
  exit 1
fi

echo "closed_debug_port=$PORT"
