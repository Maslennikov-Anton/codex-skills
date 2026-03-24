#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRET_FILE="${ALLURE_TESTOPS_SECRET_FILE:-/home/ant/.allure-testops.env}"

if [[ -f "${SECRET_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${SECRET_FILE}"
fi

if [[ -z "${ALLURE_TESTOPS_URL:-}" ]]; then
  echo "ALLURE_TESTOPS_URL is required" >&2
  exit 2
fi

if [[ -z "${ALLURE_TESTOPS_TOKEN:-}" ]]; then
  echo "ALLURE_TESTOPS_TOKEN is required" >&2
  exit 2
fi

auth() {
  curl --silent --show-error --fail-with-body \
    -X POST "${ALLURE_TESTOPS_URL%/}/api/uaa/oauth/token" \
    -H "Expect:" \
    -H "Accept: application/json" \
    --form "grant_type=apitoken" \
    --form "scope=openid" \
    --form "token=${ALLURE_TESTOPS_TOKEN}"
}

jwt() {
  auth | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
}

api_call() {
  if [[ $# -lt 2 ]]; then
    echo "Usage: $0 METHOD PATH [QUERY] [JSON_BODY]" >&2
    exit 2
  fi

  local method="$1"
  local path_part="$2"
  local query_part="${3:-}"
  local json_body="${4:-}"
  local access_token
  access_token="$(jwt)"

  if [[ -n "${json_body}" ]]; then
    exec curl --silent --show-error --fail-with-body \
      -X "${method}" "${ALLURE_TESTOPS_URL%/}${path_part}${query_part}" \
      -H "Accept: application/json" \
      -H "Authorization: Bearer ${access_token}" \
      -H "Content-Type: application/json" \
      --data "${json_body}"
  fi

  exec curl --silent --show-error --fail-with-body \
    -X "${method}" "${ALLURE_TESTOPS_URL%/}${path_part}${query_part}" \
    -H "Accept: application/json" \
    -H "Authorization: Bearer ${access_token}"
}

testcase_get() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 testcase-get TESTCASE_ID" >&2
    exit 2
  fi
  api_call GET "/api/testcase/$1"
}

testcase_workflow() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 testcase-workflow TESTCASE_ID" >&2
    exit 2
  fi
  api_call GET "/api/testcase/$1/workflow"
}

testcase_set_status() {
  if [[ $# -ne 3 ]]; then
    echo "Usage: $0 testcase-set-status TESTCASE_ID STATUS_ID WORKFLOW_ID" >&2
    exit 2
  fi

  local testcase_id="$1"
  local status_id="$2"
  local workflow_id="$3"
  api_call PATCH "/api/testcase/${testcase_id}" "" \
    "{\"statusId\":${status_id},\"workflowId\":${workflow_id}}"
}

case "${1:-}" in
  auth)
    auth
    ;;
  jwt)
    jwt
    ;;
  testcase-get)
    shift
    testcase_get "$@"
    ;;
  testcase-workflow)
    shift
    testcase_workflow "$@"
    ;;
  testcase-set-status)
    shift
    testcase_set_status "$@"
    ;;
  GET|POST|PUT|PATCH|DELETE)
    api_call "$@"
    ;;
  *)
    echo "Usage:" >&2
    echo "  $0 auth" >&2
    echo "  $0 jwt" >&2
    echo "  $0 testcase-get TESTCASE_ID" >&2
    echo "  $0 testcase-workflow TESTCASE_ID" >&2
    echo "  $0 testcase-set-status TESTCASE_ID STATUS_ID WORKFLOW_ID" >&2
    echo "  $0 METHOD PATH [QUERY] [JSON_BODY]" >&2
    exit 2
    ;;
esac
