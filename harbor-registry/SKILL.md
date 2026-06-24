---
name: harbor-registry
description: "Inspect corporate Harbor with a CLI secret or robot secret: docker login, list projects/repos/tags, find internal images, and choose Harbor images for VCont or CI work."
---

# Harbor Registry

Use this skill to inspect corporate Harbor before choosing Docker base images,
builder images, QA/runtime images, or CI image references.

For the current corporate image map and preferred internal replacements, read
`references/corporate-image-map.md` before suggesting public registry or mirror
images.

## Security Rules

- Never store a Harbor password, CLI secret, robot secret, Docker config auth
  blob, or Basic Auth header in this skill, a repo, memory, logs, or chat.
- Prefer a read-only robot account for automation. If using a personal Harbor
  account, use the Harbor profile `CLI secret` as the password, not the web UI
  password.
- Pass secrets through stdin, a credential helper, an env var, or a local
  untracked file with `chmod 600`. Do not pass secrets via `docker login -p`
  or command-line args.
- Treat push/delete/retention/replication actions as high-impact and ask for
  explicit user confirmation before running them.

## Local Credentials

Preferred one-time Docker login:

```bash
printf '%s' "$HARBOR_CLI_SECRET" | docker login harbor.isource.dev -u "$HARBOR_USER" --password-stdin
```

For API inventory, use environment variables:

```bash
export HARBOR_URL="https://harbor.isource.dev"
export HARBOR_USER="<username or robot$account>"
export HARBOR_CLI_SECRET="<CLI secret or robot secret>"
```

Or a local file outside the repo:
`/home/ant/.harbor/harbor.env`:

```bash
export HARBOR_URL="https://harbor.isource.dev"
export HARBOR_USER="<username or robot$account>"
export HARBOR_CLI_SECRET="<CLI secret or robot secret>"
```

Before using an env file, verify it is not inside a repository and has private
permissions:

```bash
chmod 600 /home/ant/.harbor/harbor.env
```

## Workflow

1. Inspect local task scope first: Dockerfiles, compose files, CI image refs,
   README, or the requested Harbor project/repository.
2. Check whether Docker/API credentials are available without printing secrets.
3. If API inventory is needed, use `scripts/harbor_inventory.py` with env vars
   or `--env-file`. The script masks credentials and does not print secrets.
4. Search narrowly first: project names from the repo or CI such as `docker`,
   `builders`, `vcont-qa`, `vcont-runtime`, `vcont-runtime-runner`.
5. Prefer internal Harbor images over Docker Hub/public registries when they
   exist and match the required OS, toolchain, architecture, and freshness.
6. For VCont work, verify the exact image/tag currently used by local
   Dockerfiles, `.gitlab-ci.yml`, compose files, or README before changing it.
7. Before declaring an image usable, verify one of:
   - `docker pull <image>` succeeds;
   - `docker build --check` or a narrow build reaches metadata/layer access;
   - the Harbor API shows a recent artifact with tags and digest.

## Commands

List projects:

```bash
python3 /home/ant/codex-skills/harbor-registry/scripts/harbor_inventory.py \
  --env-file /home/ant/.harbor/harbor.env projects
```

List repositories in a project:

```bash
python3 /home/ant/codex-skills/harbor-registry/scripts/harbor_inventory.py \
  --env-file /home/ant/.harbor/harbor.env repos --project docker
```

List tags for a repository:

```bash
python3 /home/ant/codex-skills/harbor-registry/scripts/harbor_inventory.py \
  --env-file /home/ant/.harbor/harbor.env tags \
  --project docker --repository library/python
```

Show latest tags with pull-ready references:

```bash
python3 /home/ant/codex-skills/harbor-registry/scripts/harbor_inventory.py \
  --env-file /home/ant/.harbor/harbor.env latest \
  --project docker --repository library/python
```

Search projects, repositories, and tags:

```bash
python3 /home/ant/codex-skills/harbor-registry/scripts/harbor_inventory.py \
  --env-file /home/ant/.harbor/harbor.env search vcont
```

For nested repository names, Harbor API paths require slash escaping. The helper
normalizes names returned as `project/repository` and double-encodes nested
slashes before calling artifact/tag endpoints.

## Output Guidance

When reporting results, include image names, tags, digest prefixes, push/update
time, and the verification method. Do not include usernames unless needed, and
never include secrets or auth headers.
