"""Source identity, truthful uncertainty and lossless wiki updates on real files."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'project-context/scripts/wiki.py'
spec = importlib.util.spec_from_file_location('project_wiki', SCRIPT)
wiki = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wiki)


class WikiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'wiki'; self.root.mkdir()
        (self.root / 'sources').mkdir(); (self.root / 'pages').mkdir()
        self.origin = self.base / 'spec.md'
        self.origin.write_text('Example contract\nSlots: 2\n[Original relative link](not-in-snapshot.md)\n')
        raw = self.origin.read_bytes()
        (self.root / 'sources/spec-v1.md').write_bytes(raw)
        (self.root / 'index.md').write_text('# Example\n[CI](pages/ci.md)\n')
        (self.root / 'pages/ci.md').write_text('# CI\n[Source](../sources/spec-v1.md)\n')
        self.data = {'schema': 1, 'project': 'example', 'sources': [
            {'id': 'spec-v1', 'path': 'sources/spec-v1.md', 'origin': str(self.origin),
             'version': 'v1', 'kind': 'document', 'sha256': wiki.sha(raw)}], 'claims': [
            {'id': 'slots-v1', 'key': 'ci.slots', 'scope': 'example current configured CI', 'value': '2',
             'statement': 'Configured concurrency is two slots.', 'kind': 'contract', 'page': 'pages/ci.md',
             'evidence': [{'source': 'spec-v1', 'start': 2, 'end': 2}]}]}
        self.save()
        (self.root / 'log.jsonl').write_text(json.dumps({'at': '2026-10-21T12:00:00+03:00',
                    'action': 'ingest', 'summary': 'Initial source and claim'}) + '\n')
        self.baseline = self.base / 'before.json'
        result = self.cli('snapshot', str(self.root), '--output', str(self.baseline))
        self.assertEqual(result.returncode, 0, result.stderr)

    def save(self):
        (self.root / 'catalog.json').write_text(json.dumps(self.data, indent=2))

    def log(self, summary='Reviewed source update'):
        with (self.root / 'log.jsonl').open('a') as stream:
            stream.write(json.dumps({'at': '2026-10-21T13:00:00+03:00', 'action': 'ingest', 'summary': summary}) + '\n')

    def cli(self, *arguments):
        return subprocess.run([sys.executable, str(SCRIPT), *arguments], capture_output=True, text=True)

    def lint(self, live=False):
        return wiki.analyze(self.root, self.baseline, live)

    def update_source(self):
        raw = b'Example contract\nSlots: 4\n'
        self.origin.write_bytes(raw)
        (self.root / 'sources/spec-v2.md').write_bytes(raw)
        source = copy.deepcopy(self.data['sources'][0])
        source.update(id='spec-v2', version='v2', path='sources/spec-v2.md', sha256=wiki.sha(raw))
        self.data['sources'][0].update(superseded_by='spec-v2', supersession_reason='New approved version')
        self.data['sources'].append(source)
        self.log(); self.save()

    def replacement(self):
        self.update_source()
        claim = copy.deepcopy(self.data['claims'][0])
        claim.update(id='slots-v2', value='4', statement='Configured concurrency is four slots.',
                     evidence=[{'source': 'spec-v2', 'start': 2, 'end': 2}])
        self.data['claims'][0].update(superseded_by='slots-v2', supersession_reason='Approved v2 contract')
        self.data['claims'].append(claim)
        self.save()

    def test_valid_wiki_query_has_version_hash_and_locator_without_editing_source(self):
        before = self.origin.read_bytes()
        report, code = self.lint(live=True)
        self.assertEqual((code, report['statuses']['slots-v1']), (0, 'pinned'))
        result, code = wiki.query(self.root, 'ci.slots', check_live=True)
        cite = result['matches'][0]['evidence'][0]
        self.assertEqual((code, cite['version'], cite['start'], cite['end']), (0, 'v1', 2, 2))
        self.assertEqual(cite['sha256'], wiki.sha(before))
        self.assertEqual(self.origin.read_bytes(), before)

    def test_unknown_key_is_not_an_answer(self):
        result, code = wiki.query(self.root, 'missing')
        self.assertEqual((code, result['answer_state'], result['matches']), (2, 'not-found', []))

    def test_new_source_marks_old_claim_stale_until_reviewed(self):
        self.update_source()
        report, code = self.lint()
        self.assertEqual((code, report['statuses']['slots-v1']), (2, 'stale'))
        result, code = wiki.query(self.root, 'ci.slots')
        self.assertEqual((code, result['answer_state']), (2, 'needs-review'))

    def test_explicit_supersession_preserves_historical_value_and_raw_source(self):
        raw = (self.root / 'sources/spec-v1.md').read_bytes()
        self.replacement()
        self.assertEqual(self.lint(live=True)[1], 0)
        current, code = wiki.query(self.root, 'ci.slots', check_live=True)
        self.assertEqual((code, [c['value'] for c in current['matches']]), (0, ['4']))
        history, code = wiki.query(self.root, 'ci.slots', history=True, check_live=True)
        self.assertEqual([(c['value'], c['status']) for c in history['matches']], [('2', 'superseded'), ('4', 'pinned')])
        self.assertEqual((self.root / 'sources/spec-v1.md').read_bytes(), raw)

    def test_history_record_removal_is_error(self):
        self.replacement()
        self.data['claims'].pop(0); self.save()
        self.assertEqual(self.lint()[1], 3)

    def test_rewriting_old_assertion_in_place_is_error(self):
        self.data['claims'][0]['value'] = '4'; self.log(); self.save()
        report, code = self.lint()
        self.assertEqual(code, 3)
        self.assertIn('history rewritten', report['issues'][0]['message'])

    def test_source_hash_cannot_be_rebased_to_hide_snapshot_edit(self):
        raw = b'Changed contract\nSlots: 999\n'
        (self.root / 'sources/spec-v1.md').write_bytes(raw)
        self.data['sources'][0]['sha256'] = wiki.sha(raw); self.log(); self.save()
        report, code = self.lint()
        self.assertEqual(code, 3)
        self.assertIn('history rewritten', report['issues'][0]['message'])

    def test_raw_snapshot_corruption_is_error(self):
        (self.root / 'sources/spec-v1.md').write_text('oops')
        self.assertEqual(self.lint()[1], 3)

    def test_missing_or_out_of_range_evidence_is_error(self):
        original = copy.deepcopy(self.data)
        for evidence in ([], [{'source': 'absent', 'start': 1, 'end': 1}],
                         [{'source': 'spec-v1', 'start': True, 'end': 2}],
                         [{'source': 'spec-v1', 'start': 2, 'end': 100}]):
            with self.subTest(evidence=evidence):
                self.data = copy.deepcopy(original); self.data['claims'][0]['evidence'] = evidence; self.save()
                self.assertEqual(self.lint()[1], 3)

    def test_conflicting_current_values_require_review_not_silent_selection(self):
        claim = copy.deepcopy(self.data['claims'][0]); claim.update(id='competing', value='4')
        self.data['claims'].append(claim); self.log(); self.save()
        report, code = self.lint()
        self.assertEqual(code, 2)
        self.assertEqual(set(report['statuses'].values()), {'disputed'})
        self.assertIn('conflicting-claims', [i['code'] for i in report['issues']])

    def test_different_version_scope_is_not_a_contradiction(self):
        claim = copy.deepcopy(self.data['claims'][0]); claim.update(id='other-version', value='4', scope='example v2 only')
        self.data['claims'].append(claim); self.log(); self.save()
        self.assertEqual(self.lint()[1], 0)

    def test_observed_behavior_cannot_replace_contract(self):
        claim = copy.deepcopy(self.data['claims'][0]); claim.update(id='observed', kind='observation', value='4')
        self.data['claims'].append(claim); self.log(); self.save()
        report, code = self.lint()
        self.assertEqual(code, 2)
        self.assertIn('contract-observation-gap', [i['code'] for i in report['issues']])
        self.data['claims'][0].update(superseded_by='observed', supersession_reason='Matches product now')
        self.save()
        self.assertEqual(self.lint()[1], 3)

    def test_supersession_cannot_change_key_or_form_cycle(self):
        self.replacement()
        self.data['claims'][1]['key'] = 'unrelated'; self.save()
        self.assertEqual(self.lint()[1], 3)
        self.data['claims'][1]['key'] = 'ci.slots'
        self.data['claims'][1].update(superseded_by='slots-v1', supersession_reason='cycle')
        self.save()
        self.assertEqual(self.lint()[1], 3)

    def test_source_supersession_cycle_is_error(self):
        self.update_source()
        self.data['sources'][1].update(superseded_by='spec-v1', supersession_reason='cycle'); self.save()
        self.assertEqual(self.lint()[1], 3)

    def test_log_rewrite_is_error(self):
        (self.root / 'log.jsonl').write_text(json.dumps({'at':'2026-10-21','action':'ingest','summary':'fake history'})+'\n')
        self.assertEqual(self.lint()[1], 3)

    def test_catalog_change_requires_log_append(self):
        self.data['claims'][0].update(related=['slots-v1']); self.save()
        self.assertEqual(self.lint()[1], 3)

    def test_additive_cross_references_preserve_facts_and_are_allowed_with_log(self):
        other = copy.deepcopy(self.data['claims'][0]); other.update(id='related-topic', key='ci.capacity-note')
        self.data['claims'].append(other)
        self.data['claims'][0]['related'] = ['related-topic']
        self.log('Add navigation to related claim without changing factual payload'); self.save()
        self.assertEqual(self.lint()[1], 0)

    def test_existing_cross_reference_cannot_disappear_during_update(self):
        other = copy.deepcopy(self.data['claims'][0]); other.update(id='related-topic', key='ci.capacity-note')
        self.data['claims'].append(other); self.data['claims'][0]['related'] = ['related-topic']
        self.log(); self.save()
        with_links = self.base / 'with-links.json'
        self.assertEqual(self.cli('snapshot', str(self.root), '--output', str(with_links)).returncode, 0)
        self.data['claims'][0]['related'] = []; self.log('Attempt to drop an existing relation'); self.save()
        self.assertEqual(wiki.analyze(self.root, with_links)[1], 3)

    def test_snapshot_is_write_once(self):
        before = self.baseline.read_bytes()
        result = self.cli('snapshot', str(self.root), '--output', str(self.baseline))
        self.assertEqual(result.returncode, 3)
        self.assertEqual(self.baseline.read_bytes(), before)

    def test_invalid_wiki_cannot_create_a_baseline(self):
        (self.root / 'catalog.json').write_text('[]')
        destination = self.base / 'invalid-baseline.json'
        result = self.cli('snapshot', str(self.root), '--output', str(destination))
        self.assertEqual(result.returncode, 3)
        self.assertFalse(destination.exists())

    def test_broken_navigation_is_error(self):
        (self.root / 'pages/ci.md').write_text('[Missing](missing.md)\n')
        self.assertEqual(self.lint()[1], 3)

    def test_orphan_page_requires_review(self):
        (self.root / 'pages/orphan.md').write_text('# Forgotten\n')
        report, code = self.lint()
        self.assertEqual(code, 2)
        self.assertIn('orphan-page', [i['code'] for i in report['issues']])

    def test_source_symlink_or_path_escape_is_error(self):
        path = self.root / 'sources/spec-v1.md'; path.unlink(); path.symlink_to(self.origin)
        self.assertEqual(self.lint()[1], 3)
        path.unlink()
        self.data['sources'][0]['path'] = '../spec.md'; self.save()
        self.assertEqual(self.lint()[1], 3)

    def test_navigation_cannot_read_file_outside_wiki(self):
        (self.root / 'pages/ci.md').write_text('[Outside](../../spec.md)\n')
        self.assertEqual(self.lint()[1], 3)

    def test_normalizing_parent_link_cannot_hide_a_symlink(self):
        outside = self.base / 'outside'; outside.mkdir()
        (self.root / 'pages/link').symlink_to(outside, target_is_directory=True)
        (self.root / 'pages/ci.md').write_text('[Unsafe](link/../ci.md)\n')
        self.assertEqual(self.lint()[1], 3)

    def test_live_source_drift_does_not_destroy_old_evidence_or_look_current(self):
        before = (self.root / 'sources/spec-v1.md').read_bytes()
        self.origin.write_text('new source not yet ingested')
        result, code = wiki.query(self.root, 'ci.slots', check_live=True)
        self.assertEqual((code, result['answer_state'], result['matches'][0]['status']), (2, 'needs-review', 'stale'))
        self.assertEqual((self.root / 'sources/spec-v1.md').read_bytes(), before)

    def test_reusing_snapshot_path_for_new_version_is_error(self):
        duplicate = copy.deepcopy(self.data['sources'][0]); duplicate.update(id='spec-v2', version='v2')
        self.data['sources'].append(duplicate); self.log(); self.save()
        self.assertEqual(self.lint()[1], 3)


if __name__ == '__main__':
    unittest.main()
