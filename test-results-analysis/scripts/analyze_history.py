#!/usr/bin/env python3
"""Read-only Allure export adapter and conservative history aggregation (stdlib)."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

STATUSES = {"passed", "failed", "broken", "skipped", "unknown"}
FAILURES = {"failed", "broken"}
UNKNOWN = {"", "unknown", "unavailable", "n/a"}


class InputError(ValueError):
    """Diagnostic text contains schema field names, never raw result bodies."""


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise InputError(message)


def validate(row):
    require(isinstance(row, dict), "attempt must be an object")
    for key in ("run_id", "result_id", "test_id", "variant", "revision"):
        require(isinstance(row.get(key), str) and row[key].strip(), f"missing/invalid {key}")
    for key in ("artifacts", "environment"):
        require(isinstance(row.get(key), dict) and row[key], f"missing/invalid {key}")
        require(all(isinstance(k, str) and k.strip() and isinstance(v, str) for k, v in row[key].items()),
                f"{key} must map strings to strings")
    require(type(row.get("run_order")) is int and row["run_order"] >= 0, "invalid run_order")
    require(type(row.get("run_complete")) is bool, "run_complete must be explicit boolean")
    attempt = row.get("attempt")
    require(attempt is None or (type(attempt) is int and attempt >= 0), "invalid attempt")
    require(row.get("status") in STATUSES, "invalid status")
    require(row.get("expected_status") in STATUSES, "invalid expected_status")
    duration = row.get("duration_ms")
    require(duration is None or (type(duration) in (int, float) and math.isfinite(duration)
                                and duration >= 0), "invalid duration_ms")
    return row


def context(row):
    return {k: row[k] for k in ("revision", "artifacts", "environment")}


def comparable(row):
    values = [row["revision"], *row["artifacts"].values(), *row["environment"].values()]
    return all(v.strip().lower() not in UNKNOWN for v in values)


def analyze(rows):
    groups, seen, runs = defaultdict(list), {}, {}
    duplicates = 0
    for raw in rows:
        row = validate(raw)
        key = row["run_id"], row["result_id"]
        if key in seen:
            require(seen[key] == row, "conflicting duplicate result")
            duplicates += 1
            continue
        seen[key] = row
        run_metadata = (row["run_order"], row["run_complete"], context(row))
        require(row["run_id"] not in runs or runs[row["run_id"]] == run_metadata,
                "inconsistent metadata within run")
        runs[row["run_id"]] = run_metadata
        isolation = None if comparable(row) else row["run_id"]
        groups[(row["test_id"], row["variant"], digest(context(row)), isolation)].append(row)
    require(bool(seen), "empty history")
    output = []
    for (test_id, variant, context_id, isolation), attempts in sorted(groups.items()):
        by_run = defaultdict(list)
        for attempt in attempts:
            by_run[attempt["run_id"]].append(attempt)
        outcomes = []
        for run_id, items in sorted(by_run.items(), key=lambda pair: (pair[1][0]["run_order"], pair[0])):
            indices = [r["attempt"] for r in items]
            ordered = (all(i is not None for i in indices)
                       and sorted(indices) == list(range(len(items))))
            eligible = all(r["expected_status"] == "passed" for r in items)
            issues = []
            if not ordered:
                issues.append("unknown, duplicated or non-contiguous retry indices")
            if not eligible:
                issues.append("expected outcome outside positive-case metrics")
            if not all(r["run_complete"] for r in items):
                issues.append("incomplete run/export")
            if not all(r["status"] in FAILURES | {"passed"} for r in items):
                issues.append("skipped or unknown observed status")
            usable = not issues
            sequence = sorted(items, key=lambda r: r["attempt"]) if ordered else items
            first, last = sequence[0], sequence[-1]
            outcomes.append({"run_id": run_id, "run_order": first["run_order"],
                             "attempts": len(items), "statuses": [r["status"] for r in sequence],
                             "issues": issues,
                             "usable": usable, "initial": first["status"] if usable else None,
                             "final": last["status"] if usable else None,
                             "rescued": bool(usable and first["status"] in FAILURES
                                             and last["status"] == "passed"),
                             "final_duration_ms": last.get("duration_ms") if usable else None})
        finals = {r["final"] for r in outcomes if r["usable"]}
        if isolation is not None:
            classification = "incomparable-context"
        elif not all(r["usable"] for r in outcomes):
            classification = "incomplete"
        elif "passed" in finals and finals & FAILURES:
            classification = "cross-run-variability-candidate"
        elif finals and finals <= FAILURES:
            classification = "persistent-failure-observed" if len(outcomes) >= 2 else "single-failure"
        elif any(r["rescued"] for r in outcomes):
            classification = "retry-rescue-observed"
        else:
            classification = "pass-observed"
        durations = [r["final_duration_ms"] for r in outcomes
                     if r["final"] == "passed" and r["final_duration_ms"] is not None]
        output.append({"test_id": test_id, "variant": variant, "context_id": context_id,
                       "context": context(attempts[0]), "classification": classification,
                       "runs": outcomes, "rescued_runs": sum(r["rescued"] for r in outcomes),
                       "usable_runs": sum(r["usable"] for r in outcomes),
                       "raw_status_counts": dict(Counter(r["status"] for r in attempts)),
                       "passed_final_median_ms": statistics.median(durations) if durations else None})
    return {"schema_version": 1, "unique_attempts": len(seen), "duplicate_rows": duplicates,
            "groups": output,
            "limits": "Observed export only; not a test-plan/attachment completeness audit or flaky root cause."}


def allure_rows(manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(isinstance(manifest, dict), "manifest must be an object")
    require(manifest.get("schema_version") == 1 and isinstance(manifest.get("runs"), list),
            "expected manifest schema_version=1 and runs list")
    for run in manifest["runs"]:
        require(isinstance(run, dict), "manifest run must be an object")
        require(type(run.get("no_test_retries", False)) is bool, "invalid no_test_retries")
        attempt_map = run.get("attempts", {})
        require(isinstance(attempt_map, dict), "attempts must map result UUIDs to indices")
        expected_map = run.get("expected_status_by_uuid", {})
        require(isinstance(expected_map, dict), "expected_status_by_uuid must be an object")
        directory = (manifest_path.parent / run["results_dir"]).resolve()
        require(directory.is_dir(), "results_dir is not a directory")
        paths = sorted(directory.glob("*-result.json"))
        require(bool(paths), "results_dir contains no Allure result files")
        for path in paths:
            require(not path.is_symlink(), "symlink result files are unsupported")
            result = json.loads(path.read_text(encoding="utf-8"))
            require(isinstance(result, dict), "Allure result must be an object")
            uuid = result.get("uuid")
            require(isinstance(uuid, str) and uuid, "Allure result missing UUID")
            raw_labels = result.get("labels", [])
            require(isinstance(raw_labels, list), "Allure labels must be a list")
            require(all(isinstance(label, dict) and isinstance(label.get("name"), str)
                        and isinstance(label.get("value"), str) for label in raw_labels),
                    "invalid Allure label")
            ids = {label["value"] for label in raw_labels if label["name"].lower() == "as_id"}
            require(len(ids) <= 1 and all(value.strip() for value in ids), "ambiguous/empty AS_ID")
            labels = {label["name"].lower(): label["value"] for label in raw_labels}
            if "as_id" in labels:
                test_id = "as_id:" + str(labels["as_id"])
            elif result.get("testCaseId"):
                test_id = "testCaseId:" + result["testCaseId"]
            else:
                require(bool(result.get("fullName")), "Allure result missing stable test identity")
                test_id = "fullName:" + result["fullName"]
            raw_parameters = result.get("parameters", [])
            require(isinstance(raw_parameters, list) and all(isinstance(p, dict)
                    and isinstance(p.get("name"), str) and type(p.get("excluded", False)) is bool
                    for p in raw_parameters), "invalid Allure parameters")
            parameters = sorted((p["name"], canonical(p.get("value")))
                                for p in raw_parameters if not p.get("excluded", False))
            variant = digest({"historyId": result.get("historyId"), "parameters": parameters})
            start, stop = result.get("start"), result.get("stop")
            duration = stop - start if type(start) in (int, float) and type(stop) in (int, float) else None
            attempt = attempt_map.get(uuid)
            if run.get("no_test_retries"):
                require(not attempt_map, "choose attempts map or no_test_retries, not both")
                attempt = 0
            row = {"run_id": run["id"], "run_order": run["order"], "run_complete": run["complete"],
                   "result_id": uuid, "test_id": test_id, "variant": variant, "attempt": attempt,
                   "status": result.get("status", "unknown"),
                   "expected_status": expected_map.get(uuid, "passed"),
                   "duration_ms": duration, **{k: run[k] for k in ("revision", "artifacts", "environment")}}
            yield validate(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("allure", "analyze"))
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "allure":
            # Validate the whole export before emitting a partial stream.
            rows = list(allure_rows(args.input))
            require(bool(rows), "empty Allure export")
            analyze(rows)
            for row in rows:
                print(canonical(row))
        else:
            rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines()
                    if line.strip()]
            require(bool(rows), "empty history")
            report = analyze(rows)
            report["input_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
            print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    except (ValueError, OSError, KeyError, TypeError) as error:
        # Never dump input records, error messages from tests, or attachment bodies.
        detail = str(error) if isinstance(error, InputError) else type(error).__name__
        print(f"Invalid history input: {detail}; check schema and local files.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
