#!/usr/bin/env python3
"""Prepare isolated fixtures and score observed Codex JSONL traces, not prose claims.

Does not invoke a model. Runs only the local grader of the selected trusted case.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "behavior-cases.json"
READER = re.compile(r"\b(cat|sed|head|tail|rg|read_text|readFile|read_file)\b")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): digest(p) for p in root.rglob("*")
            if p.is_file() and not set(p.relative_to(root).parts) & {"__pycache__", ".git", ".pytest_cache"}}


def safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError(f"Path outside fixture: {relative}")
    return path


def load_cases(path: Path) -> dict:
    data = json.loads(path.read_text())
    if not isinstance(data, list) or not data:
        raise ValueError("Expected a nonempty case array")
    cases = {}
    for case in data:
        name = case["id"]
        if not re.fullmatch(r"[a-z0-9-]+", name) or name in cases:
            raise ValueError("Case ids must be unique lowercase slugs")
        if not case.get("prompt") or case.get("grader") not in {"manual", "unittest", "truthful-oracle"}:
            raise ValueError(f"Invalid case: {name}")
        if set(case["required_skills"]) & set(case["forbidden_skills"]):
            raise ValueError(f"Conflicting routing assertions: {name}")
        cases[name] = case
    return cases


def prepare(case: dict, output: Path, skills_root: Path, variant: str, model: str, harness: str) -> None:
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    workspace.mkdir()
    for name, content in case.get("files", {}).items():
        path = safe_path(workspace, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    snapshot = {p.parent.name: {"sha256": digest(p), "text": p.read_text()}
                for p in skills_root.glob("*/SKILL.md")}
    required = set(case["required_skills"])
    if required - snapshot.keys():
        raise ValueError("Required skills missing from snapshot")
    state = {"case": case, "variant": variant, "model": model, "harness": harness,
             "skills": snapshot, "initial_files": files(workspace)}
    resources = {str(path.relative_to(skills_root)): digest(path)
                 for name in snapshot for path in (skills_root / name).rglob("*")
                 if path.is_file() and "__pycache__" not in path.parts}
    state["corpus_sha256"] = hashlib.sha256(json.dumps(resources, sort_keys=True).encode()).hexdigest()
    (output / "evaluation.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    (output / "prompt.txt").write_text(case["prompt"] + "\n")


def read_trace(path: Path, skills: dict) -> dict:
    events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    loaded, commands, final_messages = set(), [], []
    completed, failed, usage = False, False, None
    for event in events:
        if event.get("type") == "turn.completed":
            completed, usage = True, event.get("usage")
        if event.get("type") in {"turn.failed", "error"}:
            failed = True
        item = event.get("item", {})
        if event.get("type") != "item.completed":
            continue
        if item.get("type") == "agent_message":
            final_messages.append(item.get("text", ""))
        if item.get("type") != "command_execution":
            continue
        commands.append(item.get("command", ""))
        command, output = commands[-1], item.get("aggregated_output", "")
        if item.get("exit_code") != 0 or "SKILL.md" not in command or not READER.search(command):
            continue
        for name, skill in skills.items():
            # Match both frontmatter and a body fragment from the captured skill.
            # A mention in the final answer or `echo /.../SKILL.md` is not a read.
            body = skill["text"].split("\n---", 1)[-1].strip()
            fragment = next((line for line in body.splitlines() if len(line) >= 24), body[:60])
            if re.search(rf"(?m)^name:\s*['\"]?{re.escape(name)}['\"]?\s*$", output) and fragment in output:
                loaded.add(name)
    return {"loaded_skills": sorted(loaded), "command_count": len(commands),
            "repeated_commands": len(commands) - len(set(commands)), "usage": usage,
            "trace_complete": completed and not failed, "final_messages": final_messages}


def run_unittest(workspace: Path, *, patch: str = "") -> dict:
    setup = {"": "", "contract": "import access; access.can_edit = lambda role: role == 'owner'\n",
             "grant-all": "import access; access.can_edit = lambda role: True\n"}[patch]
    code = setup + (
        "import json, unittest\n"
        "suite = unittest.defaultTestLoader.discover('.', pattern='test_*.py')\n"
        "result = unittest.TextTestRunner(verbosity=0).run(suite)\n"
        "print(json.dumps(dict(tests=result.testsRun, failures=len(result.failures), "
        "errors=len(result.errors), skipped=len(result.skipped))))\n"
    )
    result = subprocess.run([sys.executable, "-B", "-c", code], cwd=workspace,
                            capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise ValueError("Grader process did not complete")
    return json.loads(result.stdout.splitlines()[-1])


def grade(case: dict, workspace: Path) -> tuple[str, dict]:
    if case["grader"] == "manual":
        return "needs_review", {"review": case["review"]}
    first = run_unittest(workspace)
    nonempty = first["tests"] > 0 and first["errors"] == 0 and first["skipped"] == 0
    if case["grader"] == "unittest":
        return ("pass" if nonempty and first["failures"] == 0 else "fail"), {"original": first}
    second = run_unittest(workspace, patch="contract")
    third = run_unittest(workspace, patch="grant-all")
    passed = nonempty and first["failures"] > 0 and second["tests"] == first["tests"] and not any(
        second[key] for key in ("failures", "errors", "skipped")) and third["failures"] > 0 and not any(
        third[key] for key in ("errors", "skipped")) and third["tests"] == first["tests"]
    return ("pass" if passed else "fail"), {"buggy_product": first, "contract_implementation": second,
                                           "unauthorized_viewer_mutation": third}


def score(run: Path, trace: Path, elapsed_seconds: float | None = None) -> dict:
    state = json.loads((run / "evaluation.json").read_text())
    case = state["case"]
    observed = read_trace(trace, state["skills"])
    loaded = set(observed["loaded_skills"])
    missing = sorted(set(case["required_skills"]) - loaded)
    forbidden = set(state["skills"]) if case["forbidden_skills"] == ["*"] else set(case["forbidden_skills"])
    unexpected = sorted(loaded & forbidden)
    current = files(run / "workspace")
    changed = {name for name in current.keys() | state["initial_files"].keys()
               if current.get(name) != state["initial_files"].get(name)}
    violations = sorted(changed - set(case.get("allowed_changes", [])))
    try:
        outcome, details = grade(case, run / "workspace")
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        outcome, details = "inconclusive", {"error": type(error).__name__}
    if violations:
        outcome = "fail"
    routing = "fail" if missing or unexpected else "pass"
    if not observed["trace_complete"]:
        routing = "inconclusive"
        if outcome != "fail":
            outcome = "inconclusive"
    return {"case": case["id"], "variant": state["variant"], "model": state["model"],
            "harness": state["harness"], "case_sha256": hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest(),
            "trace_sha256": digest(trace), "corpus_sha256": state["corpus_sha256"],
            "elapsed_seconds": elapsed_seconds,
            "skills_sha256": {name: data["sha256"] for name, data in state["skills"].items()},
            **observed, "routing": routing, "missing_skill_reads": missing, "forbidden_skill_reads": unexpected,
            "outcome": outcome, "constraint_violations": violations, "grader": details}


def compare(reports: list[dict]) -> list[dict]:
    """Reject mixed inputs before calculating descriptive (not causal) statistics."""
    identities, groups, corpora, seen = {}, {}, {}, set()
    for report in reports:
        key = report["case"]
        identity = (report["model"], report["harness"], report["case_sha256"])
        if key in identities and identities[key] != identity:
            raise ValueError(f"Incomparable model/harness/fixture for {key}")
        identities[key] = identity
        group = (key, report["variant"])
        if group in corpora and corpora[group] != report["corpus_sha256"]:
            raise ValueError(f"Mixed skill snapshots in one variant for {key}")
        corpora[group] = report["corpus_sha256"]
        execution = (*group, report["trace_sha256"])
        if execution in seen:
            raise ValueError(f"Duplicate trace is not an independent repetition: {key}")
        seen.add(execution)
        groups.setdefault((key, report["variant"]), []).append(report)
    summaries = []
    for (case, variant), runs in sorted(groups.items()):
        summary = {"case": case, "variant": variant, "runs": len(runs),
                   "routing_passes": sum(r["routing"] == "pass" for r in runs),
                   "outcome_passes": sum(r["outcome"] == "pass" for r in runs),
                   "incomplete_traces": sum(not r["trace_complete"] for r in runs),
                   "constraint_failures": sum(bool(r["constraint_violations"]) for r in runs)}
        for field, values in (
            ("seconds", [r.get("elapsed_seconds") for r in runs]),
            ("input_tokens", [(r.get("usage") or {}).get("input_tokens") for r in runs]),
            ("output_tokens", [(r.get("usage") or {}).get("output_tokens") for r in runs]),
            ("commands", [r["command_count"] for r in runs]),
        ):
            measured = [value for value in values if isinstance(value, (int, float))]
            summary[field] = {"measured_runs": len(measured), "mean": statistics.mean(measured) if measured else None,
                              "stdev": statistics.stdev(measured) if len(measured) > 1 else None}
        summaries.append(summary)
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    setup = sub.add_parser("prepare")
    setup.add_argument("--case", required=True)
    setup.add_argument("--cases", type=Path, default=CASES)
    setup.add_argument("--output", required=True, type=Path)
    setup.add_argument("--skills-root", type=Path, default=ROOT)
    setup.add_argument("--variant", required=True, help="e.g. before, candidate, no-skill")
    setup.add_argument("--model", required=True, help="Actual resolved model, recorded for comparison")
    setup.add_argument("--harness", required=True, help="CLI version and effective settings fingerprint")
    evaluate = sub.add_parser("score")
    evaluate.add_argument("--run", required=True, type=Path)
    evaluate.add_argument("--trace", required=True, type=Path)
    evaluate.add_argument("--elapsed-seconds", type=float, help="Measured wall time from the harness, never inferred")
    comparison = sub.add_parser("compare")
    comparison.add_argument("reports", type=Path, nargs="+")
    args = parser.parse_args()
    try:
        if args.mode == "prepare":
            prepare(load_cases(args.cases)[args.case], args.output, args.skills_root,
                    args.variant, args.model, args.harness)
            print(args.output / "prompt.txt")
            return 0
        if args.mode == "compare":
            print(json.dumps(compare([json.loads(p.read_text()) for p in args.reports]), ensure_ascii=False, indent=2))
            return 0
        if args.elapsed_seconds is not None and (not math.isfinite(args.elapsed_seconds) or args.elapsed_seconds < 0):
            raise ValueError("elapsed-seconds must be finite and nonnegative")
        report = score(args.run, args.trace, args.elapsed_seconds)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["routing"] == report["outcome"] == "pass" else 1
    except (ValueError, KeyError, OSError) as error:
        print(f"Evaluation failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
