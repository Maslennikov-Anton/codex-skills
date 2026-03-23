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

Also note that `glab auth status` can report `Invalid token provided` on some self-managed GitLab setups even when direct API calls succeed. Before deciding the token is bad, check:

```bash
glab api user --hostname gitlab.example.org
glab api version --hostname gitlab.example.org
glab api personal_access_tokens/self --hostname gitlab.example.org
```

If those succeed, treat the warning as a status-check inconsistency rather than a real auth failure.

If auth was set up with `glab auth login --stdin` and behavior looks inconsistent, inspect `~/.config/glab-cli/config.yml`. A malformed token line such as `token: !!null glpat-...` indicates broken YAML serialization and can cause misleading diagnostics.

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

Do not assume every `glab` command supports `--hostname`. Some commands rely on repository context or `-R/--repo` instead. If a command rejects `--hostname`, retry from the target repository or pass `-R GROUP/NAMESPACE/PROJECT`.

## Need more visibility

Use:

```bash
DEBUG=true glab <command>
GLAB_DEBUG_HTTP=true glab api <endpoint>
```

Use `glab api` when you need to see more direct API behavior than a higher-level subcommand exposes.
