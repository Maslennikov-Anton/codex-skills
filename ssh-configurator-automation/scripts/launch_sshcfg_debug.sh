#!/usr/bin/env bash
set -euo pipefail

PORT="${SSHCFG_CDP_PORT:-9222}"
USER_DATA_DIR="${SSHCFG_USER_DATA_DIR:-/tmp/sshcfg-automation}"

exec /usr/lib/ssh-configurator/ssh-configurator \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$USER_DATA_DIR"
