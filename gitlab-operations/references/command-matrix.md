# Command Matrix

Primary official docs:

- https://docs.gitlab.com/cli/
- https://docs.gitlab.com/cli/auth/login/
- https://docs.gitlab.com/cli/issue/
- https://docs.gitlab.com/cli/issue/create/
- https://docs.gitlab.com/cli/issue/list/
- https://docs.gitlab.com/cli/mr/
- https://docs.gitlab.com/cli/repo/clone/
- https://docs.gitlab.com/cli/repo/fork/
- https://docs.gitlab.com/cli/ci/list/
- https://docs.gitlab.com/cli/release/create/
- https://docs.gitlab.com/cli/api/
- https://docs.gitlab.com/cli/variable/set/

## Core commands

| Area | Command | Purpose | Example |
|---|---|---|---|
| Auth | `glab auth login` | Authenticate to a GitLab host | `glab auth login --stdin < token.txt` |
| API | `glab api` | Authenticated REST or GraphQL call | `glab api projects/:fullpath/releases` |
| Repo | `glab repo clone` | Clone a project | `glab repo clone gitlab-org/cli` |
| Repo | `glab repo fork` | Fork a project | `glab repo fork namespace/repo --clone` |
| Issue | `glab issue list` | List issues | `glab issue list --assignee=@me` |
| Issue | `glab issue create` | Create issue | `glab issue create -t "Fix login bug" -l bug` |
| Issue | `glab issue note` | Comment on issue | `glab issue note -m "closing because !123 was merged" 123` |
| Issue | `glab issue view` | Inspect issue or open in browser | `glab issue view --web 123` |
| MR | `glab mr create` | Create merge request | `glab mr create --fill --label bugfix` |
| MR | `glab mr diff` | Show MR diff | `glab mr diff 123` |
| MR | `glab mr checkout` | Checkout MR branch | `glab mr checkout 243` |
| MR | `glab mr approve` | Approve MR | `glab mr approve 123` |
| MR | `glab mr merge` | Merge MR | `glab mr merge 123` |
| CI | `glab ci list` | List pipelines | `glab ci list --status=failed --output json` |
| Release | `glab release create` | Create or update release | `glab release create v1.0.1 --notes "bugfix release"` |
| Variable | `glab variable set` | Create project or group variable | `glab variable set SERVER_TOKEN "secret"` |

## Repo context controls

| Need | Preferred control |
|---|---|
| Act on another repository | `-R/--repo` |
| Act on another GitLab host | `--hostname` or `GITLAB_HOST` |
| Avoid prompts in scripts | `NO_PROMPT=true` |
| Use stored repo context | run inside the target Git repository |

## Useful top-level command families from the official docs index

These are worth considering before falling back to raw API calls:

- `glab issue`
- `glab mr`
- `glab ci`
- `glab job`
- `glab release`
- `glab repo`
- `glab variable`
- `glab label`
- `glab milestone`
- `glab schedule`
- `glab snippet`
- `glab user`
- `glab work-items`
- `glab token`
- `glab deploy-key`
- `glab ssh-key`
- `glab gpg-key`
- `glab auth`
- `glab api`

If the user asks about one of these families and the exact subcommand is not yet in this skill, open the corresponding page under `https://docs.gitlab.com/cli/` and extend from there.
