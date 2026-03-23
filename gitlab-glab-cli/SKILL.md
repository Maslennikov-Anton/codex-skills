---
name: gitlab-glab-cli
description: >
  Work with GitLab from the terminal using the official glab CLI. Use when a
  user needs help authenticating to GitLab, managing repositories, issues,
  merge requests, pipelines, releases, variables, or making authenticated REST
  and GraphQL requests with `glab api`. Covers GitLab.com, GitLab Dedicated,
  and self-managed GitLab instances.
---

# GitLab CLI (`glab`)

Use this skill when the task is about working with GitLab through the official `glab` CLI documented at `https://docs.gitlab.com/cli/`.

## What this skill covers

- Authentication and multi-host setup.
- Repo operations: clone, fork, remote-aware work.
- Issues and merge requests.
- CI/CD pipelines and jobs.
- Releases.
- Variables.
- Authenticated GitLab REST and GraphQL requests via `glab api`.
- Troubleshooting around tokens, host detection, CI auto-login, and self-managed instances.

## Workflow

1. Identify whether the user wants:
   - ordinary repo workflow;
   - issue/MR workflow;
   - CI/CD workflow;
   - release/admin workflow;
   - raw API access through `glab api`.
2. Check whether the target is:
   - `gitlab.com`;
   - GitLab Dedicated;
   - self-managed GitLab.
3. If auth might be missing, start with [references/auth-and-setup.md](references/auth-and-setup.md).
4. If a higher-level `glab` command exists, prefer it over raw API calls.
5. If `glab` does not expose the exact operation cleanly, fall back to `glab api`.
6. If the command is repo-context-sensitive, confirm whether execution is:
   - inside the target Git repository;
   - with `-R/--repo`;
   - with `--hostname` for cross-host work.
7. For automations and scripts, prefer non-interactive flags and env vars over prompts.

## Which reference to open

- Setup, token precedence, host selection, CI auto-login:
  [references/auth-and-setup.md](references/auth-and-setup.md)
- Common command workflows:
  [references/common-workflows.md](references/common-workflows.md)
- Command matrix by area:
  [references/command-matrix.md](references/command-matrix.md)
- `glab api` for REST and GraphQL:
  [references/api-mode.md](references/api-mode.md)
- Troubleshooting:
  [references/troubleshooting.md](references/troubleshooting.md)

## Practical rules

- Prefer `glab auth login` for initial setup, but prefer env vars or `--stdin` in automation.
- Prefer `-R/--repo` when acting outside the target repository.
- Prefer `glab mr`, `glab issue`, `glab ci`, `glab release`, and `glab variable` before `glab api`.
- Use `glab api` when the CLI surface is missing the exact operation or when GraphQL is a better fit.
- Do not expose personal access tokens in output.
- State clearly when behavior depends on the GitLab instance type or role permissions.
