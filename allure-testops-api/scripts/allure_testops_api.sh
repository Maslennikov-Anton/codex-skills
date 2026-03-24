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
    curl --silent --show-error --fail-with-body \
      -X "${method}" "${ALLURE_TESTOPS_URL%/}${path_part}${query_part}" \
      -H "Accept: application/json" \
      -H "Authorization: Bearer ${access_token}" \
      -H "Content-Type: application/json" \
      --data "${json_body}"
    return
  fi

  curl --silent --show-error --fail-with-body \
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

testcase_overview_get() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 testcase-overview-get TESTCASE_ID" >&2
    exit 2
  fi
  api_call GET "/api/testcase/$1/overview"
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

testcase_scenario_get() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 testcase-scenario-get TESTCASE_ID" >&2
    exit 2
  fi
  api_call GET "/api/testcase/$1/scenario"
}

testcase_step_tree() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 testcase-step-tree TESTCASE_ID" >&2
    exit 2
  fi
  api_call GET "/api/testcase/$1/step"
}

normalize_scenario_file() {
  local file_path="$1"
  python3 - "$file_path" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
obj = json.loads(path.read_text())
steps = obj["steps"] if isinstance(obj, dict) else obj

normalized = {"steps": []}
for index, step in enumerate(steps, start=1):
    name = (step.get("name") or "").strip()
    expected = (step.get("expectedResult") or "").strip()
    if not name:
        raise SystemExit(f"Step #{index} is missing 'name'")
    if not expected:
        raise SystemExit(f"Step #{index} is missing 'expectedResult'")
    normalized["steps"].append({"name": name, "expectedResult": expected})

print(json.dumps(normalized, ensure_ascii=False))
PY
}

testcase_sync_scenario() {
  if [[ $# -ne 2 ]]; then
    echo "Usage: $0 testcase-sync-scenario TESTCASE_ID SCENARIO_JSON_FILE" >&2
    exit 2
  fi

  local testcase_id="$1"
  local scenario_file="$2"
  local scenario_json
  local step_tree_json
  local root_ids_file
  local step_pairs_file

  scenario_json="$(normalize_scenario_file "${scenario_file}")"
  api_call POST "/api/testcase/${testcase_id}/scenario" "" "${scenario_json}" >/dev/null

  step_tree_json="$(api_call GET "/api/testcase/${testcase_id}/step")"
  root_ids_file="$(mktemp)"
  step_pairs_file="$(mktemp)"

  printf '%s' "${step_tree_json}" | python3 -c '
import json, sys
obj = json.load(sys.stdin)
for step_id in obj["root"]["children"]:
    print(step_id)
' > "${root_ids_file}"

  printf '%s' "${scenario_json}" | python3 -c '
import json, sys
obj = json.load(sys.stdin)
for step in obj["steps"]:
    print(json.dumps(step, ensure_ascii=False))
' > "${step_pairs_file}"

  mapfile -t root_ids < "${root_ids_file}"
  mapfile -t step_pairs < "${step_pairs_file}"

  rm -f "${root_ids_file}" "${step_pairs_file}"

  if [[ "${#root_ids[@]}" -ne "${#step_pairs[@]}" ]]; then
    echo "Root step count ${#root_ids[@]} does not match scenario step count ${#step_pairs[@]}" >&2
    exit 1
  fi

  local index
  for index in "${!root_ids[@]}"; do
    local step_id="${root_ids[$index]}"
    local payload
    payload="$(python3 - "${step_pairs[$index]}" <<'PY'
import json, sys
step = json.loads(sys.argv[1])
print(json.dumps({"body": step["name"]}, ensure_ascii=False))
PY
)"
    api_call PATCH "/api/testcase/step/${step_id}" "" "${payload}" >/dev/null
  done

  api_call GET "/api/testcase/${testcase_id}/overview"
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
  testcase-overview-get)
    shift
    testcase_overview_get "$@"
    ;;
  testcase-workflow)
    shift
    testcase_workflow "$@"
    ;;
  testcase-set-status)
    shift
    testcase_set_status "$@"
    ;;
  testcase-scenario-get)
    shift
    testcase_scenario_get "$@"
    ;;
  testcase-step-tree)
    shift
    testcase_step_tree "$@"
    ;;
  testcase-sync-scenario)
    shift
    testcase_sync_scenario "$@"
    ;;
  GET|POST|PUT|PATCH|DELETE)
    api_call "$@"
    ;;
  *)
    echo "Usage:" >&2
    echo "  $0 auth" >&2
    echo "  $0 jwt" >&2
    echo "  $0 testcase-get TESTCASE_ID" >&2
    echo "  $0 testcase-overview-get TESTCASE_ID" >&2
    echo "  $0 testcase-workflow TESTCASE_ID" >&2
    echo "  $0 testcase-set-status TESTCASE_ID STATUS_ID WORKFLOW_ID" >&2
    echo "  $0 testcase-scenario-get TESTCASE_ID" >&2
    echo "  $0 testcase-step-tree TESTCASE_ID" >&2
    echo "  $0 testcase-sync-scenario TESTCASE_ID SCENARIO_JSON_FILE" >&2
    echo "  $0 METHOD PATH [QUERY] [JSON_BODY]" >&2
    exit 2
    ;;
esac
