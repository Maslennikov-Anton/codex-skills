# Common Workflows

Primary official docs:

- https://docs.gitlab.com/cli/
- https://docs.gitlab.com/cli/issue/
- https://docs.gitlab.com/cli/issue/create/
- https://docs.gitlab.com/cli/issue/list/
- https://docs.gitlab.com/cli/mr/
- https://docs.gitlab.com/cli/release/create/
- https://docs.gitlab.com/cli/repo/clone/
- https://docs.gitlab.com/cli/repo/fork/
- https://docs.gitlab.com/cli/ci/list/

## Repo workflow

Clone a project:

```bash
glab repo clone gitlab-org/cli
glab repo clone https://gitlab.com/gitlab-org/cli
```

Clone a specific branch:

```bash
glab repo clone gitlab-org/cli -- --branch development
```

Fork a project:

```bash
glab repo fork namespace/repo --clone
```

## Issue workflow

List issues:

```bash
glab issue list
glab issue list --assignee=@me
glab issue list --milestone release-2.0.0 --opened
```

Create an issue:

```bash
glab issue create -t "Fix login bug" -l bug
glab issue create -t "Fix CVE-YYYY-XXXX" -l security --linked-mr 123
```

Open in browser or add a note:

```bash
glab issue view --web 123
glab issue note -m "closing because !123 was merged" 123
```

## Merge request workflow

Create an MR:

```bash
glab mr create --fill --label bugfix
```

Review and merge:

```bash
glab mr view 123
glab mr diff 123
glab mr approve 123
glab mr merge 123
```

Work locally with an MR:

```bash
glab mr checkout 243
glab mr rebase 243
```

## CI/CD workflow

List pipelines:

```bash
glab ci list
glab ci list --status=failed
glab ci list --source=merge_request_event --output json
```

Use this area when the user wants pipeline visibility from the terminal. If the needed pipeline or job action is missing from the documented high-level commands you have open, fall back to `glab api`.

## Release workflow

Create a release:

```bash
glab release create v1.0.1 --notes "bugfix release"
```

Create a release from notes file:

```bash
glab release create v1.0.1 -F changelog.md
```

Create a release with assets:

```bash
glab release create v1.0.1 ./dist/*
```

## Variable workflow

Set a project variable:

```bash
glab variable set SERVER_TOKEN "some value"
```

Set a group variable:

```bash
cat token.txt | glab variable set GROUP_TOKEN -g mygroup --scope=prod
```

## When to switch to `glab api`

Use `glab api` when:

- the high-level subcommand does not expose the exact endpoint or flag you need;
- you need GraphQL;
- you need pagination or a one-off admin request without waiting for a higher-level subcommand.
