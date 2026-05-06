#!/usr/bin/env python3
"""Create a lightweight skill eval workspace from evals/evals.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_evals(skill_path: Path) -> dict:
    evals_path = skill_path / "evals" / "evals.json"
    if not evals_path.exists():
        skill_name = skill_path.name
        evals_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"skill_name": skill_name, "evals": []}
        evals_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return data
    return json.loads(evals_path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_path", type=Path, help="Path to the skill directory")
    parser.add_argument("--iteration", type=int, default=1, help="Iteration number")
    parser.add_argument(
        "--baseline",
        default="baseline",
        help="Baseline directory name, e.g. baseline, without_skill, old_skill",
    )
    args = parser.parse_args()

    skill_path = args.skill_path.resolve()
    if not (skill_path / "SKILL.md").exists():
        raise SystemExit(f"Not a skill directory: {skill_path}")

    data = load_evals(skill_path)
    evals = data.get("evals", [])
    workspace = skill_path.parent / f"{skill_path.name}-workspace" / f"iteration-{args.iteration}"
    workspace.mkdir(parents=True, exist_ok=True)

    for index, item in enumerate(evals):
        eval_id = str(item.get("id") or f"eval-{index}")
        eval_dir = workspace / eval_id
        (eval_dir / "with_skill" / "outputs").mkdir(parents=True, exist_ok=True)
        (eval_dir / args.baseline / "outputs").mkdir(parents=True, exist_ok=True)
        metadata = {
            "eval_id": eval_id,
            "prompt": item.get("prompt", ""),
            "expected_output": item.get("expected_output", ""),
            "files": item.get("files", []),
            "assertions": item.get("assertions", []),
        }
        (eval_dir / "eval_metadata.json").write_text(
            json.dumps(metadata, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"Workspace: {workspace}")
    print(f"Eval count: {len(evals)}")
    if not evals:
        print(f"Created empty eval set: {skill_path / 'evals' / 'evals.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
