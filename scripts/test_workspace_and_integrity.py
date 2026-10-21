"""Safety boundaries and adversarial red/green controls for local process helpers."""
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


workspace = load('workspace', 'artifact-lifecycle/scripts/workspace.py')
integrity = load('integrity', 'autotest-engineer/scripts/test_integrity.py')


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'codex-workspaces'
        self.reports = self.base / 'codex-reports'
        self.info = workspace.create(self.root, 'test-owned')
        self.run = self.root / self.info['id']
        self.scratch = self.run / 'scratch'
        self.evidence = self.run / 'evidence'
        (self.evidence / 'REPORT.md').write_text('Observed failure; command and hash recorded.\n')
        (self.evidence / 'failure.log').write_bytes(b'FAILED expected 2 actual 1\n')
        (self.scratch / 'intermediate.bin').write_bytes(b'x' * 1000)

    def finish(self, apply=False):
        return workspace.finish(self.root, self.info['id'], self.reports, apply)

    def test_preview_preserves_everything_and_creates_no_report(self):
        result = self.finish()
        self.assertEqual(result['action'], 'preview')
        self.assertTrue((self.scratch / 'intermediate.bin').exists())
        self.assertFalse(self.reports.exists())

    def test_apply_preserves_raw_failure_and_removes_owned_scratch_only(self):
        other = self.base / 'unrelated'; other.mkdir(); (other / 'keep').write_text('mine')
        result = self.finish(True)
        report = Path(result['report'])
        self.assertEqual((report.parent / 'failure.log').read_bytes(), b'FAILED expected 2 actual 1\n')
        self.assertFalse(self.run.exists())
        self.assertEqual((other / 'keep').read_text(), 'mine')

    def test_scratch_symlink_target_survives(self):
        outside = self.base / 'product'; outside.mkdir(); (outside / 'keep').write_text('product')
        (self.scratch / 'venv-link').symlink_to(outside, target_is_directory=True)
        self.finish(True)
        self.assertEqual((outside / 'keep').read_text(), 'product')

    def test_missing_report_refuses_cleanup(self):
        (self.evidence / 'REPORT.md').unlink()
        with self.assertRaises(ValueError): self.finish(True)
        self.assertTrue(self.run.exists())

    def test_evidence_symlink_refuses(self):
        (self.evidence / 'link').symlink_to(self.base / 'secret')
        with self.assertRaises(ValueError): self.finish(True)
        self.assertTrue(self.run.exists())

    def test_root_symlink_refuses(self):
        alias = self.base / 'alias'; alias.mkdir()
        link = alias / 'codex-workspaces'; link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError): workspace.create(link, 'unsafe')

    def test_symlink_parent_refuses_before_any_creation(self):
        target = self.base / 'outside'; target.mkdir()
        alias = self.base / 'alias'; alias.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError): workspace.create(alias / 'codex-workspaces', 'unsafe')
        self.assertEqual(list(target.iterdir()), [])

    def test_reserved_metadata_refuses_before_archiving(self):
        (self.evidence / 'workspace-manifest.json').write_text('important evidence')
        with self.assertRaises(ValueError): self.finish(True)
        self.assertFalse(self.reports.exists())

    def test_unmarked_existing_directory_is_not_adopted(self):
        root = self.base / 'legacy' / 'codex-workspaces'; root.mkdir(parents=True)
        (root / 'user-data').write_text('do not delete')
        with self.assertRaises(FileNotFoundError): workspace.create(root, 'unsafe')
        self.assertFalse((root / workspace.MARKER).exists())

    def test_run_id_escape_refuses(self):
        with self.assertRaises(ValueError): workspace.finish(self.root, '../outside', self.reports, True)

    def test_manifest_owner_mismatch_refuses(self):
        manifest = self.run / 'manifest.json'; data = json.loads(manifest.read_text())
        data['uid'] += 1; manifest.write_text(json.dumps(data))
        with self.assertRaises(ValueError): self.finish(True)

    def test_active_lock_refuses(self):
        with workspace.locked(self.root, self.info['id']):
            with self.assertRaises(ValueError): self.finish(True)

    def test_external_process_in_scratch_refuses(self):
        proc = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'], cwd=self.scratch)
        try:
            with self.assertRaisesRegex(ValueError, 'active process'): self.finish(True)
        finally:
            proc.terminate(); proc.wait(timeout=5)
        self.assertTrue(self.run.exists())

    def test_real_command_failure_exit_code_is_preserved(self):
        self.assertEqual(workspace.execute(self.root, self.info['id'],
                         [sys.executable, '-c', 'raise SystemExit(7)']), 7)

    def test_existing_report_is_never_overwritten(self):
        destination = self.reports / self.info['id']; destination.mkdir(parents=True)
        (destination / 'REPORT.md').write_text('earlier report')
        with self.assertRaises(ValueError): self.finish(True)
        self.assertEqual((destination / 'REPORT.md').read_text(), 'earlier report')
        self.assertTrue(self.scratch.exists())


class IntegrityTests(unittest.TestCase):
    TEST = ('import unittest\nfrom artifact import value\nclass Contract(unittest.TestCase):\n'
            '    def test_supported(self):\n        self.assertEqual(value(), 2)\n')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        (self.repo / 'tests').mkdir()
        self.test = self.repo / 'tests/test_contract.py'; self.test.write_text(self.TEST)
        (self.repo / 'artifact.py').write_text('def value():\n    return 1\n')
        (self.repo / 'pytest.ini').write_text('[pytest]\n')
        # Baseline includes dirty and newly created nonignored files without committing.
        self.before = integrity.snapshot(self.repo)

    def run_fixture(self):
        return subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests'],
                              cwd=self.repo, capture_output=True, text=True)

    def test_buggy_artifact_stays_red_and_baseline_is_unchanged(self):
        run = self.run_fixture()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('1 != 2', run.stderr)
        self.assertEqual(integrity.compare(self.before, self.repo)['status'], 'unchanged')

    def test_product_fix_passes_same_unchanged_oracle(self):
        (self.repo / 'artifact.py').write_text('def value():\n    return 2\n')
        self.assertEqual(self.run_fixture().returncode, 0)
        self.assertEqual(integrity.compare(self.before, self.repo)['changes'], [])

    def test_green_by_rewritten_expected_value_requires_review(self):
        self.test.write_text(self.TEST.replace('value(), 2', 'value(), 1'))
        self.assertEqual(self.run_fixture().returncode, 0)
        changes = integrity.compare(self.before, self.repo)['changes']
        self.assertIn('assertion-removed-or-rewritten', changes[0]['reasons'])

    def test_skip_xfail_catch_mock_and_assert_true_are_reviewed(self):
        variants = [self.TEST.replace('    def test_', '    @unittest.skip("bug")\n    def test_'),
                    self.TEST.replace('self.assertEqual(value(), 2)', 'assert True'),
                    self.TEST + '\ndef test_hidden():\n    try:\n        assert value() == 2\n    except Exception:\n        pass\n',
                    self.TEST + '\nimport pytest\n@pytest.mark.xfail\ndef test_x():\n    assert value() == 2\n',
                    self.TEST + '\nfrom unittest.mock import patch\n@patch("artifact.value", return_value=2)\ndef test_mock(mock):\n    assert mock() == 2\n']
        for source in variants:
            with self.subTest(source=source):
                self.test.write_text(source)
                self.assertEqual(integrity.compare(self.before, self.repo)['status'], 'needs-review')

    def test_deleted_test_and_reduced_selection_are_reviewed(self):
        self.test.unlink()
        (self.repo / 'pytest.ini').write_text('[pytest]\naddopts = -k nothing\n')
        changes = integrity.compare(self.before, self.repo)['changes']
        self.assertEqual({c['path'] for c in changes}, {'pytest.ini', 'tests/test_contract.py'})
        self.assertIn('deleted-test-or-config', changes[1]['reasons'])

    def test_extra_custom_runner_is_watched(self):
        (self.repo / 'runner.py').write_text('exit(1)\n')
        before = integrity.snapshot(self.repo, ['runner.py'])
        (self.repo / 'runner.py').write_text('exit(0)\n')
        self.assertEqual(integrity.compare(before, self.repo)['changes'][0]['path'], 'runner.py')

    def test_snapshot_does_not_store_source_or_secrets(self):
        self.test.write_text(self.TEST + '\nSECRET = "synthetic-secret"\n')
        self.assertNotIn('synthetic-secret', json.dumps(integrity.snapshot(self.repo)))

    def test_symlink_cannot_read_outside_repository(self):
        self.test.unlink(); self.test.symlink_to('/etc/passwd')
        with self.assertRaises(ValueError): integrity.snapshot(self.repo)

    def test_cli_change_alarm_exit_two(self):
        baseline = self.repo / 'baseline.json'; baseline.write_text(json.dumps(self.before))
        self.test.write_text(self.TEST.replace('value(), 2', 'value(), 1'))
        result = subprocess.run([sys.executable, str(ROOT / 'autotest-engineer/scripts/test_integrity.py'),
                                 '--repo', str(self.repo), 'check', '--snapshot', str(baseline)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'needs-review')


if __name__ == '__main__':
    unittest.main()
