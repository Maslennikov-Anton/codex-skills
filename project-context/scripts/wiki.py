#!/usr/bin/env python3
"""Read-only project-wiki lint/query and a write-once pre-update snapshot; Python stdlib."""
import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ID = re.compile(r'[a-z][a-z0-9_-]{0,63}')
LINK = re.compile(r'!?\[[^\]\n]*\]\(([^)\n]+)\)')
KINDS = {'contract', 'implementation', 'observation', 'inference'}
LIMITS = 'Structural provenance checks; no semantic truth, product pass, or external-service verification.'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def local(root, relative, prefix=None):
    path = Path(relative)
    require(not path.is_absolute() and '..' not in path.parts and path.parts,
            f'expected a relative path within wiki: {relative}')
    if prefix:
        require(path.parts[0] == prefix, f'expected {prefix}/ path: {relative}')
    result = root / path
    require(not any(p.is_symlink() for p in (result, *result.parents)), f'symlink refused: {relative}')
    require(result.is_file(), f'missing regular file: {relative}')
    return result


def records(items, label):
    require(isinstance(items, list), f'{label} must be a list')
    result = {}
    for item in items:
        require(isinstance(item, dict) and isinstance(item.get('id'), str)
                and ID.fullmatch(item['id']), f'invalid {label} ID')
        require(item['id'] not in result, f'duplicate {label} ID: {item["id"]}')
        result[item['id']] = item
    return result


def successors(items, fields):
    for name, item in items.items():
        target = item.get('superseded_by')
        if target is None:
            require(not item.get('supersession_reason'), f'{name}: reason without successor')
            continue
        require(target in items and target != name, f'{name}: missing/self successor')
        require(text(item.get('supersession_reason')), f'{name}: missing supersession reason')
        require(all(item.get(f) == items[target].get(f) for f in fields),
                f'{name}: successor changes claim/source identity or authority')
        seen, cursor = {name}, target
        while cursor is not None:
            require(cursor not in seen, f'{name}: successor cycle')
            seen.add(cursor)
            cursor = items[cursor].get('superseded_by')


def check_history(catalog, log, baseline):
    previous = json.loads(Path(baseline).read_text())
    require(previous.get('schema') == 1 and previous['catalog']['project'] == catalog['project'],
            'baseline belongs to another project/schema')
    length = previous['log_bytes']
    require(len(log) >= length and sha(log[:length]) == previous['log_sha256'], 'log history changed/truncated')
    if catalog != previous['catalog']:
        require(len(log) > length, 'catalog changed without an appended log entry')
    for group in ('sources', 'claims'):
        current = records(catalog[group], group)
        for old in previous['catalog'][group]:
            require(old['id'] in current, f'history removed: {old["id"]}')
            new = current[old['id']]
            # Preserve factual payload; allow explained supersession and additive cross-references.
            mutable = {'superseded_by', 'supersession_reason'}
            if group == 'claims':
                mutable.add('related')
                require(set(old.get('related', [])).issubset(new.get('related', [])),
                        f'historical cross-reference removed: {old["id"]}')
            require({k: v for k, v in old.items() if k not in mutable} ==
                    {k: v for k, v in new.items() if k not in mutable}, f'history rewritten: {old["id"]}')
            if old.get('superseded_by'):
                require(all(old.get(k) == new.get(k) for k in mutable), f'supersession rewritten: {old["id"]}')


def inspect(root, baseline=None, check_live=False):
    root = Path(root).absolute()
    require(not any(p.is_symlink() for p in (root, *root.parents)), 'symlink wiki root refused')
    catalog = json.loads(local(root, 'catalog.json').read_text())
    require(catalog.get('schema') == 1 and text(catalog.get('project')), 'invalid catalog schema/project')
    sources, claims = records(catalog.get('sources'), 'source'), records(catalog.get('claims'), 'claim')
    issues, source_lines, drift = [], {}, set()

    def issue(level, code, message, claim_ids=()):
        issues.append(dict(level=level, code=code, message=message, claims=sorted(claim_ids)))

    paths = set()
    for name, source in sources.items():
        require(all(text(source.get(k)) for k in ('path', 'origin', 'version', 'kind', 'sha256')),
                f'{name}: missing provenance')
        require(source['kind'] in ('document', 'code', 'observation'), f'{name}: invalid source kind')
        require(source['version'].strip().lower() not in ('unknown', 'latest', 'n/a'), f'{name}: unpinned version')
        require(re.fullmatch('[0-9a-f]{64}', source['sha256']), f'{name}: invalid SHA256')
        path = local(root, source['path'], 'sources')
        require(path not in paths, f'{name}: snapshot path reused')
        paths.add(path)
        require(path.stat().st_size <= 10 * 1024 * 1024, f'{name}: text source exceeds 10 MiB')
        data = path.read_bytes()
        require(sha(data) == source['sha256'], f'{name}: source snapshot hash changed')
        source_lines[name] = data.decode('utf-8').splitlines()
        if check_live and not source.get('superseded_by'):
            origin = Path(source['origin'])
            if not origin.is_absolute():
                issue('review', 'live-unchecked', f'{name}: only absolute local origins can be checked')
                drift.add(name)
            elif (not origin.is_file() or origin.stat().st_size > 10 * 1024 * 1024
                  or sha(origin.read_bytes()) != source['sha256']):
                issue('review', 'source-drift', f'{name}: live origin missing/changed; pinned snapshot preserved')
                drift.add(name)
    successors(sources, ('origin', 'kind'))

    for name, claim in claims.items():
        require(all(text(claim.get(k)) for k in ('key', 'scope', 'value', 'statement', 'kind', 'page')),
                f'{name}: missing claim fields')
        require(claim['kind'] in KINDS, f'{name}: invalid claim kind')
        local(root, claim['page'], 'pages')
        evidence = claim.get('evidence')
        require(isinstance(evidence, list) and evidence, f'{name}: evidence required')
        for cite in evidence:
            require(isinstance(cite, dict) and cite.get('source') in sources, f'{name}: missing evidence source')
            start, end = cite.get('start'), cite.get('end')
            require(type(start) is int and type(end) is int and
                    1 <= start <= end <= len(source_lines[cite['source']]), f'{name}: invalid line locator')
        related = claim.get('related', [])
        require(isinstance(related, list) and all(x in claims for x in related), f'{name}: broken related claim')
    successors(claims, ('key', 'scope', 'kind'))

    statuses = {name: 'superseded' if c.get('superseded_by') else 'pinned' for name, c in claims.items()}
    groups = defaultdict(list)
    for name, claim in claims.items():
        if claim.get('superseded_by'):
            continue
        stale = [c['source'] for c in claim['evidence']
                 if sources[c['source']].get('superseded_by') or c['source'] in drift]
        if stale:
            statuses[name] = 'stale'
            issue('review', 'stale-claim', f'{name}: review against updated/unverified source: {stale}', [name])
        groups[(claim['key'], claim['scope'])].append(name)
    for names in groups.values():
        if len({claims[n]['value'] for n in names}) > 1:
            code = 'conflicting-claims' if len({claims[n]['kind'] for n in names}) == 1 else 'contract-observation-gap'
            issue('review', code, 'different canonical values in the same key/scope; semantic review required', names)
            for name in names:
                if statuses[name] != 'stale': statuses[name] = 'disputed'

    # Check derived Markdown only. Raw source links retain their original context.
    pages = {p.relative_to(root).as_posix() for p in (root / 'pages').rglob('*.md')}
    derived = pages | {'index.md'}
    graph = defaultdict(set)
    for page in sorted(derived):
        path = local(root, page)
        for target in LINK.findall(path.read_text()):
            target = target.strip()
            if target.startswith('<') and '>' in target: target = target[1:target.index('>')]
            else: target = target.split(' ', 1)[0]
            parsed = urlsplit(target)
            if parsed.scheme in ('https', 'http', 'mailto') or not parsed.path: continue
            require(not parsed.scheme, f'{page}: unsupported link scheme')
            relative = Path(page).parent / unquote(parsed.path)
            # Normalize legitimate ../sources links, then enforce containment/symlinks.
            candidate = (root / relative).absolute()
            require(not any(p.is_symlink() for p in (candidate, *candidate.parents)), f'{page}: symlink link refused')
            candidate = Path(os.path.normpath(candidate))
            require(candidate.is_relative_to(root), f'{page}: link escapes wiki')
            resolved = local(root, candidate.relative_to(root))
            if resolved.relative_to(root).as_posix() in derived:
                graph[page].add(resolved.relative_to(root).as_posix())
    reachable, pending = set(), ['index.md']
    while pending:
        page = pending.pop()
        if page not in reachable:
            reachable.add(page)
            pending.extend(graph[page] - reachable)
    for page in sorted(pages - reachable):
        issue('review', 'orphan-page', page)

    log = local(root, 'log.jsonl').read_bytes()
    require(log.endswith(b'\n') and log.strip(), 'log must contain newline-terminated records')
    for line in log.decode('utf-8').splitlines():
        entry = json.loads(line)
        require(isinstance(entry, dict) and all(text(entry.get(k)) for k in ('at', 'action', 'summary')),
                'invalid log entry')
        datetime.fromisoformat(entry['at'].replace('Z', '+00:00'))
    if baseline:
        check_history(catalog, log, baseline)
    return catalog, statuses, issues, log


def analyze(root, baseline=None, check_live=False):
    try:
        catalog, statuses, issues, log = inspect(root, baseline, check_live)
        report = dict(project=catalog['project'], sources=len(catalog['sources']), claims=len(catalog['claims']),
                      live_checked=check_live, statuses=statuses, issues=issues,
                      limits=LIMITS)
        return report, 2 if issues else 0
    except (ValueError, OSError, KeyError, TypeError, UnicodeError, AttributeError) as error:
        return {'issues': [{'level': 'error', 'code': 'invalid-wiki', 'message': str(error)}]}, 3


def query(root, key, history=False, check_live=False):
    try:
        catalog, statuses, all_issues, _ = inspect(root, check_live=check_live)
    except (ValueError, OSError, KeyError, TypeError, UnicodeError, AttributeError) as error:
        return {'issues': [{'level': 'error', 'code': 'invalid-wiki', 'message': str(error)}]}, 3
    sources = records(catalog['sources'], 'source')
    matches = []
    for claim in catalog['claims']:
        if claim['key'] != key or (claim.get('superseded_by') and not history): continue
        cites = []
        for cite in claim['evidence']:
            source = sources[cite['source']]
            cites.append(dict(cite, path=source['path'], version=source['version'],
                              sha256=source['sha256'], origin=source['origin']))
        matches.append(dict(claim, status=statuses[claim['id']], evidence=cites))
    names = {c['id'] for c in matches}
    issues = [i for i in all_issues if not i['claims'] or names.intersection(i['claims'])]
    answer = 'not-found' if not matches else 'needs-review' if issues else 'pinned-evidence'
    return dict(key=key, matches=matches, issues=issues, answer_state=answer,
                live_checked=check_live, limits=LIMITS), 2 if issues or not matches else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for action in ('lint', 'query', 'snapshot'):
        item = sub.add_parser(action)
        item.add_argument('root', type=Path)
        item.add_argument('--check-live', action='store_true')
        if action == 'lint': item.add_argument('--baseline', type=Path)
        if action == 'query':
            item.add_argument('--key', required=True)
            item.add_argument('--history', action='store_true')
        if action == 'snapshot': item.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == 'query':
            result, code = query(args.root, args.key, args.history, args.check_live)
        elif args.action == 'snapshot':
            catalog, _, issues, log = inspect(args.root, check_live=args.check_live)
            data = dict(schema=1, catalog=catalog, log_bytes=len(log), log_sha256=sha(log))
            with args.output.open('x') as stream: json.dump(data, stream, indent=2)
            result, code = dict(action='snapshot-created', existing_issues=issues), 0
        else:
            result, code = analyze(args.root, args.baseline, args.check_live)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return code
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
