"""Contract tests for offline history aggregation and benchmark decision gates."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


history = load("history", "test-results-analysis/scripts/analyze_history.py")
bench = load("bench", "performance-benchmark/scripts/compare_benchmarks.py")


def row(run="r1", attempt=0, status="passed", **extra):
    return {"run_id": run, "run_order": int(run[1:]), "run_complete": True,
            "result_id": f"{run}-{attempt}", "test_id": "as_id:820", "variant": "mode-A",
            "attempt": attempt, "status": status, "expected_status": "passed", "duration_ms": 20,
            "revision": "test-sha", "artifacts": {"studio": "product-sha"},
            "environment": {"runner": "linux4cpu"}, **extra}


def record(samples=None):
    return {"revision": "source-sha", "environment": {"cpu": "cpu", "kernel": "linux",
            "python": "3.12", "dependencies": "stdlib"},
            "workload": {"id": "matching-1000", "input_sha256": "fixed-digest"},
            "protocol": {"unit": "seconds", "warmups": 2, "repeats": 5,
                         "method": "alternating perf_counter"},
            "samples_seconds": samples or [1.0, 1.01, 1.02, 1.01, 1.0]}


class HistoryTests(unittest.TestCase):
    def test_test_retry_and_job_rerun_are_distinct(self):
        report = history.analyze([row(status="failed"), row(attempt=1), row("r2")])
        group = report["groups"][0]
        self.assertEqual(group["classification"], "retry-rescue-observed")
        self.assertEqual(group["rescued_runs"], 1)
        self.assertEqual(len(group["runs"]), 2)
        self.assertEqual(group["runs"][0]["initial"], "failed")

    def test_repeated_failure_remains_failure(self):
        group = history.analyze([row(status="failed"), row("r2", status="broken")])["groups"][0]
        self.assertEqual(group["classification"], "persistent-failure-observed")
        self.assertEqual(group["raw_status_counts"], {"failed": 1, "broken": 1})

    def test_variability_with_same_context_only(self):
        group = history.analyze([row(status="failed"), row("r2")])["groups"][0]
        self.assertEqual(group["classification"], "cross-run-variability-candidate")

    def test_revision_product_environment_and_variant_split_groups(self):
        for change in ({"revision": "new-sha"}, {"artifacts": {"studio": "new-build"}},
                       {"environment": {"runner": "another-runner"}}, {"variant": "mode-B"}):
            with self.subTest(change=change):
                groups = history.analyze([row(status="failed"), row("r2", **change)])["groups"]
                self.assertEqual(len(groups), 2)
                self.assertNotIn("cross-run-variability-candidate", [g["classification"] for g in groups])

    def test_unknown_context_never_pools_runs(self):
        groups = history.analyze([row(revision="unknown"), row("r2", revision="unknown")])["groups"]
        self.assertEqual(len(groups), 2)
        self.assertEqual({g["classification"] for g in groups}, {"incomparable-context"})

    def test_unknown_order_gap_skipped_expected_and_incomplete_not_success(self):
        cases = [[row(attempt=None)], [row(attempt=1)], [row(status="skipped")],
                 [row(expected_status="failed")], [row(run_complete=False)],
                 [row(), row(attempt=0, result_id="other-uuid")]]
        for rows in cases:
            with self.subTest(rows=rows):
                group = history.analyze(rows)["groups"][0]
                self.assertEqual(group["classification"], "incomplete")
                self.assertEqual(group["usable_runs"], 0)

    def test_exact_duplicate_dedup_and_conflict_rejected(self):
        report = history.analyze([row(), row()])
        self.assertEqual(report["unique_attempts"], 1)
        self.assertEqual(report["duplicate_rows"], 1)
        with self.assertRaises(ValueError):
            history.analyze([row(), row(status="failed")])

    def test_invalid_metadata_and_durations_rejected(self):
        for change in ({"environment": {}}, {"artifacts": {}}, {"duration_ms": -1},
                       {"duration_ms": float("nan")}, {"run_complete": "true"},
                       {"attempt": True}, {"status": "success"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                history.analyze([row(**change)])

    def test_run_metadata_consistency(self):
        with self.assertRaises(ValueError):
            history.analyze([row(), row(attempt=1, revision="different")])

    def test_pass_duration_does_not_include_failed_attempt_time(self):
        group = history.analyze([row(status="failed", duration_ms=10000),
                                 row(attempt=1, duration_ms=20)])["groups"][0]
        self.assertEqual(group["passed_final_median_ms"], 20)

    def test_allure_adapter_preserves_parameters_and_unknown_retry_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index in range(2):
                (root / f"{index}-result.json").write_text(json.dumps({
                    "uuid": str(index), "labels": [{"name": "AS_ID", "value": "820"}],
                    "historyId": "same", "parameters": [{"name": "mode", "value": f"secret{index}"}],
                    "status": "passed", "start": 10, "stop": 30}))
            manifest = {"schema_version": 1, "runs": [{"id": "r1", "order": 1, "complete": True,
                "revision": "sha", "artifacts": {"studio": "build"},
                "environment": {"runner": "linux"}, "results_dir": "."}]}
            path = root / "manifest.json"; path.write_text(json.dumps(manifest))
            rows = list(history.allure_rows(path))
            self.assertNotIn("secret", json.dumps(rows))
            self.assertEqual(len({r["variant"] for r in rows}), 2)
            self.assertTrue(all(r["attempt"] is None for r in rows))
            self.assertTrue(all(g["classification"] == "incomplete" for g in history.analyze(rows)["groups"]))
            manifest["runs"][0]["no_test_retries"] = True
            path.write_text(json.dumps(manifest))
            self.assertTrue(all(r["attempt"] == 0 for r in history.allure_rows(path)))

    def test_empty_cli_input_is_error_not_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.jsonl"; path.write_text("")
            result = subprocess.run([sys.executable, "-B", history.__file__, "analyze", str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")

    def test_malformed_allure_objects_fail_without_partial_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); manifest = root / "manifest.json"
            run = {"id": "r1", "order": 1, "complete": True, "revision": "sha",
                   "artifacts": {"studio": "build"}, "environment": {"runner": "linux"},
                   "results_dir": ".", "no_test_retries": True}
            result_file = root / "a-result.json"
            for payload, data in (([], {}), ({"schema_version": 1, "runs": [run]}, []),
                                   ({"schema_version": 1, "runs": [run]},
                                    {"uuid": "a", "labels": [{"name": "AS_ID", "value": "1"},
                                                               {"name": "AS_ID", "value": "2"}]})):
                manifest.write_text(json.dumps(payload)); result_file.write_text(json.dumps(data))
                command = subprocess.run([sys.executable, "-B", history.__file__, "allure", str(manifest)],
                                         capture_output=True, text=True)
                self.assertEqual(command.returncode, 2)
                self.assertEqual(command.stdout, "")
                self.assertNotIn("Traceback", command.stderr)


class BenchmarkTests(unittest.TestCase):
    def test_clear_comparable_improvement_is_measurement_only(self):
        result, code = bench.compare(record(), record([0.5, 0.51, 0.5, 0.51, 0.5]))
        self.assertEqual(code, 0)
        self.assertEqual(result["verdict"], "measurement-win")
        self.assertIn("no functional", result["limits"])

    def test_regression_and_no_effect_are_no_win(self):
        for samples in ([1, 1.01, 1.02, 1.01, 1], [2, 2.01, 2, 2.01, 2]):
            self.assertEqual(bench.compare(record(), record(samples))[1], 1)

    def test_changed_environment_workload_or_protocol_inconclusive(self):
        for key in ("environment", "workload", "protocol"):
            after = record([0.5] * 5); after[key]["extra"] = "changed"
            result, code = bench.compare(record(), after)
            self.assertEqual(code, 2)
            self.assertIn(f"different {key}", result["reasons"])

    def test_noise_and_small_sample_inconclusive(self):
        self.assertEqual(bench.compare(record(), record([0.1, 0.9, 0.3, 0.7, 0.1]))[1], 2)
        before, after = record([1, 1, 1]), record([0.5, 0.5, 0.5])
        before["protocol"]["repeats"] = after["protocol"]["repeats"] = 3
        self.assertEqual(bench.compare(before, after)[1], 2)

    def test_invalid_samples_units_and_missing_fingerprints_rejected(self):
        for samples in ([0] * 5, [float("inf")] * 5, [True] * 5, [-1] * 5):
            with self.assertRaises(ValueError):
                bench.compare(record(), record(samples))
        for group, key, value in (("protocol", "unit", "ms"), ("protocol", "repeats", 99),
                                  ("environment", "cpu", "unknown"), ("workload", "input_sha256", "")):
            after = copy.deepcopy(record()); after[group][key] = value
            with self.assertRaises(ValueError):
                bench.compare(record(), after)

    def test_invalid_threshold_not_accepted(self):
        for threshold in (-1, 1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                bench.compare(record(), record(), min_win=threshold)

    def test_numeric_overflow_is_invalid_not_measurement_win(self):
        with self.assertRaises(ValueError):
            bench.compare(record([1e-308] * 5), record([1e308] * 5))


if __name__ == "__main__":
    unittest.main()
