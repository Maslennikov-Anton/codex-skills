---
name: project-context
description: "Use in Ant's local repos under /home/ant/IdeaProjects: repo orientation, workspace map, commands, build/test/run workflows, release steps, and conventions."
metadata:
  short-description: Local project map and command conventions
---

# Project Context

Before changing or diagnosing a local project, identify the repository root and read the relevant entry in [references/workspace-map.md](references/workspace-map.md).

## Workflow

1. Confirm the current repository with `git rev-parse --show-toplevel` when inside a repo.
2. Match the repo path/name against `references/workspace-map.md`.
3. Prefer documented project commands over generic guesses.
4. If the map is missing or stale, inspect local files such as `README*`, `package.json`, `pyproject.toml`, `pom.xml`, `build.gradle*`, `Makefile`, `.github/workflows`, `docker-compose*`, and project scripts.
5. When you learn a stable command or convention that will be reused, suggest adding it to the workspace map.

## Guardrails

- Do not invent missing commands; verify them from the repo or ask for the intended workflow.
- Treat secrets and environment-specific values as references to locations or variable names, not as values to record.
- Keep project-specific details in the reference file so this skill stays small.
