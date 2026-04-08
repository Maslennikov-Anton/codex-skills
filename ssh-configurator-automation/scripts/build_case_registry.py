#!/usr/bin/env python3
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ENV_FILE = Path("/home/ant/.allure-testops.env")
DEFAULT_OUTPUT = Path("/home/ant/codex-work/configurator/coverage/case-registry.json")
DEFAULT_SOURCE_REPORT = Path(
    "/home/ant/codex-work/configurator/coverage/ssh-configurator_testops_front_results_2026-04-08.md"
)

KNOWN_HELPERS = {
    1700: "node /home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js connect-minimal",
    1691: "node /home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js assert-command diagnostics.check-systemd-journald",
    1688: "node /home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js select-first-key",
    1686: "node /home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js assert-command keys.list-user-keys",
    1661: "node /home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js assert-command network.files.list",
    1655: "node /home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js assert-command network.settings.reload-details",
    1654: "node /home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js read-console",
    1653: "node /home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js assert-command system.host.request-type",
    1647: "node /home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js assert-command system.kernel.request-cpu-qty",
    1645: "node /home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js assert-command system.datetime.request-timezone",
    1643: "node /home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js assert-command system.datetime.request-date-time",
}


def load_env(env_file: Path) -> dict:
    env = {}
    for raw_line in env_file.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        key, value = line.split("=", 1)
        env[key] = value.strip().strip("'").strip('"')
    return env


def auth_headers(base_url: str, api_token: str) -> dict:
    data = urllib.parse.urlencode(
        {"grant_type": "apitoken", "scope": "openid", "token": api_token}
    ).encode()
    req = urllib.request.Request(
        f"{base_url}/api/uaa/oauth/token",
        data=data,
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        jwt = json.load(response)["access_token"]
    return {"Accept": "application/json", "Authorization": f"Bearer {jwt}"}


def api_get(base_url: str, headers: dict, path: str) -> dict:
    req = urllib.request.Request(f"{base_url}{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def parse_markdown_report(path: Path) -> dict:
    if not path.exists():
        return {}

    rows = {}
    for line in path.read_text().splitlines():
        if not line.startswith("| "):
            continue
        if line.startswith("| ID |") or line.startswith("| --- |"):
            continue
        parts = [
            part.strip().replace("\\|", "|")
            for part in re.split(r"(?<!\\)\|", line.strip())[1:-1]
        ]
        if len(parts) != 5 or not parts[0].isdigit():
            continue
        case_id = int(parts[0])
        rows[case_id] = {
            "source_result": parts[3],
            "source_comment": parts[4],
        }
    return rows


def infer_execution_mode(name: str) -> str:
    lowered = name.lower()
    destructive_markers = [
        "удалить",
        "выключить",
        "остановить",
        "перезагрузить",
        "восстановить бэкап",
        "восстановить снепшот",
        "delete",
        "shutdown",
        "restore",
    ]
    mutating_markers = [
        "установить",
        "создать",
        "добавить",
        "переименовать",
        "редактировать",
        "задать",
        "обновить",
        "сгенерировать",
        "импортировать",
        "экспортировать",
        "запустить",
        "возобновить",
        "пауза",
        "слияние",
    ]
    if any(marker in lowered for marker in destructive_markers):
        return "destructive"
    if any(marker in lowered for marker in mutating_markers):
        return "mutating"
    return "safe-read"


def infer_required_backend(feature: str) -> str:
    if feature in {
        'ВС: Вкладка "Управление ВМ"',
        'ВС: Вкладка "Управление снепшотами"',
        'ВС: Вкладка "Резервное копирование"',
    }:
        return "virt-server"
    return "runtime-vm"


def infer_required_fixtures(comment: str) -> list[str]:
    fixtures = []
    lowered = comment.lower()
    if "сертификат" in lowered or "мониторинг" in lowered:
        fixtures.append("monitoring-assets")
    if "file dialog" in lowered or "файлов" in lowered or "import/export" in lowered:
        fixtures.append("file-artifacts")
    if "service discovery" in lowered:
        fixtures.append("service-discovery")
    if "негатив" in lowered or "валидац" in lowered:
        fixtures.append("negative-input-data")
    if "ключ" in lowered:
        fixtures.append("ssh-key-fixtures")
    return sorted(set(fixtures))


def normalize_status(source_result: str, comment: str) -> str:
    mapping = {
        "Пройден": "automation-pass",
        "Частично проверен": "in_progress",
        "Заблокирован окружением": "needs-new-backend",
    }
    if source_result in mapping:
        return mapping[source_result]

    lowered = comment.lower()
    if any(
        marker in lowered
        for marker in [
            "не была автоматизирована",
            "не покрыт текущим helper",
            "нет отдельного helper",
            "нет отдельной helper-команды",
            "нет page-specific",
        ]
    ):
        return "needs-new-helper"
    if any(
        marker in lowered
        for marker in [
            "фикстур",
            "сертификат",
            "файловые артефакты",
            "service discovery",
            "подготовленных",
        ]
    ):
        return "needs-fixture"
    if any(
        marker in lowered
        for marker in [
            "ручного",
            "визуаль",
            "tooltip",
            "theme",
            "human",
        ]
    ):
        return "needs-human-judgement"
    return "todo"


def build_registry_entry(case: dict, report_rows: dict) -> dict:
    report_data = report_rows.get(case["id"], {})
    source_result = report_data.get("source_result", "Не размечен")
    source_comment = report_data.get("source_comment", "")
    feature = case.get("feature") or ""
    name = case["name"]
    return {
        "id": case["id"],
        "name": name,
        "feature": feature,
        "application": case.get("application"),
        "story": case.get("story"),
        "description": case.get("description", ""),
        "precondition": case.get("precondition", ""),
        "expected_result": case.get("expectedResult", ""),
        "steps": case.get("steps", []),
        "source_result": source_result,
        "source_comment": source_comment,
        "normalized_status": normalize_status(source_result, source_comment),
        "execution_mode": infer_execution_mode(name),
        "required_backend": infer_required_backend(feature),
        "required_fixtures": infer_required_fixtures(source_comment),
        "helper_command": KNOWN_HELPERS.get(case["id"], ""),
        "last_evidence": source_comment if source_result in {"Пройден", "Частично проверен"} else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", type=int, default=3)
    parser.add_argument("--application", default="Конфигуратор")
    parser.add_argument("--story", default="front(ui)")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--source-report", type=Path, default=DEFAULT_SOURCE_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    env = load_env(args.env_file)
    base_url = env["ALLURE_TESTOPS_URL"].rstrip("/")
    headers = auth_headers(base_url, env["ALLURE_TESTOPS_TOKEN"])
    report_rows = parse_markdown_report(args.source_report)

    cases = api_get(
        base_url,
        headers,
        f"/api/rs/testcase?projectId={args.project_id}&page=0&size=1000",
    )["content"]
    candidate_ids = [case["id"] for case in cases if not case.get("automated")]

    def load_case(case_id: int) -> dict | None:
        overview = api_get(base_url, headers, f"/api/testcase/{case_id}/overview")
        custom_fields = {
            field["customField"]["name"]: field["name"]
            for field in overview.get("customFields", [])
        }
        if custom_fields.get("Application") != args.application:
            return None
        if custom_fields.get("Story") != args.story:
            return None
        testcase = api_get(base_url, headers, f"/api/testcase/{case_id}")
        scenario = api_get(base_url, headers, f"/api/testcase/{case_id}/scenario")
        return {
            "id": overview["id"],
            "name": overview["name"],
            "feature": custom_fields.get("Feature"),
            "application": custom_fields.get("Application"),
            "story": custom_fields.get("Story"),
            "description": testcase.get("description", ""),
            "precondition": testcase.get("precondition", ""),
            "expectedResult": testcase.get("expectedResult", ""),
            "steps": scenario.get("steps", []),
        }

    loaded_cases = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        for item in pool.map(load_case, candidate_ids):
            if item:
                loaded_cases.append(item)

    registry_cases = [
        build_registry_entry(case, report_rows)
        for case in sorted(loaded_cases, key=lambda item: item["id"], reverse=True)
    ]

    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project_id": args.project_id,
            "application": args.application,
            "story": args.story,
            "total_cases": len(registry_cases),
            "source_report": str(args.source_report),
        },
        "cases": registry_cases,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(args.output)
    print(len(registry_cases))
    return 0


if __name__ == "__main__":
    sys.exit(main())
