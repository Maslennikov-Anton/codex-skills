#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path


DEFAULT_INPUT = Path("/home/ant/codex-work/configurator/coverage/case-registry.json")
DEFAULT_OUTPUT = Path("/home/ant/codex-work/configurator/coverage/case-registry-report.md")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    registry = json.loads(args.input.read_text())
    cases = registry["cases"]
    counts = Counter(case["normalized_status"] for case in cases)

    lines = []
    lines.append("# Case Registry Report")
    lines.append("")
    lines.append(f"Источник: `{args.input}`")
    lines.append("")
    lines.append(f"Всего кейсов: `{len(cases)}`")
    lines.append("")
    lines.append("Статусы:")
    for key in sorted(counts):
        lines.append(f"- `{key}`: `{counts[key]}`")
    lines.append("")
    lines.append("| ID | Название | Feature | Status | Backend | Mode | Fixtures |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for case in cases:
        title = case["name"].replace("|", "\\|")
        feature = (case["feature"] or "").replace("|", "\\|")
        fixtures = ", ".join(case["required_fixtures"])
        lines.append(
            f"| {case['id']} | {title} | {feature} | {case['normalized_status']} | "
            f"{case['required_backend']} | {case['execution_mode']} | {fixtures} |"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
