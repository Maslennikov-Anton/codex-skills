#!/usr/bin/env python3
"""Read back one Allure 2 results directory from TestOps; never repair or upload."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import http.client
import json
import os
from pathlib import Path
import shlex
import sys
import urllib.error
import urllib.parse
import urllib.request


class AuditError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def credentials(secret_file: Path) -> tuple[str, str]:
    values = {}
    if secret_file.exists():
        for line in secret_file.read_text().splitlines():
            words = shlex.split(line, comments=True)
            if words[:1] == ["export"]:
                words = words[1:]
            if not words:
                continue
            key, separator, value = words[0].partition("=")
            if key not in {"ALLURE_TESTOPS_URL", "ALLURE_TESTOPS_TOKEN"}:
                continue
            if not separator or len(words) != 1 or "$" in value or "`" in value:
                raise AuditError("Secret file must use literal KEY=value assignments")
            values[key] = value
    values.update({k: os.environ[k] for k in ("ALLURE_TESTOPS_URL", "ALLURE_TESTOPS_TOKEN") if k in os.environ})
    url, token = values.get("ALLURE_TESTOPS_URL", ""), values.get("ALLURE_TESTOPS_TOKEN", "")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.query or parsed.fragment or not token:
        raise AuditError("Expected HTTPS ALLURE_TESTOPS_URL and nonempty ALLURE_TESTOPS_TOKEN")
    return url.rstrip("/"), token


class Client:
    def __init__(self, url: str, token: str):
        self.url = url
        self.opener = urllib.request.build_opener(NoRedirect())
        form = urllib.parse.urlencode({"grant_type": "apitoken", "scope": "openid", "token": token}).encode()
        auth = json.loads(self._read("/api/uaa/oauth/token", data=form))
        self.bearer = auth.get("access_token")
        if not isinstance(self.bearer, str) or not self.bearer:
            raise AuditError("Token exchange did not return an access token")

    def _read(self, path: str, data: bytes | None = None) -> bytes:
        headers = {"Accept": "application/json"}
        if data is None:
            headers["Authorization"] = "Bearer " + self.bearer
        request = urllib.request.Request(self.url + path, data=data, headers=headers)
        try:
            with self.opener.open(request, timeout=45) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            error.close()
            raise AuditError(f"HTTP {error.code}: {request.get_method()} {path.split('?')[0]}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as error:
            cause = error.reason if isinstance(error, urllib.error.URLError) else error
            raise AuditError(f"Request failed: {type(cause).__name__}") from None

    def get(self, path: str, **query):
        suffix = "?" + urllib.parse.urlencode(query) if query else ""
        return json.loads(self._read(path + suffix))

    def content(self, attachment_id: int) -> bytes:
        return self._read(f"/api/testresult/attachment/{attachment_id}/content")


def pages(client, path: str, **query) -> list[dict]:
    rows, seen = [], set()
    total = None
    for page in range(1000):
        data = client.get(path, **query, page=page, size=500, sort="id,ASC")
        if not isinstance(data, dict) or not isinstance(data.get("content"), list) or type(data.get("last")) is not bool:
            raise AuditError(f"Unknown pagination schema: {path}")
        count = data.get("totalElements")
        if type(count) is not int or count < 0 or (total is not None and count != total):
            raise AuditError(f"Missing or changing page total: {path}")
        total = count
        for row in data["content"]:
            identity = row.get("id") if isinstance(row, dict) else None
            if type(identity) is not int or identity in seen:
                raise AuditError(f"Missing or repeated row id: {path}")
            seen.add(identity)
            rows.append(row)
        if data["last"]:
            if len(rows) != total:
                raise AuditError(f"Incomplete pagination: {path}")
            return rows
        if not data["content"] or len(rows) >= total:
            raise AuditError(f"Pagination did not advance: {path}")
    raise AuditError(f"Pagination limit reached: {path}")


def attachments(node: dict):
    yield from node.get("attachments", [])
    for step in node.get("steps", []):
        yield from attachments(step)


def local_file(root: Path, source: str) -> Path:
    if not isinstance(source, str):
        raise AuditError("Attachment source is missing")
    path = (root / source).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise AuditError("Attachment source is absent or outside the results directory")
    return path


def identity(result: dict) -> tuple:
    # Start/stop distinguish retries; testCaseId/historyId alone merge executions.
    keys = ("fullName", "name", "start", "stop")
    if any(key not in result for key in keys):
        raise AuditError("Result lacks execution identity (fullName/name/start/stop)")
    if not all(isinstance(result[k], str) and result[k] for k in keys[:2]):
        raise AuditError("Result name/fullName must be nonempty strings")
    if any(type(result[k]) is not int for k in keys[2:]):
        raise AuditError("Result timestamps must be integer milliseconds")
    return tuple(result[k] for k in keys)


def verify(client, launch_id: int, raw: Path, *, allow_extra: bool = False) -> dict:
    files = sorted(raw.glob("*-result.json"))
    if not files:
        raise AuditError("No *-result.json files: empty input cannot prove completeness")
    local = [json.loads(path.read_text()) for path in files]
    expected = {identity(row): row for row in local}
    if len(expected) != len(local):
        raise AuditError("Ambiguous local execution identities")
    for path in sorted(raw.glob("*-container.json")):
        container = json.loads(path.read_text())
        evidence = [item for fixture in container.get("befores", []) + container.get("afters", [])
                    for item in attachments(fixture)]
        if evidence:
            # Fixture-to-result rendering differs between TestOps adapters.
            # Never silently omit such evidence from a completeness verdict.
            raise AuditError("Container fixture attachments require an instance-specific execution mapping")
    launch = client.get(f"/api/launch/{launch_id}")
    if not isinstance(launch, dict) or type(launch.get("closed")) is not bool:
        raise AuditError("Launch schema lacks closed state")
    remote = pages(client, "/api/testresult", launchId=launch_id)
    actual = {}
    for row in remote:
        key = identity(row)
        if key in actual:
            raise AuditError("Duplicate server execution identity")
        actual[key] = row
    missing, extra = set(expected) - set(actual), set(actual) - set(expected)
    if missing or (extra and not allow_extra):
        raise AuditError(f"Result count mismatch: missing={len(missing)}, extra={len(extra)}")
    checked_attachments = 0
    for key, result in expected.items():
        server = actual[key]
        if result.get("status") not in {"passed", "failed", "broken", "skipped", "unknown"}:
            raise AuditError("Unknown local result status")
        if server.get("status") != result["status"]:
            raise AuditError(f"Status mismatch: result {server['id']}")
        wanted = Counter()
        for item in attachments(result):
            payload = local_file(raw, item.get("source")).read_bytes()
            wanted[(item["name"], item["type"], len(payload), hashlib.sha256(payload).hexdigest())] += 1
        received = Counter()
        for item in pages(client, "/api/testresult/attachment", testResultId=server["id"]):
            if type(item.get("missed")) is not bool or item["missed"] or type(item.get("contentLength")) is not int:
                raise AuditError(f"Missing attachment content/metadata: result {server['id']}")
            payload = client.content(item["id"])
            if len(payload) != item["contentLength"]:
                raise AuditError(f"Attachment length differs: attachment {item['id']}")
            received[(item["name"], item["contentType"], len(payload), hashlib.sha256(payload).hexdigest())] += 1
        if wanted != received:
            raise AuditError(f"Attachment metadata/content mismatch: result {server['id']}")
        checked_attachments += sum(wanted.values())
    final_launch = client.get(f"/api/launch/{launch_id}")
    if not isinstance(final_launch, dict) or final_launch.get("closed") != launch["closed"]:
        raise AuditError("Launch state changed during audit; repeat after ingestion settles")
    return {"launch_id": launch_id, "results_verified": len(local), "attachments_verified": checked_attachments,
            "extra_results": len(extra), "closed": launch["closed"],
            "product_statuses": dict(Counter(row["status"] for row in local)),
            "state": "verified_closed" if launch["closed"] else "verified_snapshot_open_launch"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--launch-id", required=True, type=int)
    parser.add_argument("--secret-file", type=Path, default=Path(os.environ.get("ALLURE_TESTOPS_SECRET_FILE", "/home/ant/.allure-testops.env")))
    parser.add_argument("--allow-extra-results", action="store_true", help="Audit only this batch in a shared launch; still reject duplicate identities")
    args = parser.parse_args()
    try:
        if args.launch_id <= 0:
            raise AuditError("launch-id must be positive")
        url, token = credentials(args.secret_file)
        report = verify(Client(url, token), args.launch_id, args.results, allow_extra=args.allow_extra_results)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError, RecursionError) as error:
        # Never echo response bodies, credentials, or auth parse errors.
        message = str(error) if isinstance(error, AuditError) else type(error).__name__
        print(json.dumps({"state": "unverified", "error": message}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
