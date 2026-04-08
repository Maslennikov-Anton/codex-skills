#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${SSHCFG_VM_DOMAIN:-plc1}"
BASE_IMAGE="${SSHCFG_VM_BASE_IMAGE:-/home/ant/libvirtimages/vcont_plc.qcow2}"
OVERLAY_IMAGE="${SSHCFG_VM_OVERLAY_IMAGE:-/home/ant/libvirtimages/vcont_plc.plc1.overlay.qcow2}"
WORK_XML="${SSHCFG_VM_WORK_XML:-/tmp/${DOMAIN}.overlay.xml}"
REFERENCE_XML="${SSHCFG_VM_REFERENCE_XML:-/home/ant/codex-skills/ssh-configurator-automation/references/plc1-libvirt-overlay.xml}"
SHUTDOWN_WAIT_SECONDS="${SSHCFG_VM_SHUTDOWN_WAIT_SECONDS:-20}"

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "missing file: $path" >&2
    exit 1
  fi
}

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

rewrite_domain_xml_to_overlay() {
  virsh dumpxml "$DOMAIN" > "$WORK_XML"
  perl -0pi -e "s#(<disk type='file' device='disk'>.*?<source file=')([^']+)(')#\${1}$OVERLAY_IMAGE\${3}#s" "$WORK_XML"
}

stop_domain_if_needed() {
  if [[ "$(domain_state)" == "running" ]]; then
    virsh shutdown "$DOMAIN" >/dev/null || true
    if ! wait_for_shutdown; then
      virsh destroy "$DOMAIN" >/dev/null
    fi
  fi
}

recreate_overlay() {
  rm -f "$OVERLAY_IMAGE"
  qemu-img create -f qcow2 -F qcow2 -b "$BASE_IMAGE" "$OVERLAY_IMAGE" >/dev/null
}

define_domain_from_overlay_xml() {
  if [[ -f "$REFERENCE_XML" ]]; then
    cp "$REFERENCE_XML" "$WORK_XML"
  else
    rewrite_domain_xml_to_overlay
  fi
  virsh define "$WORK_XML" >/dev/null
}

print_summary() {
  echo "domain=$DOMAIN"
  echo "state=$(domain_state)"
  echo "base_image=$BASE_IMAGE"
  echo "overlay_image=$OVERLAY_IMAGE"
  virsh dumpxml "$DOMAIN" | grep -m1 "<source file="
}

require_file "$BASE_IMAGE"
stop_domain_if_needed
recreate_overlay
define_domain_from_overlay_xml
virsh start "$DOMAIN" >/dev/null
print_summary
