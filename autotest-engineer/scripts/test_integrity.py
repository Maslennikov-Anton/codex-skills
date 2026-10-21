#!/usr/bin/env python3
"""Snapshot test/CI surfaces and flag changes for contract review; never edit tests.

Exit 0: watched files unchanged; 2: review needed; 3: check could not run.
This is a conservative change alarm, not a semantic proof of test strength.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

CONFIG = {'pyproject.toml', 'pytest.ini', 'tox.ini', 'setup.cfg', '.gitlab-ci.yml',
          '.coveragerc', 'conftest.py', 'jest.config.js', 'vitest.config.ts',
          'playwright.config.ts', 'package.json', 'Makefile'}


def watched(name):
    path = Path(name)
    lower = name.lower()
    return (path.name in CONFIG or any(p in {'tests', 'test', 'scenarios', 'suites'} for p in path.parts)
            or path.name.startswith('test_') or path.stem.endswith(('_test', '.test', '.spec'))
            or lower.startswith(('.github/workflows/', '.gitlab/'))
            or (path.parts[0] == 'scripts' and 'ci' in path.stem.lower().split('_')))


def features(data, name):
    result = {'assertions': [], 'tests': [], 'risk_syntax': []}
    if not name.endswith('.py'):
        return result
    try:
        tree = ast.parse(data)
    except (SyntaxError, UnicodeError):
        result['risk_syntax'] = ['unparsed-python']
        return result
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) or (isinstance(node, ast.Call) and (
                isinstance(node.func, ast.Attribute) and
                (node.func.attr.startswith('assert') or node.func.attr == 'raises'))):
            result['assertions'].append(hashlib.sha256(ast.dump(node).encode()).hexdigest())
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test'):
            result['tests'].append(node.name)
        if isinstance(node, ast.ExceptHandler):
            result['risk_syntax'].append('exception-handler')
        if isinstance(node, ast.Call):
            target = ast.unparse(node.func)
            if any(word in target.lower() for word in ('skip', 'xfail', 'expectedfailure',
                                                       'mock', 'patch', 'setattr')):
                result['risk_syntax'].append(target)
    return result


def scan(repo, extra=()):
    repo = repo.resolve(strict=True)
    top = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=repo, text=True).strip()
    if Path(top).resolve() != repo:
        raise ValueError('--repo must name the repository root')
    paths = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others',
                                     '--exclude-standard'], cwd=repo).decode().split('\0')
    result = {}
    for name in sorted(set(paths) | set(extra)):
        if not name or not (watched(name) or name in extra):
            continue
        path = repo / name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.resolve() != path:
            raise ValueError('symlink or unsafe watched path: ' + name)
        if not path.exists():
            continue
        if not path.is_file():
            raise ValueError('watched path is not a regular file: ' + name)
        with path.open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        detail = features(b'', name)
        if name.endswith('.py'):
            detail = (features(path.read_bytes(), name) if path.stat().st_size <= 2 * 1024 * 1024
                      else {'assertions': [], 'tests': [], 'risk_syntax': ['large-python-not-parsed']})
        result[name] = {'sha256': digest, **detail}
    return result


def snapshot(repo, extra=()):
    return {'schema': 1, 'repo': str(repo.resolve()), 'extra': list(extra),
            'files': scan(repo, extra)}


def compare(baseline, repo):
    if baseline.get('schema') != 1 or baseline.get('repo') != str(repo.resolve()):
        raise ValueError('snapshot schema/repository mismatch')
    before = baseline['files']
    after = scan(repo, baseline['extra'])
    changes = []
    for name in sorted(before.keys() | after.keys()):
        old, new = before.get(name), after.get(name)
        if old == new:
            continue
        reasons = ['watched-file-changed']
        if old is None:
            reasons = ['new-test-or-config']
        elif new is None:
            reasons = ['deleted-test-or-config']
        else:
            # Hash differences are review signals even if the total count is unchanged.
            from collections import Counter
            if Counter(old['assertions']) - Counter(new['assertions']):
                reasons.append('assertion-removed-or-rewritten')
            if Counter(old['tests']) - Counter(new['tests']):
                reasons.append('test-removed-or-renamed')
            if Counter(new['risk_syntax']) - Counter(old['risk_syntax']):
                reasons.append('new-skip-exception-or-mock-syntax')
        changes.append({'path': name, 'reasons': reasons})
    return {'status': 'needs-review' if changes else 'unchanged', 'changes': changes,
            'limitation': 'Manual contract review is required; unchanged files do not prove strong assertions.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    start = commands.add_parser('snapshot')
    start.add_argument('--output', type=Path, required=True)
    start.add_argument('--also-watch', action='append', default=[])
    check = commands.add_parser('check')
    check.add_argument('--snapshot', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'snapshot':
            data = snapshot(args.repo, args.also_watch)
            with args.output.open('x') as out:
                json.dump(data, out, indent=2)
                out.write('\n')
            print(json.dumps({'status': 'snapshot-created', 'files': len(data['files'])}))
            return 0
        result = compare(json.loads(args.snapshot.read_text()), args.repo)
        print(json.dumps(result, indent=2))
        return 2 if result['changes'] else 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print('COULD NOT CHECK: ' + str(exc), file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
