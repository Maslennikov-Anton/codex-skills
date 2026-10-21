from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import check_reference_sources as provenance
import evaluate_skill_behavior as behavior


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_ingestion", ROOT / "allure-testops-operations/scripts/verify_ingestion.py")
ingestion = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ingestion)


class BehaviorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cases = behavior.load_cases(behavior.CASES)
        self.skills = {"autotest-engineer": {"text": "---\nname: autotest-engineer\ndescription: test\n---\n# Tests\nKeep supported positive expectations truthful.\n", "sha256": "sample"}}

    def trace(self, events):
        path = self.root / "trace.jsonl"
        path.write_text("\n".join(json.dumps(row) for row in events))
        return path

    def read_event(self, *, command="cat /skills/autotest-engineer/SKILL.md", output=None, exit_code=0):
        return {"type": "item.completed", "item": {"type": "command_execution", "command": command,
                "aggregated_output": self.skills["autotest-engineer"]["text"] if output is None else output,
                "exit_code": exit_code}}

    def prepared(self, case_id):
        case = copy.deepcopy(self.cases[case_id])
        run = self.root / case_id
        behavior.prepare(case, run, ROOT, "candidate", "test-model", "test-harness")
        return case, run

    def test_actual_successful_skill_read_is_observed(self):
        path = self.trace([self.read_event(), {"type": "turn.completed", "usage": {"input_tokens": 10}}])
        observed = behavior.read_trace(path, self.skills)
        self.assertEqual(observed["loaded_skills"], ["autotest-engineer"])
        self.assertTrue(observed["trace_complete"])
        self.assertEqual(observed["usage"]["input_tokens"], 10)

    def test_prose_echo_and_failed_read_do_not_count(self):
        events = [
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Used autotest-engineer"}},
            self.read_event(command="echo /skills/autotest-engineer/SKILL.md"),
            self.read_event(exit_code=1),
            self.read_event(output="/skills/autotest-engineer/SKILL.md"),
        ]
        self.assertEqual(behavior.read_trace(self.trace(events), self.skills)["loaded_skills"], [])

    def test_incomplete_or_failed_turn_is_not_success(self):
        for end in ([], [{"type": "turn.failed"}], [{"type": "turn.completed"}, {"type": "error"}]):
            with self.subTest(end=end):
                self.assertFalse(behavior.read_trace(self.trace([self.read_event(), *end]), self.skills)["trace_complete"])

    def test_truthful_oracle_detects_product_bug_and_viewer_mutation(self):
        case, run = self.prepared("truthful-positive-oracle")
        (run / "workspace/test_access.py").write_text(
            "import unittest\nfrom access import can_edit\n"
            "class Contract(unittest.TestCase):\n"
            "    def test_owner(self): self.assertTrue(can_edit('owner'))\n"
            "    def test_viewer(self): self.assertFalse(can_edit('viewer'))\n")
        status, evidence = behavior.grade(case, run / "workspace")
        self.assertEqual(status, "pass")
        self.assertEqual(evidence["buggy_product"]["failures"], 1)
        self.assertEqual(evidence["contract_implementation"]["failures"], 0)
        self.assertEqual(evidence["unauthorized_viewer_mutation"]["failures"], 1)

    def test_empty_skipped_or_weakened_tests_do_not_pass(self):
        case, run = self.prepared("truthful-positive-oracle")
        samples = (
            "",
            "import unittest\n@unittest.skip('bug')\nclass T(unittest.TestCase):\n def test_bug(self): self.fail()\n",
            "import unittest\nclass T(unittest.TestCase):\n def test_green(self): self.assertTrue(True)\n",
            "import unittest\nfrom access import can_edit\nclass T(unittest.TestCase):\n def test_owner(self): self.assertTrue(can_edit('owner'))\n",
            "syntax error !!!",
        )
        for sample in samples:
            with self.subTest(sample=sample[:25]):
                (run / "workspace/test_access.py").write_text(sample)
                self.assertEqual(behavior.grade(case, run / "workspace")[0], "fail")

    def test_constraint_violation_overrides_passing_tests(self):
        _, run = self.prepared("execute-plan-recover-check")
        (run / "workspace/calculator.py").write_text("def magnitude(value): return abs(value)\n")
        trace = self.trace([{"type": "turn.completed"}])
        before = behavior.score(run, trace)
        self.assertEqual(before["outcome"], "pass")
        self.assertEqual(before["routing"], "fail")  # No observed required read.
        (run / "workspace/unrequested.txt").write_text("extra")
        after = behavior.score(run, trace)
        self.assertEqual(after["outcome"], "fail")
        self.assertEqual(after["constraint_violations"], ["unrequested.txt"])

    def test_manual_outcome_stays_unreviewed_and_no_skill_control_detects_reads(self):
        _, run = self.prepared("no-skill-control")
        text = (ROOT / "autotest-engineer/SKILL.md").read_text()
        trace = self.trace([self.read_event(output=text), {"type": "turn.completed"}])
        report = behavior.score(run, trace)
        self.assertEqual(report["outcome"], "needs_review")
        self.assertEqual(report["routing"], "fail")
        self.assertEqual(report["forbidden_skill_reads"], ["autotest-engineer"])

    def test_incomplete_trace_is_inconclusive_even_if_artifact_passes(self):
        _, run = self.prepared("execute-plan-recover-check")
        (run / "workspace/calculator.py").write_text("def magnitude(value): return abs(value)\n")
        report = behavior.score(run, self.trace([]))
        self.assertEqual((report["routing"], report["outcome"]), ("inconclusive", "inconclusive"))

    def test_prepare_preserves_existing_run_and_blocks_path_escape(self):
        _, run = self.prepared("no-skill-control")
        with self.assertRaises(FileExistsError):
            behavior.prepare(self.cases["no-skill-control"], run, ROOT, "x", "m", "h")
        with self.assertRaises(ValueError):
            behavior.safe_path(run, "../../escape")

    def test_grader_timeout_is_not_pass(self):
        _, run = self.prepared("execute-plan-recover-check")
        import subprocess
        with patch.object(behavior, "run_unittest", side_effect=subprocess.TimeoutExpired("python", 30)):
            report = behavior.score(run, self.trace([{"type": "turn.completed"}]))
        self.assertEqual(report["outcome"], "inconclusive")

    def test_comparison_rejects_changed_model_harness_or_fixture(self):
        _, run = self.prepared("no-skill-control")
        report = behavior.score(run, self.trace([{"type": "turn.completed"}]))
        for field in ("model", "harness", "case_sha256"):
            changed = {**report, field: "different", "variant": "before"}
            with self.subTest(field=field), self.assertRaises(ValueError):
                behavior.compare([report, changed])

    def test_missing_usage_does_not_become_zero_cost(self):
        _, run = self.prepared("no-skill-control")
        report = behavior.score(run, self.trace([{"type": "turn.completed"}]))
        summary = behavior.compare([report])[0]
        self.assertIsNone(summary["input_tokens"]["mean"])
        self.assertEqual(summary["input_tokens"]["measured_runs"], 0)

    def test_comparison_rejects_duplicate_trace_and_mixed_corpus(self):
        _, run = self.prepared("no-skill-control")
        report = behavior.score(run, self.trace([{"type": "turn.completed"}]))
        with self.assertRaisesRegex(ValueError, "Duplicate trace"):
            behavior.compare([report, report])
        changed = {**report, "corpus_sha256": "different", "trace_sha256": "another-run"}
        with self.assertRaisesRegex(ValueError, "Mixed skill"):
            behavior.compare([report, changed])


class FakeClient:
    def __init__(self, results=None, attachments=None):
        self.results = results or []
        self.attachments = attachments or []
        self.closed = True
        self.payload = b"evidence"
        self.calls = []

    def get(self, path, **query):
        self.calls.append((path, query))
        if path.startswith("/api/launch/"):
            return {"closed": self.closed}
        rows = self.results if path == "/api/testresult" else self.attachments
        # Deliberately one row/page, so a successful audit must consume all pages.
        page = query["page"]
        return {"content": rows[page:page+1], "last": page + 1 >= len(rows), "totalElements": len(rows)}

    def content(self, attachment_id):
        return self.payload


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.local = {"uuid": "execution", "name": "case", "fullName": "suite.case", "start": 1, "stop": 2, "status": "failed",
                      "steps": [{"name": "click", "attachments": [{"name": "screen", "type": "image/png", "source": "screen.png"}]}]}
        self.write_result()
        (self.root / "screen.png").write_bytes(b"evidence")
        self.remote = {**self.local, "id": 10}
        self.attachment = {"id": 20, "name": "screen", "contentType": "image/png", "contentLength": 8, "missed": False}
        self.client = FakeClient([self.remote], [self.attachment])

    def write_result(self):
        (self.root / "execution-result.json").write_text(json.dumps(self.local))

    def verify(self, **kwargs):
        return ingestion.verify(self.client, 7, self.root, **kwargs)

    def test_failed_product_result_can_have_complete_delivery(self):
        report = self.verify()
        self.assertEqual(report["state"], "verified_closed")
        self.assertEqual(report["attachments_verified"], 1)
        self.assertEqual(report["product_statuses"], {"failed": 1})

    def test_open_launch_only_proves_snapshot(self):
        self.client.closed = False
        self.assertEqual(self.verify()["state"], "verified_snapshot_open_launch")

    def test_all_pages_and_retries_checked(self):
        retry = {**self.local, "start": 3, "stop": 4}
        (self.root / "retry-result.json").write_text(json.dumps(retry))
        self.client.results.append({**retry, "id": 11})
        report = self.verify()
        self.assertEqual(report["results_verified"], 2)
        self.assertTrue(any(query.get("page") == 1 for _, query in self.client.calls))

    def test_missing_extra_and_duplicate_results_rejected(self):
        variants = ([], [self.remote, {**self.remote, "id": 11}], [{**self.remote, "start": 5}])
        for rows in variants:
            with self.subTest(rows=rows), self.assertRaises(ingestion.AuditError):
                self.client.results = rows
                self.verify()

    def test_shared_launch_extra_results_are_explicit(self):
        self.client.results.append({**self.remote, "id": 11, "start": 3})
        with self.assertRaises(ingestion.AuditError):
            self.verify()
        self.assertEqual(self.verify(allow_extra=True)["extra_results"], 1)

    def test_status_mismatch_rejected(self):
        self.client.results[0] = {**self.remote, "status": "passed"}
        with self.assertRaises(ingestion.AuditError):
            self.verify()

    def test_missing_attachment_and_corrupt_same_size_bytes_rejected(self):
        self.client.attachments = []
        with self.assertRaises(ingestion.AuditError):
            self.verify()
        self.client.attachments = [self.attachment]
        self.client.payload = b"tampered"
        with self.assertRaises(ingestion.AuditError):
            self.verify()

    def test_attachment_missing_metadata_and_missing_content_rejected(self):
        variants = [{**self.attachment, "missed": True}, {k: v for k, v in self.attachment.items() if k != "contentLength"},
                    {k: v for k, v in self.attachment.items() if k != "missed"}]
        for row in variants:
            with self.subTest(row=row), self.assertRaises(ingestion.AuditError):
                self.client.attachments = [row]
                self.verify()

    def test_pagination_repeat_truncation_and_unknown_schema_rejected(self):
        bad = [
            {"content": [{"id": 1}], "last": True, "totalElements": 2},
            {"content": [{"id": 1}], "last": False, "totalElements": 3},
            {"content": [], "last": False, "totalElements": 1},
            {"content": [], "last": True},
            {"content": [], "last": "true", "totalElements": 0},
        ]
        for data in bad:
            with self.subTest(data=data), patch.object(self.client, "get", return_value=data), self.assertRaises(ingestion.AuditError):
                ingestion.pages(self.client, "/api/testresult")

    def test_changing_page_total_rejected(self):
        replies = [{"content": [{"id": 1}], "last": False, "totalElements": 2},
                   {"content": [{"id": 2}], "last": True, "totalElements": 3}]
        with patch.object(self.client, "get", side_effect=replies), self.assertRaises(ingestion.AuditError):
            ingestion.pages(self.client, "/api/testresult")

    def test_empty_and_ambiguous_local_batch_rejected(self):
        (self.root / "execution-result.json").unlink()
        with self.assertRaises(ingestion.AuditError):
            self.verify()
        self.write_result()
        (self.root / "duplicate-result.json").write_text(json.dumps(self.local))
        with self.assertRaises(ingestion.AuditError):
            self.verify()

    def test_local_attachment_escape_rejected(self):
        for source in ("../outside.png", "/etc/passwd", "missing.png"):
            with self.subTest(source=source), self.assertRaises(ingestion.AuditError):
                ingestion.local_file(self.root, source)

    def test_container_fixture_attachments_not_silently_ignored(self):
        (self.root / "fixture-container.json").write_text(json.dumps({"children": ["execution"],
            "befores": [{"attachments": [{"name": "fixture", "source": "screen.png", "type": "image/png"}]}]}))
        with self.assertRaisesRegex(ingestion.AuditError, "Container fixture"):
            self.verify()

    def test_changing_launch_state_rejected(self):
        original = self.client.get
        calls = 0
        def changed(path, **query):
            nonlocal calls
            if path.startswith("/api/launch/"):
                calls += 1
                return {"closed": calls > 1}
            return original(path, **query)
        with patch.object(self.client, "get", side_effect=changed), self.assertRaises(ingestion.AuditError):
            self.verify()

    def test_credentials_literal_only_env_overrides_and_https_required(self):
        path = self.root / "credentials.env"
        path.write_text("export ALLURE_TESTOPS_URL='https://example.test'\nALLURE_TESTOPS_TOKEN='test-token'\n")
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(ingestion.credentials(path), ("https://example.test", "test-token"))
            with patch.dict("os.environ", {"ALLURE_TESTOPS_TOKEN": "override"}):
                self.assertEqual(ingestion.credentials(path)[1], "override")
            for invalid in ("ALLURE_TESTOPS_TOKEN=$(command)", "ALLURE_TESTOPS_TOKEN=`command`", "ALLURE_TESTOPS_URL=http://example.test"):
                path.write_text("ALLURE_TESTOPS_URL=https://example.test\nALLURE_TESTOPS_TOKEN=test\n" + invalid)
                with self.subTest(invalid=invalid), self.assertRaises(ingestion.AuditError):
                    ingestion.credentials(path)

    def test_redirects_disabled(self):
        self.assertIsNone(ingestion.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.test"))


class ProvenanceTests(unittest.TestCase):
    def test_match_drift_and_missing_keep_semantic_status_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.txt"
            source.write_text("before")
            manifest = {"schema_version": 1, "source_root": str(root), "captured_at": "2026-10-21", "captured_commit": "abc",
                        "references": [{"reference": "reference.md", "semantic_review": "not reviewed",
                                        "source_sha256": {"source.txt": hashlib.sha256(source.read_bytes()).hexdigest()}}]}
            result = provenance.check(manifest)[0]
            self.assertEqual(result["fingerprints"], "match")
            self.assertEqual(result["semantic_review"], "not reviewed")
            source.write_text("after")
            self.assertEqual(provenance.check(manifest)[0]["drift"][0]["state"], "changed")
            source.unlink()
            self.assertEqual(provenance.check(manifest)[0]["drift"][0]["state"], "missing")

    def test_source_root_can_be_relocated_but_paths_cannot_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = {"schema_version": 1, "source_root": "/absent", "captured_at": "date", "captured_commit": "abc",
                        "references": [{"reference": "r", "semantic_review": "not reviewed", "source_sha256": {"../escape": "a" * 64}}]}
            with self.assertRaises(ValueError):
                provenance.check(manifest, root)

    def test_empty_or_unknown_provenance_cannot_pass(self):
        for manifest in ({}, {"schema_version": 1, "references": []}, {"schema_version": 2, "references": [{}]}):
            with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                provenance.check(manifest)


if __name__ == "__main__":
    unittest.main()
