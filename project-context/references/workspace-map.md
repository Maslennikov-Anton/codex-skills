# Workspace Map

This file is a compact map of Ant's local repositories and recurring commands. Keep entries factual and short. Prefer commands documented here, but re-check the repo when a command can affect infrastructure, VMs, Docker volumes, cloud resources, or external systems.

## Repositories

### `/home/ant/IdeaProjects/vcont`

- Purpose: VCont runtime/core project based on Eclipse 4diac FORTE.
- Stack: C++/CMake, GitLab CI, runtime scripts.
- Known workflows:
  - Standard POSIX build: `./setup_posix.sh`, then `cd bin/posix`, then `make`.
  - Reset bad CMake state from build dir: `rm -Rf CMakeCache.txt CMakeFiles/`.
  - Local RPM build: `tito build --test --rpm`.
- Verification commands:
  - Use the narrowest relevant CMake/build command from the active build directory.
- Notes: Use the `vcont` skill for VCont runtime, XML commands, Modbus, HSB, logs, boot files, and autotests.

### `/home/ant/IdeaProjects/vcont-autotests`

- Purpose: VCont pytest autotests against VCont runtime and VCStudio typelibrary.
- Stack: Python 3.13 expected by README, pytest, ruff, Allure, Docker/GitLab CI.
- Known workflows:
  - Create/activate venv, then `pip install -r requirements.txt`.
  - Install internal common tools when needed: `pip install --extra-index-url https://nexus.isource.dev/repository/pypi-vcont-release/simple/ vcont-common-tools==1.1.21`.
  - Local test run requires a running VCont (`sudo ./vcont.sh`) and `PYTHONPATH` including the project root.
- Verification commands:
  - Targeted: `pytest /path/to/test_or_dir`.
  - CI-style with Allure: `allurectl watch --results allure-results -- python -m pytest --alluredir allure-results tests/pytest_test -v`.
  - Lint policy in CI: `ruff check`.
- Notes: Use `autotest-engineer` for fixtures/flaky tests and `vcont` for runtime protocol details.

### `/home/ant/IdeaProjects/vcont-qa-infrastructure`

- Purpose: Terraform configuration for VCont fuzzing infrastructure in Yandex Cloud.
- Stack: Terraform, Helm, Yandex Cloud, Object Storage, KMS, Cloud Logging, private Nexus/registry.
- Known workflows:
  - `terraform init`
  - `terraform plan`
  - `terraform apply`
- Verification commands:
  - Prefer `terraform fmt -check`, `terraform validate`, and `terraform plan` before changing infrastructure.
- Notes: Requires Yandex Cloud access. Treat `terraform apply` as a high-impact command; do not run it without explicit user confirmation.

### `/home/ant/IdeaProjects/vcont-hsb`

- Purpose: Local two-node VCont Hot Standby stand with HSB tests.
- Stack: Python pytest, Docker Compose, Allure, VCont binary distributions in `vcont1/` and `vcont2/`.
- Known workflows:
  - Start HSB pair: `docker compose up --build -d`.
  - Inspect stand: `docker compose ps`, `docker compose logs -f`.
  - Stop stand: `docker compose down`.
  - Local no-Docker run: `./vcont1/vcont-lin.x86_64-arch/run-vcont.sh` and `./vcont2/vcont-lin.x86_64-arch/run-vcont.sh`.
  - Install test deps: `python3 -m venv .venv`, `. .venv/bin/activate`, `pip install -r requirements.txt`.
- Verification commands:
  - Full tests: `pytest`.
  - Allure results: `pytest --alluredir=allure-results`.
  - Local report: `allure serve allure-results`.
- Notes: `pytest.ini` uses `tests/pytest_test`; markers include `docker` and `slow`. Use the `vcont` skill for HSB behavior, logs, eCAL, and XML command context.

### `/home/ant/IdeaProjects/vcont-runtime-runner`

- Purpose: VCont runtime runner packaging/container project.
- Stack: Dockerfile, GitLab CI, bundled `vcont.tgz`.
- Known workflows:
  - README is still the default GitLab template; inspect `.gitlab-ci.yml` and `Dockerfile` before edits.
  - Expected surface is packaging a VCont runtime artifact into a runner image.
- Verification commands:
  - Validate Docker changes with a local image build if the required `vcont.tgz` artifact is present.
- Notes: Do not infer behavior from README; it is not project-specific.

### `/home/ant/IdeaProjects/vcont-gateway`

- Purpose: Proxy between VCStudio IDE and VCont controller; validates XML requests/responses and writes reports.
- Stack: Python 3.11+ locally, Python 3.13-slim in packaging, Docker Compose, GitLab CI.
- Known workflows:
  - Local deps: `python -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`.
  - Internal dependency for local run: `pip install ./gateway/vcont_common_tools.tar.gz` after obtaining the CI-produced archive.
  - Local gateway run: `python -m gateway.main`.
  - Compose run: `docker compose up --build`.
  - Compose cleanup: `docker compose down -v`.
- Verification commands:
  - For gateway behavior, run the gateway against an available VCont controller at the expected port.
  - For packaging changes, inspect `.gitlab-ci.yml`; CI builds `vcontgateway.tar.gz`.
- Notes: Repo does not include VCont binaries or `vcont_common_tools.tar.gz` by default; CI/Nexus supplies them.

### `/home/ant/IdeaProjects/configurator`

- Purpose: End-to-end tests for the Configurator command service over SSH, with Allure output.
- Stack: Python pytest, SSH helpers, `.env`, VM/runtime artifacts, Allure, optional libvirt/VM flows.
- Known workflows:
  - First setup requires `.env` and root `vcont_plc.qcow2`.
  - Automated setup: `sudo bash setup_project.sh` (installs system packages, Allure CLI/allurectl, prepares `.venv`, runs `pytest -m onlyrtvm`).
  - Manual deps: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install --upgrade pip`, `pip install -r requirements.txt`.
- Verification commands:
  - Smoke: `pytest test_commands/system/test_cmd_help_describe.py`.
  - Full: `pytest test_commands`.
  - Useful filters: `pytest -m onlyvirtserver`, `pytest -m onlyrtvm`, `pytest -k backup`, `pytest test_commands/system/test_cmd_console.py`.
  - Explicit Allure: `pytest test_commands --alluredir=allure-results --clean-alluredir`.
  - Local report: `allure serve allure-results`.
- Notes: `pytest.ini` defaults to `test_commands/`, `--alluredir allure-results`, `--clean-alluredir`, `-vvs`. Reuse `helpers/` and `test_commands/conftest.py`; avoid duplicating SSH logic.

### `/home/ant/IdeaProjects/opener-runners`

- Purpose: Docker Compose integration stand for VCont with 30 OpENer emulators and Dozzle.
- Stack: Docker Compose, offline Docker image tarballs, `install_docker.sh`.
- Known workflows:
  - Offline install/start: prepare `ubuntu-22.04.tar`, `dozzle-pr-3710.tar`, `vcont-snapshot/*`, `opener/OpENer`, then `chmod +x install_docker.sh`, `./install_docker.sh`.
  - If Docker is already installed: `docker compose up -d`.
  - Restart after compose changes: `docker compose down`, then `docker compose up -d`.
- Verification commands:
  - Check containers: `docker ps`.
  - Inspect logs through Dozzle or `docker compose logs`.
- Notes: Changes to emulator count require editing repeated service blocks and static IPs in `docker-compose.yaml`.

### `/home/ant/IdeaProjects/common-tools`

- Purpose: `vcont-common-tools` Python library used by `vcont_gateway`, `vcont_autotests`, and `fuzzing_hypothesys`.
- Stack: Python package with `setup.py`, Nexus release publishing through GitLab CI.
- Known workflows:
  - Local build: install `wheel` and `twine`, then `python setup.py sdist bdist_wheel`.
  - CI build step installs requirements, runs `python vcont_common_tools/common/tools.py`, then builds `sdist` and wheel.
  - Version bump is in `setup.py`.
- Verification commands:
  - Build package: `python setup.py sdist bdist_wheel`.
  - For publish readiness, inspect generated `dist/` and CI rules.
- Notes: Release upload uses Nexus credentials from Lockbox and runs on tags/manual/API/Web pipelines.

### `/home/ant/IdeaProjects/harbor`

- Purpose: Terraform configuration related to Harbor/platform infrastructure.
- Stack: Terraform, GitLab Terraform CI template.
- Known workflows:
  - README points to the internal Terraform CI template; inspect `.gitlab-ci.yml` and `*.tf` before changes.
- Verification commands:
  - Prefer `terraform fmt -check`, `terraform validate`, and `terraform plan`.
- Notes: Treat `terraform apply` and CI variable changes as high-impact operations.

### `/home/ant/IdeaProjects/vcstudio-db`

- Purpose: VCStudio database project.
- Stack: Python 3.12 pytest API/DB tests, Docker Compose Postgres + `vcservice.jar`, OpenAPI contract, ruff, mypy, Allure.
- Known workflows:
  - Local stand: `docker compose up --build`.
  - Cleanup stand: `docker compose down -v`.
  - Python deps: `python3.12 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`, `cp .env.example .env`.
  - If Docker subnet is exhausted, set another `VC_DOCKER_SUBNET` in `.env`.
- Verification commands:
  - Quality: `ruff format .`, `ruff check .`, `mypy`.
  - Full tests: `pytest -q`.
  - Schema contract: `pytest -q tests/test_db_schema.py`.
  - Explicit env run can pass `VC_BASE_URL`, `VC_DB_HOST`, `VC_DB_PORT`, `VC_DB_NAME`, `VC_DB_USER`, `VC_DB_PASSWORD`.
  - Allure report: `allure serve allure-results` or generate/open with Allure CLI.
- Notes: Use `database-engineer` for schema and SQL work. `pytest.ini` writes Allure results by default and markers include `smoke`, `contract`, `contract_stateful`, `stateful`.

### `/home/ant/IdeaProjects/st-lua-translator`

- Purpose: Black-box autotests for `ST -> Lua` translator binary.
- Stack: Python 3.12+, pytest, ruff, Allure, Lua 5.4-compatible runtime, setuptools project.
- Known workflows:
  - Full local checks: `bash scripts/run_local_checks.sh`.
  - The script creates `.venv`, installs `.[dev]`, runs `ruff check .`, and runs `pytest --alluredir allure-results`.
  - Translator archive lives at `sources/st2lua-translator.tar.gz`; harness unpacks to `.work/translator-dist`.
- Verification commands:
  - Full test suite: `./.venv/bin/python -m pytest -q`.
  - Declarative translation/runtime cases: `./.venv/bin/python -m pytest -q tests/test_translation_cases.py`.
  - Strict GitHub cases: `./.venv/bin/python -m pytest -q tests/test_github_projects.py`.
  - Allure report: `allure serve allure-results`.
- Notes: Some known regression cases can intentionally make pytest fail; use Allure results and local bug limitation reports to understand current translator defects.

### `/home/ant/IdeaProjects/fuzzing`

- Purpose: Early/default-template fuzzing repository with Docker Compose and `src/`/`fuzzing/` directories.
- Stack: Docker Compose; README is mostly default GitLab template.
- Known workflows:
  - Inspect `docker-compose.yml`, `src/`, and `fuzzing/` before assuming commands.
- Verification commands:
  - Validate compose changes with `docker compose config`.
- Notes: Use `fuzzing-bug-hunter` for targeted fuzzing and repro minimization. README is not reliable project documentation.

### `/home/ant/IdeaProjects/fuzzing-hypotesys`

- Purpose: VCont fuzzing hypotheses and systemd/container experiments.
- Stack: Python scripts, Docker Compose, Dockerfile, strategy files, reboot ping test subproject.
- Known workflows:
  - Build systemd test image: `docker build -t systemd-unit-test .`.
  - Run privileged systemd test container with cgroup mounts as documented in README.
  - Compose files: `docker-compose.yml` and `docker-compose-reboot-ping.yml`.
  - Python entrypoints include `fuzzing.py` and `random_links.py`.
- Verification commands:
  - Validate compose files with `docker compose config`.
  - For Python changes, inspect `requirements.txt` and run the narrow target script/test manually.
- Notes: Internal spelling is `fuzzing-hypotesys`/`fuzzing_hypothesys`; preserve existing names in paths and package references.

## Local Tooling Preferences

- Search text with `rg`; if system `rg` is not installed, Codex may have a vendored `rg` in its own package path.
- Prefer `gh` for GitHub PR/CI operations after `gh auth login`.
- Prefer `jq`/`yq` for structured JSON/YAML inspection.
- Prefer project-local package managers and lockfiles over global defaults.
