# Megapack Repository Workflow

Use this reference only when repository behavior matters: explaining how artifacts are made, diagnosing artifact defects from source, or reviewing pipeline logic. For artifact-only validation, prefer `artifact-validation.md`.

## Repository Layout

```text
/home/ant/IdeaProjects/megapack
├── .gitlab-ci.yml
├── README.md
├── TODO.md
├── installer/
│   └── install.sh
└── scripts/
    ├── build_megapack.sh
    ├── download_deps.sh
    └── fetch_latest.sh
```

Generated/local paths:

- `packages/`: downloaded `.deb` dependencies, ignored by git.
- `develop_manifest.ini`: generated manifest, ignored by git.
- `*.run`: built artifacts, ignored by git.

## Script Responsibilities

`scripts/fetch_latest.sh`:

- queries Nexus Assets API: `/service/rest/v1/assets`;
- paginates through `continuationToken`;
- matches artifact paths against a glob-like pattern;
- chooses latest by `lastModified`;
- downloads the matching artifact.

`scripts/download_deps.sh`:

- downloads VCont `.deb` packages by direct Nexus URL;
- downloads configurator, agent, and OPC UA packages via `fetch_latest.sh`;
- writes `develop_manifest.ini` with downloaded versions and build metadata;
- supports `-a/--arch`, `-V/--variant`, `-v/--version`, `-b/--branch`.

`scripts/build_megapack.sh`:

- reads version from `-v` or `develop_manifest.ini`;
- stages packages under `packages/<arch>`;
- copies `installer/install.sh`;
- generates `metadata.ini` from `dpkg-deb -f`;
- collects `.deb` dependencies into `[dependencies]`;
- runs `makeself --sha256`.

`installer/install.sh`:

- is embedded into the `.run` artifact;
- reads `metadata.ini`;
- checks root, arch, dependencies, and variant conflicts;
- installs packages through `dpkg -i`;
- supports `help`, `version`, `install [opcua]`, `uninstall`, and `purge`.

## CI Shape

Known GitLab stages:

- `build`: six jobs download dependencies and run `build_megapack.sh`.
- `upload`: uploads `vcont-*.run` to Nexus.

Known build variants:

- `build-x86_64-developer`
- `build-x86_64-lic`
- `build-x86_64-trial-light`
- `build-x86_64-trial-full`
- `build-x86_64-legacy-lic`
- `build-x86_64-legacy-developer`

Legacy jobs were observed as `allow_failure: true` in the repo snapshot reviewed on 2026-06-02.

## Useful Local Checks

These checks do not prove artifact installability, but they are useful while reviewing source:

```bash
bash -n scripts/build_megapack.sh scripts/download_deps.sh scripts/fetch_latest.sh installer/install.sh
shellcheck scripts/build_megapack.sh scripts/download_deps.sh scripts/fetch_latest.sh installer/install.sh
./scripts/build_megapack.sh --help
./scripts/download_deps.sh --help
```

Full source-side build requires real `.deb` files under `packages/<arch>` and `makeself`.

## Important Variable Names

Repository docs mention both forms:

- CI variables in `.gitlab-ci.yml`: `REPO_SNAPSHOT`, `REPO_RELEASE`;
- script environment variables: `SNAPSHOT_REPO`, `RELEASE_REPO`.

When diagnosing CI, verify the actual template exports and environment. Do not assume these names map automatically.
