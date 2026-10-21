"""Executable invariants for frozen evaluation, truthful failures and bounded experiments."""
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'loop-engineering/scripts/experiment.py'
spec = importlib.util.spec_from_file_location('experiment', SCRIPT)
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)

EVALUATOR = '''import json, pathlib, sys, time
root = pathlib.Path('.')
candidate = json.loads((root / 'candidate.json').read_text())
mode = candidate.get('mode')
if mode == 'sleep': time.sleep(20)
if mode == 'mutate-input': (root / 'cases/expected.json').write_text('999')
if mode == 'mutate-candidate': (root / 'candidate.json').write_text('{}')
if mode == 'garbage':
    print('not a metric'); sys.exit(0)
if mode == 'large':
    print('x' * 70000); sys.exit(0)
print(json.dumps({'metric': candidate['metric']}))
if candidate.get('value', 2) != json.loads((root / 'cases/expected.json').read_text()):
    print('FAILED supported positive: expected 2', file=sys.stderr); sys.exit(7)
sys.exit(candidate.get('exit', 0))
'''


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'project'; self.root.mkdir()
        self.state = self.base / 'evidence'
        (self.root / 'cases').mkdir()
        (self.root / 'cases/expected.json').write_text('2')
        (self.root / 'evaluator.py').write_text(EVALUATOR)
        self.candidate(10)

    def candidate(self, metric, **fields):
        (self.root / 'candidate.json').write_text(json.dumps(dict(metric=metric, **fields)))

    def init(self, **overrides):
        options = dict(root=self.root, state=self.state, protected=['evaluator.py', 'cases'],
                       artifacts=['candidate.json'], command=[sys.executable, 'evaluator.py'],
                       direction='min', min_delta=1, max_experiments=3, timeout=5,
                       objective='minimize fixture score; positive value must equal 2')
        options.update(overrides)
        return experiment.initialize(**options)

    def run_candidate(self, label='candidate'):
        return experiment.evaluate(self.state, label)

    def baseline(self, **options):
        self.init(**options)
        record, code = self.run_candidate('baseline')
        self.assertEqual((record['decision'], code), ('baseline', 0))
        return record

    def test_baseline_keep_discard_compares_with_best_not_last(self):
        self.baseline()
        self.candidate(8)
        kept, code = self.run_candidate()
        self.assertEqual((kept['decision'], kept['metric'], code), ('keep', 8, 0))
        self.candidate(11)
        self.assertEqual(self.run_candidate()[0]['decision'], 'discard')
        self.candidate(9)  # Beats initial baseline, but not the retained candidate.
        self.assertEqual(self.run_candidate()[0]['decision'], 'discard')
        _, records, _ = experiment.read_state(self.state)
        self.assertEqual(len(records), 4)

    def test_max_direction_and_exact_threshold(self):
        self.baseline(direction='max', min_delta=2)
        self.candidate(12)
        self.assertEqual(self.run_candidate()[0]['decision'], 'keep')

    def test_equal_metric_is_not_improvement_even_with_zero_threshold(self):
        self.baseline(min_delta=0)
        self.assertEqual(self.run_candidate()[0]['decision'], 'discard')

    def test_gain_below_threshold_is_no_signal(self):
        self.baseline()
        self.candidate(9.5)
        record, code = self.run_candidate()
        self.assertEqual((record['decision'], code), ('no-signal', 3))

    def test_changed_evaluator_is_rejected_before_execution(self):
        self.baseline()
        (self.root / 'evaluator.py').write_text("print('{\"metric\": 0}')\n")
        record, code = self.run_candidate()
        self.assertEqual((record['decision'], record['evaluation_status'], code), ('invalid', 'not-run', 3))
        self.assertIsNone(record['metric'])

    def test_new_fixture_changes_selection_and_is_rejected(self):
        self.baseline()
        (self.root / 'cases/extra.json').write_text('2')
        self.assertEqual(self.run_candidate()[0]['decision'], 'invalid')

    def test_changed_selection_environment_is_rejected_without_recording_secrets(self):
        self.baseline()
        previous = os.environ.get('PYTEST_ADDOPTS')
        try:
            os.environ['PYTEST_ADDOPTS'] = '-k harmless_secret_value'
            record, code = self.run_candidate()
        finally:
            if previous is None: os.environ.pop('PYTEST_ADDOPTS', None)
            else: os.environ['PYTEST_ADDOPTS'] = previous
        self.assertEqual((record['decision'], record['evaluation_status'], code), ('invalid', 'not-run', 3))
        self.assertNotIn('harmless_secret_value', (self.state / 'contract.json').read_text())
        self.assertNotIn('harmless_secret_value', (self.state / 'ledger.jsonl').read_text())

    def test_missing_fixture_is_invalid_not_a_performance_win(self):
        self.baseline()
        (self.root / 'cases/expected.json').unlink()
        record, code = self.run_candidate()
        self.assertEqual((record['decision'], code), ('invalid', 3))

    def test_evaluator_cannot_change_inputs_during_green_run(self):
        self.baseline()
        self.candidate(0, mode='mutate-input', value=999)
        record, code = self.run_candidate()
        self.assertEqual((record['decision'], record['exit_code'], code), ('invalid', 0, 3))
        self.assertIsNone(record['metric'])

    def test_evaluator_cannot_change_candidate_during_run(self):
        self.baseline()
        self.candidate(0, mode='mutate-candidate')
        record, code = self.run_candidate()
        self.assertEqual((record['decision'], record['exit_code'], code), ('invalid', 0, 3))

    def test_failed_exit_survives_a_simultaneous_guard_violation(self):
        self.baseline()
        self.candidate(0, mode='mutate-input', value=2)
        record, code = self.run_candidate()
        self.assertEqual((record['decision'], record['evaluation_status'], code), ('invalid', 'failed', 7))
        self.assertIsNone(record['metric'])

    def test_relative_launcher_is_frozen_against_child_cwd(self):
        launcher = self.root / 'launcher'
        launcher.write_text('#!/bin/sh\nprintf \'{"metric":10}\\n\'\n')
        launcher.chmod(0o700)
        self.baseline(command=['./launcher'])
        launcher.write_text('#!/bin/sh\nprintf \'{"metric":0}\\n\'\n')
        record, code = self.run_candidate()
        self.assertEqual((record['decision'], record['evaluation_status'], code), ('invalid', 'not-run', 3))

    def test_product_failure_keeps_original_exit_and_raw_evidence(self):
        self.baseline()
        self.candidate(0, value=1)
        record, code = self.run_candidate()
        self.assertEqual((record['decision'], record['evaluation_status'], code), ('failed', 'failed', 7))
        self.assertEqual(record['exit_code'], 7)
        self.assertIsNone(record['metric'])
        self.assertIn('FAILED supported positive', (self.state / 'runs/0001/stderr.log').read_text())
        # Same frozen positive oracle accepts a corrected candidate; no test changes.
        self.candidate(8, value=2)
        self.assertEqual(self.run_candidate()[0]['decision'], 'keep')

    def test_cli_returns_child_failure_code(self):
        self.baseline()
        self.candidate(0, value=1)
        result = subprocess.run([sys.executable, str(SCRIPT), 'run', '--state', str(self.state),
                                 '--label', 'defect'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 7)
        self.assertEqual(json.loads(result.stdout)['evaluation_status'], 'failed')

    def test_failed_baseline_stops_optimizer(self):
        self.candidate(0, value=1)
        self.init()
        record, code = self.run_candidate('baseline')
        self.assertEqual((record['decision'], code), ('failed', 7))
        self.candidate(8)
        with self.assertRaisesRegex(ValueError, 'baseline was not valid'):
            self.run_candidate()

    def test_baseline_must_be_captured_before_artifact_edits(self):
        self.init()
        self.candidate(8)
        record, code = self.run_candidate('late baseline')
        self.assertEqual((record['decision'], code), ('invalid', 3))
        self.assertIn('baseline artifact changed', record['reason'])

    def test_budget_includes_failed_candidates_and_cannot_be_restarted(self):
        self.baseline(max_experiments=1)
        self.candidate(0, exit=9)
        self.assertEqual(self.run_candidate()[1], 9)
        with self.assertRaisesRegex(ValueError, 'budget exhausted'):
            self.run_candidate()
        with self.assertRaises(FileExistsError): self.init()
        self.assertEqual(len(experiment.read_state(self.state)[1]), 2)

    def test_timeout_is_crash_with_null_metric_and_real_signal(self):
        self.baseline(timeout=0.3)
        self.candidate(0, mode='sleep')
        record, code = self.run_candidate()
        self.assertEqual((record['decision'], record['evaluation_status'], code), ('crash', 'timeout', 124))
        self.assertLess(record['exit_code'], 0)
        self.assertIsNone(record['metric'])

    def test_launch_error_is_not_a_zero_metric(self):
        self.init(command=['/missing/command'])
        record, code = self.run_candidate()
        self.assertEqual((record['decision'], record['evaluation_status'], code), ('crash', 'launch-error', 3))
        self.assertIsNone(record['metric'])
        self.assertIsNone(record['exit_code'])

    def test_invalid_outputs_are_not_successful_metrics(self):
        for fields in ({'metric': True}, {'metric': math.nan}, {'metric': math.inf},
                       {'metric': 0, 'mode': 'garbage'}, {'metric': 0, 'mode': 'large'}):
            with self.subTest(fields=fields):
                state = self.base / f'state-{len(list(self.base.iterdir()))}'
                self.state = state
                self.candidate(10); self.baseline()
                (self.root / 'candidate.json').write_text(json.dumps(fields))
                record, code = self.run_candidate()
                self.assertEqual((record['decision'], code), ('invalid', 3))

    def test_overflow_in_metric_difference_is_invalid(self):
        self.candidate(1e308); self.init(); self.run_candidate('baseline')
        self.candidate(-1e308)
        record, code = self.run_candidate()
        self.assertEqual((record['decision'], record['metric'], code), ('invalid', None, 3))

    def test_contract_edits_are_detected(self):
        self.baseline()
        path = self.state / 'contract.json'; data = json.loads(path.read_text())
        data['min_delta'] = 0; path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'contract changed'): self.run_candidate()

    def test_ledger_edits_are_detected(self):
        self.baseline()
        path = self.state / 'ledger.jsonl'; data = json.loads(path.read_text())
        data['metric'] = 999; path.write_text(json.dumps(data) + '\n')
        with self.assertRaisesRegex(ValueError, 'ledger changed'): self.run_candidate()

    def test_incomplete_run_is_not_silently_retried(self):
        self.baseline()
        (self.state / 'runs/0001').mkdir()
        with self.assertRaisesRegex(ValueError, 'incomplete/unrecorded'): self.run_candidate()

    def test_concurrent_runner_cannot_spend_same_attempt(self):
        self.baseline()
        with (self.state / '.lock').open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError, 'active'): self.run_candidate()

    def test_invalid_contracts_are_rejected_without_creating_state(self):
        for options in ({'max_experiments': 0}, {'timeout': 0}, {'min_delta': -1},
                        {'min_delta': math.nan}, {'protected': ['../outside']},
                        {'protected': ['candidate.json']}, {'state': self.root / 'generated'}):
            with self.subTest(options=options):
                with self.assertRaises(ValueError): self.init(**options)
                self.assertFalse(self.state.exists())

    def test_symlink_inputs_and_state_are_refused(self):
        (self.root / 'cases/link').symlink_to(self.root / 'candidate.json')
        with self.assertRaisesRegex(ValueError, 'symlink'): self.init()
        (self.root / 'cases/link').unlink()
        self.state.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'): self.init()


if __name__ == '__main__':
    unittest.main()
