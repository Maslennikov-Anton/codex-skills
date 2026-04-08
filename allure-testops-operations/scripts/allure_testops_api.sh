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

json_from_file() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 json-from-file JSON_FILE" >&2
    exit 2
  fi

  local json_file="$1"
  if [[ ! -f "${json_file}" ]]; then
    echo "JSON file not found: ${json_file}" >&2
    exit 2
  fi

  cat "${json_file}"
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

testcase_set_step_expected_result() {
  if [[ $# -ne 3 ]]; then
    echo "Usage: $0 testcase-set-step-expected-result TESTCASE_ID STEP_INDEX EXPECTED_RESULT_TEXT" >&2
    exit 2
  fi

  local testcase_id="$1"
  local step_index="$2"
  local expected_text="$3"
  local step_tree_json
  local root_step_id
  local expected_result_id
  local expected_children
  local old_child_id
  local payload

  step_tree_json="$(api_call GET "/api/testcase/${testcase_id}/step")"

  root_step_id="$(printf '%s' "${step_tree_json}" | python3 -c '
import json, sys
obj = json.load(sys.stdin)
index = int(sys.argv[1])
children = obj["root"]["children"]
if index < 0 or index >= len(children):
    raise SystemExit(f"Step index {index} is out of range")
print(children[index])
' "${step_index}")"

  expected_result_id="$(printf '%s' "${step_tree_json}" | python3 -c '
import json, sys
obj = json.load(sys.stdin)
step_id = sys.argv[1]
step = obj["scenarioSteps"][step_id]
expected_id = step.get("expectedResultId")
if not expected_id:
    raise SystemExit(f"Root step {step_id} has no expectedResultId")
print(expected_id)
' "${root_step_id}")"

  expected_children="$(printf '%s' "${step_tree_json}" | python3 -c '
import json, sys
obj = json.load(sys.stdin)
step_id = sys.argv[1]
for child_id in obj["scenarioSteps"].get(step_id, {}).get("children", []) or []:
    print(child_id)
' "${expected_result_id}")"

  if [[ -n "${expected_children}" ]]; then
    while IFS= read -r old_child_id; do
      [[ -z "${old_child_id}" ]] && continue
      api_call DELETE "/api/testcase/step/${old_child_id}" >/dev/null
    done <<< "${expected_children}"
  fi

  payload="$(python3 - "${expected_result_id}" "${testcase_id}" "${expected_text}" <<'PY'
import json, sys
parent_id = int(sys.argv[1])
testcase_id = int(sys.argv[2])
text = sys.argv[3]
print(json.dumps({
    "bodyJson": {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                    }
                ],
            }
        ],
    },
    "parentId": parent_id,
    "testCaseId": testcase_id,
}, ensure_ascii=False))
PY
)"

  api_call POST "/api/testcase/step" "?withExpectedResult=false" "${payload}"
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

defect_list() {
  if [[ $# -lt 1 || $# -gt 3 ]]; then
    echo "Usage: $0 defect-list PROJECT_ID [PAGE] [SIZE]" >&2
    exit 2
  fi

  local project_id="$1"
  local page="${2:-0}"
  local size="${3:-20}"
  api_call GET "/api/defect" "?projectId=${project_id}&page=${page}&size=${size}"
}

defect_get() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 defect-get DEFECT_ID" >&2
    exit 2
  fi

  api_call GET "/api/defect/$1"
}

defect_create() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 defect-create DEFECT_JSON_FILE" >&2
    exit 2
  fi

  local payload
  payload="$(json_from_file "$1")"
  api_call POST "/api/defect" "" "${payload}"
}

defect_patch() {
  if [[ $# -ne 2 ]]; then
    echo "Usage: $0 defect-patch DEFECT_ID DEFECT_PATCH_JSON_FILE" >&2
    exit 2
  fi

  local defect_id="$1"
  local payload
  payload="$(json_from_file "$2")"
  api_call PATCH "/api/defect/${defect_id}" "" "${payload}"
}

defect_close() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 defect-close DEFECT_ID" >&2
    exit 2
  fi

  api_call PATCH "/api/defect/$1" "" '{"closed":true}'
}

defect_reopen() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 defect-reopen DEFECT_ID" >&2
    exit 2
  fi

  api_call PATCH "/api/defect/$1" "" '{"closed":false}'
}

defect_matcher_list() {
  if [[ $# -lt 1 || $# -gt 3 ]]; then
    echo "Usage: $0 defect-matcher-list DEFECT_ID [PAGE] [SIZE]" >&2
    exit 2
  fi

  local defect_id="$1"
  local page="${2:-0}"
  local size="${3:-20}"
  api_call GET "/api/defect/${defect_id}/matcher" "?page=${page}&size=${size}"
}

issueschema_list() {
  if [[ $# -lt 1 || $# -gt 3 ]]; then
    echo "Usage: $0 issueschema-list PROJECT_ID [PAGE] [SIZE]" >&2
    exit 2
  fi

  local project_id="$1"
  local page="${2:-0}"
  local size="${3:-20}"
  api_call GET "/api/issueschema" "?projectId=${project_id}&page=${page}&size=${size}"
}

testcase_defect_list() {
  if [[ $# -lt 1 || $# -gt 3 ]]; then
    echo "Usage: $0 testcase-defect-list TESTCASE_ID [PAGE] [SIZE]" >&2
    exit 2
  fi

  local testcase_id="$1"
  local page="${2:-0}"
  local size="${3:-20}"
  api_call GET "/api/testcase/${testcase_id}/defect" "?page=${page}&size=${size}"
}

testcase_link_defect() {
  if [[ $# -ne 2 ]]; then
    echo "Usage: $0 testcase-link-defect TESTCASE_ID DEFECT_ID" >&2
    exit 2
  fi

  local testcase_id="$1"
  local defect_id="$2"

  # This endpoint may return 200 with an empty body, so verify by reading linked defects.
  api_call POST "/api/testcase/${testcase_id}/defect/${defect_id}" >/dev/null
  api_call GET "/api/testcase/${testcase_id}/defect" "?page=0&size=100"
}

defect_create_template() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 defect-create-template OUTPUT_JSON_FILE" >&2
    exit 2
  fi

  local output_file="$1"
  cat > "${output_file}" <<'EOF'
{
  "projectId": 3,
  "name": "Тестовый дефект: краткий заголовок",
  "description": "Краткое описание:\nОпиши проблему.\n\nПредусловия:\n1. Пользователь авторизован.\n2. Открыт нужный экран.\n\nШаги воспроизведения:\n1. Выполнить первое действие.\n2. Выполнить второе действие.\n\nОжидаемый результат:\nСистема ведет себя корректно.\n\nФактический результат:\nНаблюдается ошибка.\n\nСерьезность: Major\nПриоритет: Medium\nОкружение: test / web UI / Chrome / Linux",
  "matcher": {
    "name": "Тестовый matcher",
    "messageRegex": ".*(error text|navigation failed).*",
    "traceRegex": ".*(ExceptionType|ComponentName).*"
  }
}
EOF
}

defect_verify() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 defect-verify DEFECT_ID" >&2
    exit 2
  fi

  local defect_id="$1"
  local defect_json
  local matcher_json

  defect_json="$(api_call GET "/api/defect/${defect_id}")"
  matcher_json="$(api_call GET "/api/defect/${defect_id}/matcher" "?page=0&size=100")"

  python3 - <<'PY' "${defect_json}" "${matcher_json}"
import json
import sys

defect = json.loads(sys.argv[1])
matchers = json.loads(sys.argv[2])

summary = {
    "id": defect.get("id"),
    "projectId": defect.get("projectId"),
    "name": defect.get("name"),
    "closed": defect.get("closed"),
    "hasDescription": bool(defect.get("description")),
    "matcherCount": matchers.get("totalElements", len(matchers.get("content", []))),
}

print(json.dumps(summary, ensure_ascii=False))
PY
}

testcase_unlink_defect() {
  if [[ $# -ne 2 ]]; then
    echo "Usage: $0 testcase-unlink-defect TESTCASE_ID DEFECT_ID" >&2
    exit 2
  fi

  local testcase_id="$1"
  local defect_id="$2"

  api_call DELETE "/api/testcase/${testcase_id}/defect/${defect_id}" >/dev/null
  api_call GET "/api/testcase/${testcase_id}/defect" "?page=0&size=100"
}

defect_clone() {
  if [[ $# -ne 2 ]]; then
    echo "Usage: $0 defect-clone DEFECT_ID OUTPUT_JSON_FILE" >&2
    exit 2
  fi

  local defect_id="$1"
  local output_file="$2"
  local defect_json
  local matcher_json

  defect_json="$(api_call GET "/api/defect/${defect_id}")"
  matcher_json="$(api_call GET "/api/defect/${defect_id}/matcher" "?page=0&size=100")"

  python3 - <<'PY' "${defect_json}" "${matcher_json}" "${output_file}"
import json
import sys
from pathlib import Path

defect = json.loads(sys.argv[1])
matchers = json.loads(sys.argv[2]).get("content", [])
output_path = Path(sys.argv[3])

payload = {
    "projectId": defect.get("projectId"),
    "name": f'{defect.get("name", "").strip()} (copy)',
    "description": defect.get("description", ""),
}

if matchers:
    matcher = matchers[0]
    payload["matcher"] = {
        "name": matcher.get("name", ""),
        "messageRegex": matcher.get("messageRegex", ""),
        "traceRegex": matcher.get("traceRegex", ""),
    }

output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
PY
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
  testcase-set-step-expected-result)
    shift
    testcase_set_step_expected_result "$@"
    ;;
  defect-list)
    shift
    defect_list "$@"
    ;;
  defect-get)
    shift
    defect_get "$@"
    ;;
  defect-create)
    shift
    defect_create "$@"
    ;;
  defect-patch)
    shift
    defect_patch "$@"
    ;;
  defect-close)
    shift
    defect_close "$@"
    ;;
  defect-reopen)
    shift
    defect_reopen "$@"
    ;;
  defect-matcher-list)
    shift
    defect_matcher_list "$@"
    ;;
  issueschema-list)
    shift
    issueschema_list "$@"
    ;;
  testcase-defect-list)
    shift
    testcase_defect_list "$@"
    ;;
  testcase-link-defect)
    shift
    testcase_link_defect "$@"
    ;;
  defect-create-template)
    shift
    defect_create_template "$@"
    ;;
  defect-verify)
    shift
    defect_verify "$@"
    ;;
  testcase-unlink-defect)
    shift
    testcase_unlink_defect "$@"
    ;;
  defect-clone)
    shift
    defect_clone "$@"
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
    echo "  $0 testcase-set-step-expected-result TESTCASE_ID STEP_INDEX EXPECTED_RESULT_TEXT" >&2
    echo "  $0 defect-list PROJECT_ID [PAGE] [SIZE]" >&2
    echo "  $0 defect-get DEFECT_ID" >&2
    echo "  $0 defect-create DEFECT_JSON_FILE" >&2
    echo "  $0 defect-patch DEFECT_ID DEFECT_PATCH_JSON_FILE" >&2
    echo "  $0 defect-close DEFECT_ID" >&2
    echo "  $0 defect-reopen DEFECT_ID" >&2
    echo "  $0 defect-matcher-list DEFECT_ID [PAGE] [SIZE]" >&2
    echo "  $0 issueschema-list PROJECT_ID [PAGE] [SIZE]" >&2
    echo "  $0 testcase-defect-list TESTCASE_ID [PAGE] [SIZE]" >&2
    echo "  $0 testcase-link-defect TESTCASE_ID DEFECT_ID" >&2
    echo "  $0 defect-create-template OUTPUT_JSON_FILE" >&2
    echo "  $0 defect-verify DEFECT_ID" >&2
    echo "  $0 testcase-unlink-defect TESTCASE_ID DEFECT_ID" >&2
    echo "  $0 defect-clone DEFECT_ID OUTPUT_JSON_FILE" >&2
    echo "  $0 METHOD PATH [QUERY] [JSON_BODY]" >&2
    exit 2
    ;;
esac
