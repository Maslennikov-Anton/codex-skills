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
├── scripts/
│   ├── build_megapack.sh
│   ├── download_deps.sh
│   └── fetch_latest.sh
├── manifest.ini
├── develop_manifest.ini
└── packages/
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
- downloads configurator, agent, eCAL, and OPC UA packages using branch-specific rules;
- writes `develop_manifest.ini` with downloaded versions and build metadata;
- supports `-a/--arch`, `-V/--variant`, `-v/--version`, `-b/--branch`.

Branch/component strategy from the developer README:

| Component | develop snapshot | master/release |
| --- | --- | --- |
| `vcont` | latest from Nexus Assets API | fixed version from `manifest.ini` or `VERSION_VCONT` |
| `configurator` | latest from Nexus Assets API | fixed version from `manifest.ini` or `VERSION_CONFIGURATOR` |
| `agent` | latest from Nexus Assets API | fixed version from `manifest.ini` key `agent`; skip if absent |
| `ecal` | latest from `generic-vcont-release` | latest from `generic-vcont-release` |
| `opcua` | latest from `generic-vcont-release` | latest from `generic-vcont-release` |

`manifest.ini` OPC UA version keys are informational for the README-described flow; verify scripts before assuming they control downloads.

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
- supports `help`, `version`, `install [opcua] [agent]`, `uninstall`, and `purge`.

## CI Shape

Known GitLab stages:

- `build`: parallel jobs download dependencies and run `build_megapack.sh`.
- `upload`: uploads `vcont-*.run` to Nexus.

Current matrix from the developer README:

- architectures: `x86_64`, `x86_64-legacy`, `aarch64`, `aarch64-legacy`;
- variants: `developer`, `lic`, `trial-light`, `trial-full`.

Manual `release-build` requires:

| Variable | Values |
| --- | --- |
| `BUILD_ARCH` | `x86_64`, `x86_64-legacy`, `aarch64`, `aarch64-legacy` |
| `BUILD_VARIANT` | `developer`, `lic`, `trial-light`, `trial-full` |

Optional release overrides: `VERSION_VCONT`, `VERSION_CONFIGURATOR`. If unset, release versions come from `manifest.ini`. Release upload runs automatically after `release-build` according to the README.

For ordinary CI, only `build-x86_64-developer` and `upload-snapshot-x86_64-developer` were described as blocking jobs; other jobs may be manual or `allow_failure: true` depending on branch/tag. Re-check `.gitlab-ci.yml` before reporting current pipeline gates.

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
