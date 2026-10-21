#!/usr/bin/env python3
"""One bounded evaluation at a time, with frozen inputs and an evidence ledger (Linux, stdlib)."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import shutil
import stat
import subprocess
import sys
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def plain_path(path):
    path = Path(os.path.abspath(path))
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError(f"symlink path refused: {path}")
    return path


def fingerprint(root, selectors):
    """Exact files or whole directory trees, including membership and executable mode."""
    result = {}
    for selector in selectors:
        relative = Path(selector)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError(f"expected relative path inside root: {selector}")
        path = plain_path(root / relative)
        paths = [path]
        if path.is_dir():
            paths += sorted(path.rglob('*'))
        for item in paths:
            plain_path(item)
            mode = item.stat().st_mode
            key = item.relative_to(root).as_posix()
            if stat.S_ISDIR(mode):
                result[key] = {'kind': 'directory'}
            elif stat.S_ISREG(mode):
                sha = hashlib.sha256()
                with item.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        sha.update(block)
                result[key] = {'sha256': sha.hexdigest(), 'mode': stat.S_IMODE(mode)}
            else:
                raise ValueError(f"non-regular input refused: {item}")
    return result


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def environment(command, root):
    # Store one digest, never raw environment values (which may contain credentials).
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    stable = {k: v for k, v in env.items() if k not in ('PWD', 'OLDPWD', 'SHLVL', '_')}
    # Popen resolves a relative launcher/PATH against its child cwd, not this helper's cwd.
    search = os.pathsep.join(str(root / part) if not os.path.isabs(part) else part
                            for part in os.get_exec_path(env))
    launcher_name = str(root / command[0]) if '/' in command[0] and not os.path.isabs(command[0]) else command[0]
    executable = shutil.which(launcher_name, path=search)
    launcher = None
    if executable:
        path = Path(executable).resolve()
        launcher = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return {'environment_sha256': digest(stable), 'launcher': launcher, 'kernel': list(os.uname())}


def initialize(root, state, protected, artifacts, command, direction, min_delta,
               max_experiments, timeout, objective):
    root, state = plain_path(root), plain_path(state)
    if not root.is_dir() or state.is_relative_to(root):
        raise ValueError('root must exist; state must be outside root (owned evidence directory)')
    if not protected or not artifacts or not command or not objective.strip():
        raise ValueError('protected inputs, artifacts, command and objective are required')
    if direction not in ('min', 'max') or not math.isfinite(min_delta) or min_delta < 0:
        raise ValueError('invalid metric direction/min_delta')
    if type(max_experiments) is not int or max_experiments < 1 or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('explicit positive candidate limit and timeout required')
    frozen, initial = fingerprint(root, protected), fingerprint(root, artifacts)
    if set(frozen) & set(initial):
        raise ValueError('protected inputs and mutable artifacts overlap')
    contract = dict(schema=1, root=str(root), protected=protected, artifacts=artifacts,
                    command=command, direction=direction, min_delta=min_delta,
                    max_experiments=max_experiments, timeout=timeout, objective=objective,
                    frozen=frozen, initial_artifact=initial, environment=environment(command, root))
    contract['digest'] = digest(contract)
    state.mkdir(parents=True, exist_ok=False)
    write_json(state / 'contract.json', contract)
    (state / 'ledger.jsonl').touch(exist_ok=False)
    (state / 'runs').mkdir()
    return contract


@contextmanager
def locked(state):
    plain_path(state)
    with plain_path(state / '.lock').open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('another evaluation is active') from None
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def read_state(state):
    for name in ('contract.json', 'ledger.jsonl', 'runs'):
        plain_path(state / name)
    contract = json.loads((state / 'contract.json').read_text())
    unsigned = {k: v for k, v in contract.items() if k != 'digest'}
    if contract['digest'] != digest(unsigned):
        raise ValueError('contract changed; do not rebase the evaluator')
    records, previous = [], contract['digest']
    for line in (state / 'ledger.jsonl').read_text().splitlines():
        record = json.loads(line)
        unsigned = {k: v for k, v in record.items() if k != 'digest'}
        if (record['previous'] != previous or record['digest'] != digest(unsigned)
                or record['attempt'] != len(records)):
            raise ValueError('ledger changed or is out of order')
        records.append(record)
        previous = record['digest']
    if {p.name for p in (state / 'runs').iterdir()} != {f'{i:04d}' for i in range(len(records))}:
        raise ValueError('incomplete/unrecorded attempt: preserve evidence and investigate before continuing')
    return contract, records, previous


def same_inputs(contract):
    return (fingerprint(Path(contract['root']), contract['protected']) == contract['frozen']
            and environment(contract['command'], Path(contract['root'])) == contract['environment'])


def evaluate(state, label):
    state = plain_path(state)
    with locked(state):
        contract, records, previous = read_state(state)
        if len(records) >= contract['max_experiments'] + 1:
            raise ValueError('candidate budget exhausted (baseline is additional)')
        if records and records[0]['decision'] != 'baseline':
            raise ValueError('baseline was not valid; stop optimization and investigate the failure')
        root = Path(contract['root'])
        attempt = len(records)
        output = state / 'runs' / f'{attempt:04d}'
        output.mkdir()
        record = dict(attempt=attempt, label=label, previous=previous,
                      decision='invalid', evaluation_status='not-run', exit_code=None,
                      metric=None, elapsed_seconds=0, reason='', artifact=None)
        process = None
        started = time.monotonic()
        try:
            before = fingerprint(root, contract['artifacts'])
            record['artifact'] = before
            if not same_inputs(contract):
                record['reason'] = 'protected evaluator/inputs/environment changed before run'
            elif attempt == 0 and before != contract['initial_artifact']:
                record['reason'] = 'baseline artifact changed after init'
            else:
                timed_out = False
                with (output / 'stdout.log').open('xb') as stdout, (output / 'stderr.log').open('xb') as stderr:
                    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
                    try:
                        process = subprocess.Popen(contract['command'], cwd=root, env=env,
                                                   stdout=stdout, stderr=stderr, start_new_session=True)
                    except OSError:
                        record.update(decision='crash', evaluation_status='launch-error')
                        raise
                    try:
                        process.wait(timeout=contract['timeout'])
                    except subprocess.TimeoutExpired:
                        timed_out = True
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    except BaseException:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                        raise
                record['exit_code'] = process.returncode
                record['evaluation_status'] = ('timeout' if timed_out else
                                                'passed' if process.returncode == 0 else 'failed')
                if not same_inputs(contract) or fingerprint(root, contract['artifacts']) != before:
                    record['reason'] = 'protected inputs or candidate changed during run'
                elif timed_out:
                    record.update(decision='crash', reason='evaluation exceeded timeout')
                elif process.returncode != 0:
                    record.update(decision='failed', reason='original evaluator failure; metric is not usable')
                else:
                    # One small JSON object on stdout; diagnostics belong on stderr.
                    if (output / 'stdout.log').stat().st_size > 65536:
                        raise ValueError('metric output exceeds 64 KiB')
                    metric = json.loads((output / 'stdout.log').read_text())['metric']
                    if type(metric) not in (int, float) or not math.isfinite(metric):
                        raise ValueError('metric must be a finite number, not a boolean')
                    record['metric'] = metric
                    if attempt == 0:
                        record['decision'] = 'baseline'
                    else:
                        best = next(r for r in reversed(records) if r['decision'] in ('keep', 'baseline'))
                        gain = (best['metric'] - metric) if contract['direction'] == 'min' else (metric - best['metric'])
                        if not math.isfinite(gain):
                            raise ValueError('non-finite improvement; rescale the metric before a new session')
                        if gain > 0 and gain >= contract['min_delta']:
                            record['decision'] = 'keep'
                        elif gain > 0:
                            record.update(decision='no-signal', reason='gain below minimum meaningful delta')
                        else:
                            record.update(decision='discard', reason='no improvement over incumbent')
        except (ValueError, OSError, KeyError, TypeError, OverflowError) as error:
            record['reason'] = str(error)
        if record['decision'] in ('invalid', 'failed', 'crash'):
            record['metric'] = None
        record['elapsed_seconds'] = round(time.monotonic() - started, 6)
        record['digest'] = digest(record)
        write_json(output / 'result.json', record)
        with (state / 'ledger.jsonl').open('a') as stream:
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        code = record['exit_code']
        if record['evaluation_status'] == 'timeout':
            return record, 124
        if code is not None and code != 0:
            return record, code if code > 0 else 128 - code
        return record, 0 if record['decision'] in ('baseline', 'keep', 'discard') else 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    init = sub.add_parser('init')
    init.add_argument('--root', type=Path, required=True)
    init.add_argument('--state', type=Path, required=True)
    init.add_argument('--protected', action='append', required=True)
    init.add_argument('--artifact', action='append', required=True)
    init.add_argument('--direction', choices=('min', 'max'), required=True)
    init.add_argument('--min-delta', type=float, required=True)
    init.add_argument('--max-experiments', type=int, required=True)
    init.add_argument('--timeout', type=float, required=True)
    init.add_argument('--objective', required=True)
    init.add_argument('command', nargs=argparse.REMAINDER)
    run = sub.add_parser('run')
    run.add_argument('--state', type=Path, required=True)
    run.add_argument('--label', required=True)
    args = parser.parse_args()
    try:
        if args.action == 'init':
            command = args.command[1:] if args.command[:1] == ['--'] else args.command
            result = initialize(args.root, args.state, args.protected, args.artifact, command,
                                args.direction, args.min_delta, args.max_experiments, args.timeout, args.objective)
            code = 0
        else:
            result, code = evaluate(args.state, args.label)
        print(json.dumps(result, indent=2, allow_nan=False))
        return code
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
