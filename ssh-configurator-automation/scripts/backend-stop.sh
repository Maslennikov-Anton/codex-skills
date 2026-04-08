#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${SSHCFG_VM_DOMAIN:-plc1}"
SHUTDOWN_WAIT_SECONDS="${SSHCFG_VM_SHUTDOWN_WAIT_SECONDS:-20}"

domain_state() {
  virsh domstate "$DOMAIN" 2>/dev/null | tr -d '\r' | xargs
}

wait_for_shutdown() {
  local remaining="$SHUTDOWN_WAIT_SECONDS"
  while (( remaining > 0 )); do
    if [[ "$(domain_state)" != "running" ]]; then
      return 0
    fi
    sleep 1
    ((remaining--))
  done
  return 1
}

if [[ "$(domain_state)" == "running" ]]; then
  virsh shutdown "$DOMAIN" >/dev/null || true
  if ! wait_for_shutdown; then
    virsh destroy "$DOMAIN" >/dev/null
  fi
fi

echo "domain=$DOMAIN"
echo "state=$(domain_state)"
