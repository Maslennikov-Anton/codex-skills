# Troubleshooting

Primary official docs:

- https://docs.gitlab.com/cli/
- https://docs.gitlab.com/cli/auth/login/
- https://docs.gitlab.com/cli/api/

## Wrong host

Symptoms:

- command hits `gitlab.com` instead of self-managed GitLab;
- repo-scoped command fails outside a repository;
- token works in browser/API but `glab` targets a different host.

Checks:

- current Git remotes;
- `GITLAB_HOST` or `GL_HOST`;
- explicit `--hostname`;
- whether the current directory is the intended repo.

## Token confusion

The docs say environment tokens override stored credentials:

- `GITLAB_TOKEN`
- `GITLAB_ACCESS_TOKEN`
- `OAUTH_TOKEN`

If behavior is surprising, check whether one of these is set in the shell or CI environment.

## CI auto-login surprise

If `GLAB_ENABLE_CI_AUTOLOGIN=true`, `glab` may use CI context automatically.

If behavior differs between local and CI runs:

- inspect `CI_JOB_TOKEN`;
- inspect host variables;
- verify the specific command supports job-token auth.

## Too interactive for automation

Use:

- `NO_PROMPT=true`
- `--stdin`
- explicit `--hostname`
- explicit `-R/--repo`

Avoid editor- and browser-dependent flows in non-interactive jobs unless the user explicitly wants them.

## Need more visibility

Use:

```bash
DEBUG=true glab <command>
GLAB_DEBUG_HTTP=true glab api <endpoint>
```

Use `glab api` when you need to see more direct API behavior than a higher-level subcommand exposes.
