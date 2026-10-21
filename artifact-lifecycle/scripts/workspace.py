#!/usr/bin/env python3
"""Owned scratch workspaces; explicit preview, evidence retention, bounded cleanup.

Linux, Python stdlib only. Not a general disk cleaner or security boundary.
"""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import time
import uuid

ROOT = Path.home() / '.cache' / 'codex-workspaces'
REPORTS = Path.home() / 'codex-reports'
RUN_ID = re.compile(r'run-[0-9a-f]{32}')
MARKER = '.codex-owned-workspaces.json'


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def real_directory(path):
    path = Path(os.path.abspath(path))
    if path.resolve() != path or not path.is_dir() or path.is_symlink():
        raise ValueError('directory missing or symlink in path: ' + str(path))
    if path.stat().st_uid != os.getuid():
        raise ValueError('directory is not owned by current user')
    return path


def managed_root(root, initialize=False):
    root = Path(os.path.abspath(root))
    if root.name != 'codex-workspaces':
        raise ValueError('root basename must be codex-workspaces')
    if root.resolve() != root:
        raise ValueError('symlink in root path')
    if initialize:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
    root = real_directory(root)
    marker = root / MARKER
    if initialize and not marker.exists() and not any(root.iterdir()):
        dump(marker, {'schema': 1, 'uid': os.getuid()})
    if marker.is_symlink() or json.loads(marker.read_text()) != {'schema': 1, 'uid': os.getuid()}:
        raise ValueError('invalid ownership marker')
    if root.stat().st_mode & 0o022:
        raise ValueError('managed root must not be writable by group/others')
    return root


def create(root, purpose):
    root = managed_root(root, initialize=True)
    run_id = 'run-' + uuid.uuid4().hex
    run = root / run_id
    run.mkdir(mode=0o700)
    (run / 'scratch').mkdir()
    (run / 'evidence').mkdir()
    dump(run / 'manifest.json', {'schema': 1, 'id': run_id, 'uid': os.getuid(),
                                'purpose': purpose, 'created': time.time()})
    (run / '.lock').touch(mode=0o600)
    return {'id': run_id, 'scratch': str(run / 'scratch'), 'evidence': str(run / 'evidence')}


@contextmanager
def locked(root, run_id):
    if not RUN_ID.fullmatch(run_id):
        raise ValueError('invalid run id')
    run = real_directory(managed_root(root) / run_id)
    before = run.stat()
    # O_NOFOLLOW prevents replacing the lock with a link outside the workspace.
    fd = os.open(run / '.lock', os.O_RDWR | os.O_NOFOLLOW)
    with os.fdopen(fd, 'r+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('workspace is in use by a wrapped command') from exc
        if run.stat().st_ino != before.st_ino or (run / 'manifest.json').is_symlink():
            raise ValueError('workspace changed')
        manifest = json.loads((run / 'manifest.json').read_text())
        if (manifest.get('schema'), manifest.get('id'), manifest.get('uid')) != (1, run_id, os.getuid()):
            raise ValueError('invalid workspace manifest')
        real_directory(run / 'scratch')
        real_directory(run / 'evidence')
        yield run, manifest


def active_processes(run):
    """Own-UID cwd/fd/argv references, without reading environments or logging argv."""
    needle = str(run)
    active = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            refs = [os.readlink(proc / 'cwd')]
            refs += [os.readlink(fd) for fd in (proc / 'fd').iterdir()]
            argv = (proc / 'cmdline').read_bytes().decode(errors='replace')
            if any(r == needle or r.startswith(needle + '/') for r in refs) or needle in argv:
                active.append(int(proc.name))
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError as exc:
            raise ValueError('cannot inspect own process ' + proc.name) from exc
    return active


def inventory(run):
    """Do not follow scratch symlinks (venvs commonly contain them). Reject mounts."""
    total = 0
    device = run.stat().st_dev
    for base, dirs, files in os.walk(run, followlinks=False):
        for name in dirs + files:
            path = Path(base) / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                continue
            if info.st_dev != device or path.is_mount():
                raise ValueError('nested mount: ' + str(path))
            total += info.st_size if stat.S_ISREG(info.st_mode) else 0
    return total


def evidence_files(run):
    evidence = run / 'evidence'
    if (evidence / 'workspace-manifest.json').exists():
        raise ValueError('workspace-manifest.json is reserved for retained metadata')
    report = evidence / 'REPORT.md'
    if report.is_symlink() or not report.is_file() or not report.read_text().strip():
        raise ValueError('nonempty evidence/REPORT.md is required before cleanup')
    total = 0
    for base, dirs, files in os.walk(evidence, followlinks=False):
        for name in dirs + files:
            path = Path(base) / name
            mode = path.lstat().st_mode
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise ValueError('evidence must contain regular files/directories only')
            if stat.S_ISREG(mode):
                total += path.stat().st_size
    if total > 64 * 1024 * 1024:
        raise ValueError('evidence exceeds 64 MiB; select a smaller reproducible evidence set')
    return total


def finish(root, run_id, reports, apply=False):
    with locked(root, run_id) as (run, manifest):
        active = active_processes(run)
        if active:
            raise ValueError('active process references workspace: ' + ','.join(map(str, active)))
        inventory(run)
        retained = evidence_files(run)
        reports = Path(os.path.abspath(reports))
        if reports.name != 'codex-reports':
            raise ValueError('reports basename must be codex-reports')
        # Validate ancestors before creating the report destination.
        if reports.resolve() != reports or reports == run or run in reports.parents:
            raise ValueError('unsafe report destination')
        destination = reports / run_id
        if destination.exists() or destination.is_symlink():
            raise ValueError('report destination already exists; keep workspace for review')
        result = {'id': run_id, 'action': 'preview', 'scratch_bytes': inventory(run / 'scratch'),
                  'retained_bytes': retained, 'report': str(destination / 'REPORT.md')}
        if not apply:
            return result
        reports.mkdir(mode=0o700, parents=True, exist_ok=True)
        real_directory(reports)
        staging = reports / ('.pending-' + run_id)
        if staging.exists() or staging.is_symlink():
            raise ValueError('pending report exists; review before retry')
        shutil.copytree(run / 'evidence', staging)
        dump(staging / 'workspace-manifest.json', manifest)
        # Verify byte-for-byte retention before destroying scratch.
        for source in (run / 'evidence').rglob('*'):
            if source.is_file() and source.read_bytes() != (staging / source.relative_to(run / 'evidence')).read_bytes():
                raise ValueError('retained evidence verification failed')
        staging.rename(destination)
        if not shutil.rmtree.avoids_symlink_attacks:
            raise ValueError('platform lacks symlink-safe rmtree; report retained, scratch not deleted')
        shutil.rmtree(run)
        result['action'] = 'cleaned'
        return result


def execute(root, run_id, command):
    with locked(root, run_id) as (run, _):
        # Pass through the real return code. A failed probe is never made green.
        return subprocess.run(command, cwd=run / 'scratch', check=False).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    commands = parser.add_subparsers(dest='action', required=True)
    start = commands.add_parser('start')
    start.add_argument('--purpose', required=True)
    end = commands.add_parser('finish')
    end.add_argument('run_id')
    end.add_argument('--reports', type=Path, default=REPORTS)
    end.add_argument('--apply', action='store_true')
    run = commands.add_parser('run')
    run.add_argument('run_id')
    run.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.action == 'start':
            result = create(args.root, args.purpose)
        elif args.action == 'finish':
            result = finish(args.root, args.run_id, args.reports, args.apply)
        else:
            command = args.command[1:] if args.command[:1] == ['--'] else args.command
            if not command:
                raise ValueError('a command is required')
            return execute(args.root, args.run_id, command)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print('REFUSED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
