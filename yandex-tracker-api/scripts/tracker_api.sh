#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage:" >&2
  echo "  tracker_api.sh METHOD PATH [QUERY] [JSON_BODY]" >&2
  echo "  tracker_api.sh FILE PATH FILE_PATH" >&2
  exit 2
fi

if [[ -z "${TRACKER_TOKEN:-}" ]]; then
  echo "TRACKER_TOKEN is required" >&2
  exit 2
fi

if [[ -z "${TRACKER_ORG_ID:-}" ]]; then
  echo "TRACKER_ORG_ID is required" >&2
  exit 2
fi

BASE_URL="${TRACKER_BASE_URL:-https://api.tracker.yandex.net/v3}"
AUTH_SCHEME="${TRACKER_AUTH_SCHEME:-OAuth}"
ORG_HEADER="${TRACKER_ORG_HEADER:-X-Org-ID}"
ACCEPT_LANGUAGE="${TRACKER_ACCEPT_LANGUAGE:-}"

METHOD="$1"
PATH_PART="$2"
QUERY_PART="${3:-}"

shift 3 || true

url="${BASE_URL}${PATH_PART}${QUERY_PART}"

common_args=(
  --silent
  --show-error
  --fail-with-body
  -H "Authorization: ${AUTH_SCHEME} ${TRACKER_TOKEN}"
  -H "${ORG_HEADER}: ${TRACKER_ORG_ID}"
)

if [[ -n "${ACCEPT_LANGUAGE}" ]]; then
  common_args+=(-H "Accept-Language: ${ACCEPT_LANGUAGE}")
fi

if [[ "${METHOD}" == "FILE" ]]; then
  if [[ $# -lt 1 ]]; then
    echo "FILE mode requires FILE_PATH" >&2
    exit 2
  fi

  FILE_PATH="$1"
  exec curl -X POST "${url}" \
    "${common_args[@]}" \
    --form "file=@${FILE_PATH}"
fi

JSON_BODY="${1:-}"

if [[ -n "${JSON_BODY}" ]]; then
  exec curl -X "${METHOD}" "${url}" \
    "${common_args[@]}" \
    -H "Content-Type: application/json" \
    --data "${JSON_BODY}"
fi

exec curl -X "${METHOD}" "${url}" "${common_args[@]}"
