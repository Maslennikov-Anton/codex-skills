# Auth And Setup

Primary official docs:

- https://docs.gitlab.com/cli/
- https://docs.gitlab.com/cli/auth/login/

## Supported targets

`glab` supports:

- GitLab.com
- GitLab Dedicated
- self-managed GitLab

It can keep credentials for multiple authenticated hosts and detect the active host from Git remotes in the current repository.

## First setup

Interactive:

```bash
glab auth login
```

Non-interactive with token:

```bash
glab auth login --hostname gitlab.example.org --token "$GITLAB_TOKEN"
```

Non-interactive from stdin:

```bash
glab auth login --hostname gitlab.com --stdin < token.txt
```

Self-managed with custom API endpoint and SSH protocol:

```bash
glab auth login \
  --hostname gitlab.example.org \
  --api-host gitlab.example.org:3443 \
  --api-protocol https \
  --git-protocol ssh \
  --stdin < token.txt
```

## Token behavior

The docs state that these environment variables take precedence over stored credentials:

- `GITLAB_TOKEN`
- `GITLAB_ACCESS_TOKEN`
- `OAUTH_TOKEN`

When CI auto-login is enabled, those variables also override `CI_JOB_TOKEN`.

## Config location

By default credentials and config are stored in:

```text
~/.config/glab-cli/config.yml
```

The docs also note:

- `--use-keyring` stores the token in the OS keyring instead of the config file.
- `GLAB_CONFIG_DIR` overrides the config directory.

For self-managed GitLab, treat `glab auth status` as a helpful signal but not the final authority. If `auth status` reports `Invalid token provided`, verify with direct API calls before concluding auth is broken:

```bash
glab api user --hostname gitlab.example.org
glab api version --hostname gitlab.example.org
glab api personal_access_tokens/self --hostname gitlab.example.org
```

If those return `200` or valid JSON, the token and API access are working even if `auth status` prints a warning.

If login behaves strangely after `glab auth login --stdin`, inspect `~/.config/glab-cli/config.yml` for malformed token serialization. One observed failure mode is a token written with a YAML null tag, for example:

```yaml
token: !!null glpat-...
```

That should be treated as a broken config entry and corrected by re-running login or fixing the stored value.

## Environment variables worth checking

- `GITLAB_HOST` or `GL_HOST`: target GitLab host, especially for self-managed instances.
- `GITLAB_TOKEN`: token for API requests.
- `GLAB_ENABLE_CI_AUTOLOGIN=true`: enables CI auto-login.
- `NO_PROMPT=true`: disables prompts.
- `DEBUG=true`: enables more logging.
- `GLAB_DEBUG_HTTP=true`: prints HTTP request/response info.

## CI login

Official example:

```bash
glab auth login --hostname "$CI_SERVER_HOST" --job-token "$CI_JOB_TOKEN"
```

Use this only for commands that support job-token auth.

## Practical setup sequence

1. Authenticate with `glab auth login`.
2. Verify the repo host or pass `--hostname`.
3. Verify auth with `glab api user` and, for PAT-backed auth, `glab api personal_access_tokens/self`.
4. For scripted use, set `GITLAB_TOKEN` and `NO_PROMPT=true`.
5. For CI, prefer job-token-aware commands or `glab api` where compatible.
