---
name: project-context
description: "Ориентация в IdeaProjects repo: trusted commands, conventions, dirty worktree, test/push; вести/читать wiki проекта по версиям источников. Не для личной памяти и простых правок."
---

# Project Context

Use this skill before unfamiliar, repo-wide, push/test, diagnostic, or
context-dependent work under `/home/ant/IdeaProjects`. Its job is to replace
generic repo guesses with verified local context: repo purpose, trusted
commands, known generated files, dirty-worktree risks, and related domain
skills.

The compact source of truth is [references/workspace-map.md](references/workspace-map.md).
For refreshing or extending the map, use
[references/maintenance.md](references/maintenance.md).

For a user-requested project knowledge base, source ingestion, or questions against an existing wiki, use
[references/project-wiki.md](references/project-wiki.md). Keep claims tied to source versions; report stale/conflicting
claims explicitly. Ordinary repo work does not authorize automatic wiki or personal-memory writes.

## Workflow

1. Confirm the repo root with `git rev-parse --show-toplevel` when inside a repo.
2. If the task may depend on prior local decisions, recurring repo history, or user preferences, do a quick memory lookup and verify drift-prone facts against the repo.
3. Check `git status --short --ignored` before edits when the task can touch files, commits, pushes, generated outputs, Docker artifacts, reports, or test results.
4. Match the repo path/name against `references/workspace-map.md` when the repo is unfamiliar, the command is not obvious, or generated artifacts/push/test behavior matters.
5. If the task is to commit/push/sync according to `.gitignore`, use `gitignore-scoped-push` after this orientation.
6. Prefer the documented commands and notes over generic build/test assumptions.
7. If the map is missing, stale, or contradicted by executable files, inspect local evidence first: `README*`, `pyproject.toml`, `package.json`, `pom.xml`, `build.gradle*`, `Makefile`, `.gitlab-ci.yml`, `.github/workflows`, `docker-compose*`, `compose.yaml`, Dockerfiles, `requirements*.txt`, `setup.py`, `pytest.ini`, Terraform files, `.env.example`, `scripts/`, and test config.
8. Combine with the domain skill named in the map when the task needs protocol, framework, CI, security, database, or testing depth.
9. When you learn a reusable stable fact, update the map only if the user requested skill/context maintenance or explicitly asked to remember/sync it.
10. Before creating disposable analysis/test workspaces use `artifact-lifecycle`; finish by retaining minimal evidence and cleaning owned intermediates. For tests/config/reporting changes apply [test integrity](../autotest-engineer/references/test-integrity.md) before editing, including a working-tree baseline.

## Guardrails

- Do not invent missing commands; verify them from the repo or ask for the intended workflow.
- Treat secrets and environment-specific values as references to locations or variable names, not as values to record.
- Do not record transient spikes, one-off pipeline numbers, local temp files, or unapproved experiments as permanent project context.
- Trust executable sources such as CI, Dockerfiles, scripts, and test config over stale README text when they conflict.
- Never revert or overwrite dirty worktree changes discovered during orientation unless the user explicitly asks.
- Keep source repos read-only during cross-repo map refreshes unless the task explicitly includes changing those repos.
- Before high-impact operations (Terraform state/apply/destroy, privileged installers, destructive cleanup, cloud/IAM/secrets, releases, external mutations), check the action against existing user authorization. Ask only when the action or its impact exceeds that scope; a skill never grants additional permissions.
- Treat workspace-map commands as starting points, not proof of success; final readiness claims still go through `verification-before-completion`.
- Route memory storage/recall details to `para-memory-files` and GitLab auth/MR/pipeline/API operations to `gitlab-operations`.
- Keep project-specific details in reference files so this skill stays small.
- Before claiming a skill update is complete, run the checks from `verification-before-completion` for changed skills.
