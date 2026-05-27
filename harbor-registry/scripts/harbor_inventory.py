#!/usr/bin/env python3
"""Small Harbor v2 inventory helper.

Reads credentials from environment variables or a local env file:
HARBOR_URL, HARBOR_USER, HARBOR_CLI_SECRET.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_URL = "https://harbor.isource.dev"


def load_env_file(path: str | None) -> None:
    if not path:
        return
    env_path = Path(path).expanduser()
    if not env_path.exists():
        raise SystemExit(f"env file not found: {env_path}")
    mode = env_path.stat().st_mode & 0o777
    if mode & 0o077:
        print(
            f"warning: {env_path} is readable by group/others; use chmod 600",
            file=sys.stderr,
        )
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class HarborClient:
    def __init__(self, url: str, user: str, secret: str) -> None:
        self.base_url = url.rstrip("/")
        self.user = user
        token = base64.b64encode(f"{user}:{secret}".encode("utf-8")).decode("ascii")
        self.auth_header = f"Basic {token}"

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = urllib.parse.urlencode(params or {}, doseq=True)
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{query}"
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": self.auth_header,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"Harbor API HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise SystemExit(f"Harbor API request failed: {exc.reason}") from exc
        if not body:
            return None
        return json.loads(body)

    def paged(self, path: str, params: dict[str, Any] | None = None) -> list[Any]:
        items: list[Any] = []
        page = 1
        base_params = dict(params or {})
        while True:
            page_params = dict(base_params)
            page_params.update({"page": page, "page_size": 100})
            data = self.get(path, page_params)
            if not isinstance(data, list):
                raise SystemExit(f"expected list response for {path}")
            items.extend(data)
            if len(data) < 100:
                return items
            page += 1

    def projects(self) -> list[dict[str, Any]]:
        return self.paged("/api/v2.0/projects")

    def repositories(self, project: str) -> list[dict[str, Any]]:
        project_q = urllib.parse.quote(project, safe="")
        return self.paged(f"/api/v2.0/projects/{project_q}/repositories")

    def repository_path(self, project: str, repository: str) -> str:
        if repository.startswith(f"{project}/"):
            repository = repository[len(project) + 1 :]
        encoded_once = urllib.parse.quote(repository, safe="")
        return urllib.parse.quote(encoded_once, safe="")

    def artifacts(self, project: str, repository: str) -> list[dict[str, Any]]:
        project_q = urllib.parse.quote(project, safe="")
        repo_q = self.repository_path(project, repository)
        return self.paged(
            f"/api/v2.0/projects/{project_q}/repositories/{repo_q}/artifacts",
            {"with_tag": "true"},
        )


def require_client(args: argparse.Namespace) -> HarborClient:
    load_env_file(args.env_file)
    url = os.environ.get("HARBOR_URL", DEFAULT_URL)
    user = os.environ.get("HARBOR_USER")
    secret = os.environ.get("HARBOR_CLI_SECRET") or os.environ.get("HARBOR_SECRET")
    if not user or not secret:
        raise SystemExit(
            "missing credentials: set HARBOR_USER and HARBOR_CLI_SECRET "
            "or pass --env-file"
        )
    return HarborClient(url, user, secret)


def tag_names(artifact: dict[str, Any]) -> list[str]:
    tags = artifact.get("tags") or []
    return [tag.get("name", "") for tag in tags if tag.get("name")]


def repo_without_project(project: str, repository: str) -> str:
    if repository.startswith(f"{project}/"):
        return repository[len(project) + 1 :]
    return repository


def pull_refs(base_url: str, project: str, repository: str, tag: str) -> list[str]:
    registry = base_url.removeprefix("https://").removeprefix("http://").rstrip("/")
    repo = repo_without_project(project, repository)
    refs = [f"{registry}/{project}/{repo}:{tag}"]
    if project == "docker" and repo.startswith("library/"):
        refs.insert(0, f"{registry}/docker/{repo.split('/', 1)[1]}:{tag}")
    return refs


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def cmd_projects(client: HarborClient, args: argparse.Namespace) -> None:
    rows = [
        {
            "name": item.get("name"),
            "repo_count": item.get("repo_count"),
            "update_time": item.get("update_time"),
        }
        for item in client.projects()
    ]
    print_json(rows)


def cmd_repos(client: HarborClient, args: argparse.Namespace) -> None:
    rows = [
        {
            "name": item.get("name"),
            "artifact_count": item.get("artifact_count"),
            "pull_count": item.get("pull_count"),
            "update_time": item.get("update_time"),
        }
        for item in client.repositories(args.project)
    ]
    print_json(rows)


def cmd_tags(client: HarborClient, args: argparse.Namespace) -> None:
    rows = []
    for artifact in client.artifacts(args.project, args.repository):
        tags = tag_names(artifact)
        if not tags:
            continue
        primary_tag = tags[0]
        rows.append(
            {
                "digest": (artifact.get("digest") or "")[:20],
                "tags": tags,
                "pull_refs": pull_refs(
                    client.base_url,
                    args.project,
                    args.repository,
                    primary_tag,
                ),
                "push_time": artifact.get("push_time"),
                "size": artifact.get("size"),
            }
        )
    print_json(rows)


def cmd_search(client: HarborClient, args: argparse.Namespace) -> None:
    needle = args.query.lower()
    results: list[dict[str, Any]] = []
    for project in client.projects():
        project_name = project.get("name") or ""
        if needle in project_name.lower():
            results.append({"type": "project", "name": project_name})
        try:
            repositories = client.repositories(project_name)
        except SystemExit:
            continue
        for repo in repositories:
            repo_name = repo.get("name") or ""
            if needle in repo_name.lower():
                results.append(
                    {
                        "type": "repository",
                        "name": repo_name,
                        "artifact_count": repo.get("artifact_count"),
                        "update_time": repo.get("update_time"),
                    }
                )
            if args.with_tags:
                try:
                    artifacts = client.artifacts(project_name, repo_name)
                except SystemExit:
                    continue
                matched_tags = sorted(
                    {
                        tag
                        for artifact in artifacts
                        for tag in tag_names(artifact)
                        if needle in tag.lower()
                    }
                )
                if matched_tags:
                    results.append(
                        {
                            "type": "tags",
                            "repository": repo_name,
                            "tags": matched_tags[: args.limit_tags],
                        }
                    )
    print_json(results)


def cmd_latest(client: HarborClient, args: argparse.Namespace) -> None:
    rows = []
    for artifact in client.artifacts(args.project, args.repository):
        tags = tag_names(artifact)
        if not tags:
            continue
        for tag in tags:
            rows.append(
                {
                    "tag": tag,
                    "digest": (artifact.get("digest") or "")[:20],
                    "push_time": artifact.get("push_time"),
                    "size": artifact.get("size"),
                    "pull_refs": pull_refs(
                        client.base_url,
                        args.project,
                        args.repository,
                        tag,
                    ),
                }
            )
    rows.sort(key=lambda item: item.get("push_time") or "", reverse=True)
    print_json(rows[: args.limit])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect Harbor projects, repos, and tags")
    parser.add_argument("--env-file", help="local env file with Harbor credentials")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("projects")

    repos = subparsers.add_parser("repos")
    repos.add_argument("--project", required=True)

    tags = subparsers.add_parser("tags")
    tags.add_argument("--project", required=True)
    tags.add_argument("--repository", required=True)

    latest = subparsers.add_parser("latest")
    latest.add_argument("--project", required=True)
    latest.add_argument("--repository", required=True)
    latest.add_argument("--limit", type=int, default=10)

    search = subparsers.add_parser("search")
    search.add_argument("query")
    search.add_argument("--with-tags", action="store_true")
    search.add_argument("--limit-tags", type=int, default=20)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    client = require_client(args)
    if args.command == "projects":
        cmd_projects(client, args)
    elif args.command == "repos":
        cmd_repos(client, args)
    elif args.command == "tags":
        cmd_tags(client, args)
    elif args.command == "search":
        cmd_search(client, args)
    elif args.command == "latest":
        cmd_latest(client, args)
    else:
        parser.error(f"unknown command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
