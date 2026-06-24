# Workspace Map

This file is a compact map of Ant's local repositories and recurring commands. Keep entries factual and short. Prefer commands documented here, but re-check the repo when a command can affect infrastructure, VMs, Docker volumes, cloud resources, or external systems.

## Repositories

### `/home/ant/IdeaProjects/vcont`

- Purpose: Eclipse 4diac FORTE-based VCont runtime/core for IEC 61499 control applications; builds runtime binaries and release archives.
- Stack: C++17, CMake >= 3.22, Bash build scripts, GitLab CI, Docker/Kaniko, Nexus, Harbor.
- Known workflows:
  - Standard POSIX build: `./setup_posix.sh`, then `cd bin/posix`, then `make`.
  - Full VCont x86_64 artifact build expects sibling dirs `vcont`, `vcont-libraries`, clones `vcont-modules`, then runs `./vcont/build/linux/build_vcont_posix.sh`.
  - Test build: `./vcont/build/linux/build_vcont_posix.sh test`, then `cd vcont-x86_64-arch`, then `./forte_test`.
  - Cross builds supported by script args: `./vcont/build/linux/build_vcont_posix.sh aarch64` and `./vcont/build/linux/build_vcont_posix.sh mips`.
  - CI artifact outputs include `vcont.lin.x86_64.tgz` and `vcont.lin.aarch64.tgz`.
  - Reset bad CMake state from build dir: `rm -Rf CMakeCache.txt CMakeFiles/`.
  - Local RPM build: `tito build --test --rpm`.
- Verification commands:
  - Narrow POSIX build: `./setup_posix.sh && cd bin/posix && make`.
  - CI-style unit test after required libraries are built: `./vcont/build/linux/build_vcont_posix.sh test && cd vcont-x86_64-arch && ./forte_test`.
  - Docker QA image check, if `vcont.tgz` is present in repo root: `docker build -f docker/Dockerfile_qa --target test .`.
- Notes: Current local branch is often feature work; check dirty worktree before edits. Use the `vcont` skill for VCont runtime, XML commands, Modbus, HSB, logs, boot files, and autotests.

### `/home/ant/IdeaProjects/vcont-autotests`

- Purpose: VCont pytest autotests against VCont runtime and VCStudio typelibrary.
- Stack: Python 3.13 expected by README, Docker image uses Python 3.12-slim, pytest, pymodbus, pydantic, xmltodict, ruff, Allure/TestOps, Docker/GitLab CI.
- Known workflows:
  - Create/activate venv, then `pip install -r requirements.txt`.
  - Install internal common tools when needed: `pip install --extra-index-url https://nexus.isource.dev/repository/pypi-vcont-release/simple/ vcont-common-tools==1.1.21`.
  - Local test run requires a running VCont (`sudo ./vcont.sh`) and `PYTHONPATH` including the project root.
- Verification commands:
  - Targeted: `pytest /path/to/test_or_dir`.
  - CI-style with Allure: `allurectl watch --results allure-results -- python -m pytest --alluredir allure-results tests/pytest_test -v`.
  - Lint policy in CI/MR: `ruff check --output-format=gitlab > code-quality-report.json`.
- Notes: Dockerfile currently installs `vcont-common-tools==1.1.32`, while README mentions `1.1.21`; verify intended version before pin changes. CI services include `pymodbus-server:1.0.0` and `vcont-runtime-runner:vcont-snapshot-1.1.0.12888`. Use `autotest-engineer` for fixtures/flaky tests and `vcont` for runtime protocol details.

### `/home/ant/IdeaProjects/vcont-qa-infrastructure`

- Purpose: Terraform deployment for VCont fuzzing infrastructure in Yandex Cloud: service account, Object Storage log bucket, KMS encryption, Cloud Logging, Kubernetes namespace/secrets, and Helm release `fuzzing`.
- Stack: Terraform >= 1.0, providers `yandex`, `kubernetes`, `helm`, `local`; S3 backend in Yandex Object Storage; private Harbor/Nexus credentials via Yandex Lockbox.
- Known workflows:
  - `terraform init`
  - `terraform plan`
  - `terraform apply`
- Verification commands:
  - Prefer `terraform fmt -check`, `terraform init`, `terraform validate`, and `terraform plan` before changing infrastructure.
- Notes: Requires Yandex Cloud access. Treat `terraform apply`, `terraform destroy`, state operations, IAM/service account keys, KMS, bucket lifecycle/encryption, Kubernetes secrets, Helm values, and `locals.fuzzing_users`/`locals.vm_users` changes as high-impact; do not run or change them without explicit confirmation.

### `/home/ant/IdeaProjects/vcont-hsb`

- Purpose: Local VCont Hot Standby stand for 2, 3, or 4 VCont instances, HSB behavior tests, heartbeat timing, and external Modbus failover checks.
- Stack: Python pytest, Docker Compose, Allure, VCont Debian package `vcont1/vcont.lin.x86_64.deb`, generated runtime under `.work/vcont-runtime`, minimal Modbus TCP server in `tests/tools/modbus_tcp_server.py`.
- Known workflows:
  - Prepare runtime: `python3 scripts/prepare_vcont_runtime.py --count 2` (or `--count 3/4`).
  - Start HSB pair with external Modbus server: `docker compose up --build -d`.
  - Start 3-node stand: `COMPOSE_PROFILES=hsb-3plus docker compose up --build -d`.
  - Start 4-node stand: `COMPOSE_PROFILES=hsb-3plus,hsb-4 docker compose up --build -d`.
  - Inspect stand: `docker compose ps`, `docker compose logs -f`.
  - Stop stand: `docker compose down`.
  - Local no-Docker run: prepare runtime, then `./.work/vcont-runtime/vcont1/vcont-lin.x86_64-arch/run-vcont.sh`.
  - Install test deps: `python3 -m venv .venv`, `. .venv/bin/activate`, `pip install -r requirements.txt`.
- Verification commands:
  - Full tests: `pytest`.
  - Allure results: `pytest --alluredir=allure-results`.
  - Docker smoke/e2e without slow scenarios: `pytest -m "docker and not slow" --alluredir=allure-results`.
  - External Modbus failover: `pytest tests/pytest_test/test_hsb_modbus_failover.py --alluredir=allure-results`.
  - 3-node Modbus double failover: `pytest tests/pytest_test/test_hsb_modbus_failover.py::test_three_node_failover_continues_external_modbus_register_writes_twice --alluredir=allure-results`.
  - HSB heartbeat timing full run with terminal progress: `pytest -s tests/pytest_test/test_hsb_heartbeat_timing.py`.
  - HSB heartbeat timing debug run: `HSB_HEARTBEAT_TIMING_ITERATIONS=10 pytest -s tests/pytest_test/test_hsb_heartbeat_timing.py`.
  - Local report: `allure serve allure-results`.
- Notes: `pytest.ini` uses `tests/pytest_test`; markers include `docker` and `slow`. Runtime directories are generated from the `.deb`; old `.tgz`/unpacked `vcont1/vcont-lin.x86_64-arch` layouts are stale. Compose uses one shared image `vcont-hsb-vcont` for all VCont services so profiled `vcont3/vcont4` do not run stale images. `modbus-server` listens at `11.0.0.101:502` in Docker and `127.0.0.1:15020` from host. Modbus failover fboot writes synchronized counters to holding registers `2048..2050`; assertions require no zero reset and step `+1` across takeover. Heartbeat timing writes `reports/hsb-heartbeat-timing/report.md`; clean timing runs should have `data_quality.duplicate_measurement_count == 0`. Use the `vcont` skill for HSB behavior, logs, eCAL, fboot, Modbus, and XML command context.

### `/home/ant/IdeaProjects/vcont-runtime-runner`

- Purpose: Container packaging project for a VCont runtime runner image; Dockerfile expects `vcont.tgz` containing `vcont-x86_64-arch/*`.
- Stack: Dockerfile on `ubuntu:22.04`, GitLab CI, Kaniko, Nexus, Harbor.
- Known workflows:
  - README is still the default GitLab template; inspect `.gitlab-ci.yml` and `Dockerfile` before edits.
  - CI runs on tags only, downloads `vcont-develop-1.1.0.5132.lin.x86_64.tgz` from Nexus into `vcont.tgz`, builds with Kaniko, and publishes to `${HARBOR_URL}/vcont-qa/${CI_PROJECT_NAME}:${CI_COMMIT_TAG}`.
  - Local build, if `vcont.tgz` exists in repo root: `docker build -t vcont-runtime-runner:local .`.
- Verification commands:
  - Validate Docker changes with `docker build -t vcont-runtime-runner:local /home/ant/IdeaProjects/vcont-runtime-runner` if the required `vcont.tgz` artifact is present.
- Notes: `vcont.tgz` is not necessarily bundled locally; CI downloads it. Do not infer behavior from README; it is not project-specific.

### `/home/ant/IdeaProjects/vcont-gateway`

- Purpose: Proxy between VCStudio IDE and VCont controller; validates XML requests/responses and writes reports.
- Stack: Python 3.11+ locally, Python 3.13-slim in packaging, Docker Compose, GitLab CI, Nexus artifacts, `vcont_common_tools`, `xmltodict`, `pydantic`.
- Known workflows:
  - Local deps: `python -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`.
  - Internal dependency for local run: `pip install ./gateway/vcont_common_tools.tar.gz` after obtaining the CI-produced archive.
  - Local gateway run: `python -m gateway.main`.
  - Compose run: `docker compose up --build`.
  - Compose cleanup: `docker compose down -v`.
- Verification commands:
  - Gateway behavior requires an available VCont controller, normally `localhost:61498`; gateway listens on `61499`.
  - For packaging changes, inspect/replay `.gitlab-ci.yml` build steps with Nexus variables/artifacts available; CI builds `vcontgateway.tar.gz`.
- Notes: Repo does not include VCont binaries or `gateway/vcont_common_tools.tar.gz` by default. Compose has `gateway` and `vcont` services and mounts `./gateway/reports:/app/reports`.

### `/home/ant/IdeaProjects/configurator`

- Purpose: End-to-end tests for the Configurator command service over SSH, with Allure output.
- Stack: Python 3.10+, pytest, Paramiko, python-dotenv, SSH helpers, `.env`, VM/runtime artifacts, Allure, optional libvirt/QEMU runtime VM flow.
- Known workflows:
  - First setup requires `.env` and root `vcont_plc.qcow2`.
  - Automated setup: `sudo bash setup_project.sh` (installs system packages, Allure CLI 2.34.1, allurectl 2.17.0, prepares `.venv`, runs `pytest -m onlyrtvm`).
  - Manual deps: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install --upgrade pip`, `pip install -r requirements.txt`.
- Verification commands:
  - Smoke: `pytest test_commands/system/test_cmd_help_describe.py`.
  - Full: `pytest test_commands`.
  - Useful filters: `pytest -m onlyvirtserver`, `pytest -m onlyrtvm`, `pytest -k backup`, `pytest test_commands/system/test_cmd_console.py`.
  - Explicit Allure: `pytest test_commands --alluredir=allure-results --clean-alluredir`.
  - Local report: `allure serve allure-results`.
- Notes: No CI file found. `pytest.ini` defaults to `test_commands/`, `--alluredir allure-results`, `--clean-alluredir`, `-vvs`; markers include `onlyvirtserver`, `onlyrtvm`, `onhost`, `onrtvm`, `oncustomip`. Reuse `helpers/` and `test_commands/conftest.py`; avoid duplicating SSH logic.

### `/home/ant/IdeaProjects/opener-runners`

- Purpose: Docker Compose integration stand for VCont with 30 OpENer emulators and Dozzle log UI.
- Stack: Docker Compose, `ubuntu:22.04`, `amir20/dozzle:pr-3710`, local `vcont-snapshot/`, local `opener/OpENer`, offline image tarballs, `install_docker.sh`.
- Known workflows:
  - Offline-ish install/start: prepare `ubuntu-22.04.tar`, `dozzle-pr-3710.tar`, `vcont-snapshot/vcont`, optional `vcontcfg.json`, `vcont.fboot`, `libopen62541.so.1`, `opener/OpENer`, then `chmod +x install_docker.sh`, `./install_docker.sh`.
  - If Docker is already installed: `docker compose up -d`.
  - Restart after compose changes: `docker compose down`, then `docker compose up -d`.
- Verification commands:
  - Check containers: `docker ps`.
  - Inspect logs through Dozzle at `http://localhost:8080` or `docker compose logs`.
  - Compose syntax: `docker compose config`.
- Notes: README says offline launch, but `install_docker.sh` still runs `apt-get update`, adds Docker apt repo, and installs Docker packages from network; only image loading is local tar-based. Compose uses macvlan `my_macvlan` on host interface `enp7s0`; static IPs include `vcont-runner` `10.0.10.50`, `dozzle` `10.0.10.51`, `opener_1..30` `10.0.10.52..81`. Changes to emulator count require editing repeated service blocks and static IPs in `docker-compose.yaml`.

### `/home/ant/IdeaProjects/common-tools`

- Purpose: `vcont-common-tools` Python library used by `vcont_gateway`, `vcont_autotests`, and `fuzzing_hypothesys`.
- Stack: Python package with `setup.py`, Python >= 3.12, dependencies include `pydantic`, `attrs`, `sortedcontainers`, `xmltodict`, `pymodbus~=3.8.2`, Nexus release publishing through GitLab CI.
- Known workflows:
  - Local build: install `wheel` and `twine`, then `python setup.py sdist bdist_wheel`.
  - CI build step installs requirements and setuptools, runs `python vcont_common_tools/common/tools.py`, then builds `sdist` and wheel.
  - Package version comes from `CI_COMMIT_TAG`, defaulting to `0.0.0` locally.
- Verification commands:
  - Build package: `python setup.py sdist bdist_wheel`.
  - For publish readiness, inspect generated `dist/` and CI rules.
- Notes: Release upload uses Nexus credentials from Yandex Lockbox and runs on tags/manual/API/Web pipelines. CI downloads `vcstudio-linux-1.14.1-rc.tar.gz`, extracts `vcstudio/typelibrary`, and uploads to `pypi-vcont-release`.

### `/home/ant/IdeaProjects/harbor`

- Purpose: Terraform management for Harbor platform registry infrastructure: Harbor OIDC auth through Keycloak, Harbor projects, robot accounts, proxy registries, and Yandex Lockbox robot/admin secrets.
- Stack: Terraform >= 1.0, providers `yandex`, `harbor`, `keycloak`, `random`, `local`; S3 backend in Yandex Object Storage; GitLab Terraform CI template.
- Known workflows:
  - README points to the internal Terraform CI template; inspect `.gitlab-ci.yml` and `*.tf` before changes.
- Verification commands:
  - Prefer `terraform fmt -check`, `terraform validate`, and `terraform plan`.
- Notes: Managed areas include Harbor projects `platform`, `builders`, `library`, `inknowledge`, `vcont-qa`, `vcont` and related robots. Treat `terraform apply`, `terraform destroy`, state operations, Harbor auth/OIDC, project membership, robot accounts, generated passwords, Yandex Lockbox secrets, and CI variable changes as high-impact operations.

### `/home/ant/IdeaProjects/vcstudio-db`

- Purpose: VCStudio DB API autotests and local stand for `vcservice.jar` with Postgres.
- Stack: Python 3.12 pytest API/DB tests, Docker Compose Postgres + `vcservice.jar`, OpenAPI contract, ruff, mypy, Allure.
- Known workflows:
  - Local stand: `docker compose up --build`.
  - Readiness smoke: `curl -sk https://localhost:9443/auth/welcome`.
  - Cleanup stand: `docker compose down -v`.
  - Python deps: `python3.12 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`, `cp .env.example .env`.
  - Non-compose server run requires local Postgres 16 and `java -DIGNORE_DB_CERT=true -jar service/vcservice.jar`.
  - If Docker subnet is exhausted, set another `VC_DOCKER_SUBNET` in `.env`.
- Verification commands:
  - Quality: `ruff format --check .`, `ruff check .`, `mypy`.
  - Local formatting: `ruff format .`.
  - Full tests: `pytest -q`.
  - Schema contract: `pytest -q tests/test_db_schema.py`.
  - Explicit env run can pass `VC_BASE_URL`, `VC_DB_HOST`, `VC_DB_PORT`, `VC_DB_NAME`, `VC_DB_USER`, `VC_DB_PASSWORD`.
  - Allure report: `allure serve allure-results` or generate/open with Allure CLI.
- Notes: Compose publishes Postgres on `localhost:15432` and service HTTPS on `localhost:9443`; `vcstudio-service` uses `network_mode: service:postgres`. GitLab CI has `check` and `test` stages; test starts Postgres service, runs `vcservice.jar`, waits via `scripts/wait_for_service.py`, then runs `python -m pytest -q`. Use `database-engineer` for schema and SQL work. `pytest.ini` writes Allure results by default with `-vvs`; markers include `smoke`, `contract`, `contract_stateful`, `stateful`.

### `/home/ant/IdeaProjects/st-lua-translator`

- Purpose: Black-box autotests for `ST -> Lua` translator binary.
- Stack: Python 3.12+, pytest, ruff, Allure, Lua 5.4-compatible runtime, setuptools project.
- Known workflows:
  - Full local checks: `bash scripts/run_local_checks.sh`.
  - The script creates `.venv`, installs `.[dev]`, runs `ruff check .`, and runs `pytest --alluredir allure-results`.
  - Compose wrapper for the same local checks: `docker compose run --rm tests` or `docker compose up --build`.
  - Translator archive lives at `sources/st2lua-translator.tar.gz`; harness unpacks to `.work/translator-dist`.
  - If `sources/st2lua-translator.tar.gz` changes, remove `.work/translator-dist` or let the harness refresh it before trusting old run results.
  - Strict GitHub cases live in `tests/github_projects/manifest.json`; entries can declare `translation.must_succeed = false` with `failure_contains` when a real snippet is expected to be rejected by the translator policy.
  - `docs/BUG_LIMITATIONS_REPORT.md` is a local ignored report, not a tracked deliverable. Use it to summarize current test signals, but do not stage/push it when following `.gitignore`.
- Verification commands:
  - Full test suite: `./.venv/bin/python -m pytest -q`.
  - Declarative translation/runtime cases: `./.venv/bin/python -m pytest -q tests/test_translation_cases.py`.
  - Strict GitHub cases: `./.venv/bin/python -m pytest -q tests/test_github_projects.py`.
  - Targeted metadata/oracle smoke: `./.venv/bin/python -m pytest tests/test_translation_cases.py::test_case_metadata_contract tests/test_translation_cases.py::test_translation_strict[function_block_internal_state_translation] tests/test_translation_cases.py::test_translation_negative[negative_missing_semicolon] tests/test_github_projects.py::test_real_github_snippets_require_semantic_match[canopen_segment_copy_checksum] tests/test_github_projects.py::test_real_github_snippets_require_semantic_match[utilities_byte_base64_alphabet_lookup] -q`.
  - Python lint for GitHub strict harness edits: `./.venv/bin/python -m ruff check tests/test_github_projects.py`.
  - Python syntax check for harness edits: `./.venv/bin/python -m compileall tests/test_github_projects.py`.
  - Allure report: `allure serve allure-results`.
- Notes: `compose.yaml` runs `bash scripts/run_local_checks.sh` in a `tests` service; no `pytest.ini`; pytest config is in `pyproject.toml`. Markers include `bug`, `github_projects`, `runtime`, `smoke`, `regression`. GitLab CI installs `lua5.4`, runs `ruff check .` and `python3 -m compileall src tests scripts`; CI test job runs `python3 -m pytest --alluredir allure-results || true`, so current translator failures can be collected as artifacts without failing the job. Some supported negative cases intentionally expect translator rejection; do not convert policy rejections into bugs without product confirmation. `.gitignore` excludes `.codex`, `.venv`, `.work`, `.tools`, `artifacts`, `allure-results`, and `docs`; for pushes, stage explicit tracked paths only and keep ignored reports/caches local.

### `/home/ant/IdeaProjects/st-lua-translator-integration`

- Purpose: Integration qualification harness for `ST -> Lua -> VCont -> IDE READ`, validating translated Lua through both `vcont.fboot` and Studio-like XML command loading.
- Stack: Python 3.12, pytest, ruff, mypy, yamllint, Allure, Docker Compose VCont runtime, JSON case matrix under `tests/cases`.
- Known workflows:
  - Fast contract gate: `bash scripts/run_local_checks.sh -m contract`.
  - Runtime VCont slice: `docker compose run --rm vcont-integration -m vcont -k "<case_id or expression>" --require-vcont --junitxml=<file>.xml`.
  - Stop runtime containers after VCont runs: `docker compose down --remove-orphans`.
  - Case matrix docs: `docs/TRANSLATOR_STANDARD_COVERAGE.md`; Studio load research: `docs/STUDIO_COMMAND_LOAD_RESEARCH.md`.
- Verification commands:
  - Matrix count/schema smoke: `PYTHONPATH=src python3 - <<'PY'` with `load_cases()` and `validate_cases()`.
  - Standard local gate: `bash scripts/run_local_checks.sh -m contract`.
  - Whitespace gate before commit: `git diff --check` or `git diff --cached --check`.
- Notes: Keep the suite integration-only: cases should be `supported_runtime`, load into VCont, and be checked through `READ` in both `fboot` and `studio` modes. Expected-positive product gaps stay as red tests in JUnit/Allure; do not move them into negative/xfail/inventory files. `.gitignore` excludes `.venv`, `.work`, Allure/JUnit, caches and temporary exit-code files; leave runtime artifacts local unless the user explicitly asks for cleanup.

### `/home/ant/IdeaProjects/fuzzing`

- Purpose: Early VCont fuzzing/proxy experiments; README is default GitLab template, real surface is compose plus `src/` and `fuzzing/`.
- Stack: Docker Compose, Python 3.12-slim fuzzing image, Hypothesis, Pydantic, xmltodict; VCont runner image.
- Known workflows:
  - Compose expects prebuilt images `vcont-runtime-runner:1.1.0` and `fuzzing:1.0.0`.
  - Fuzzing Dockerfile installs `xmltodict pydantic==2.9.2 hypothesis` and runs `python fuzzing.py`.
  - Python fuzzing connects to VCont host `vcont`, port `61498`.
- Verification commands:
  - Validate compose changes with `docker compose config`.
  - Stand start, if images exist and no shared containers conflict: `docker compose up -d`.
- Notes: README is not reliable project documentation. Compose uses fixed `container_name: vcont` and `container_name: fuzzing`; avoid starting it without checking for name conflicts. `fuzzing/fuzzing_hypotesys/Dockerfile` has `COPY ../../src ./src/`, so validate build context before direct `docker build`. Use `fuzzing-bug-hunter` for targeted fuzzing and repro minimization.

### `/home/ant/IdeaProjects/fuzzing-hypotesys`

- Purpose: VCont fuzzing hypotheses and systemd/container experiments.
- Stack: Python 3.12-slim, Hypothesis, Pydantic, xmltodict, `vcont_common_tools` from Nexus, Docker Compose, Dockerfile, strategy files, reboot ping test subproject, GitLab CI with Kaniko.
- Known workflows:
  - README systemd-style container command: `docker build -t systemd-unit-test .`, then privileged `docker run ... systemd-unit-test`.
  - Main compose: `docker compose -f docker-compose.yml up --build`.
  - Reboot ping compose: `docker compose -f docker-compose-reboot-ping.yml up --build`.
  - Root Dockerfile installs `requirements.txt`, installs `vcont_common_tools` from Nexus via `NEXUS_LOGIN`/`NEXUS_SECRET`, then runs `python fuzzing.py`.
  - VCont image build requires `vcont/vcont.tgz`; VCont exposes `1503` and `61499`.
- Verification commands:
  - Validate compose files with `docker compose config` and `docker compose -f docker-compose-reboot-ping.yml config`.
  - Local build requires required artifacts/secrets: `docker compose up --build`.
  - For Python changes, inspect `requirements.txt` and run the narrow target script/test manually.
- Notes: Internal spelling is `fuzzing-hypotesys`/`fuzzing_hypothesys`; preserve existing names in paths and package references. README appears stale: root `Dockerfile` is Python fuzzing, not a systemd unit image. CI runs only on tags and publishes `${HARBOR_URL}/vcont-qa/fuzzing:${CI_COMMIT_TAG}` through Kaniko after fetching Harbor/Nexus secrets from Yandex Lockbox.

### `/home/ant/codex-skills`

- Purpose: Local Codex skills and references used across Ant's workspaces.
- Stack: Markdown `SKILL.md`, YAML frontmatter, optional `references/`, `scripts/`, `assets/`, Python validation script from `.system/skill-creator`.
- Known workflows:
  - Inspect local changes: `git status --short`, `git diff --stat`, `git diff`.
  - Validate one skill: `python3 .system/skill-creator/scripts/quick_validate.py <skill-dir>`.
  - Validate repo-wide/common-rule changes: `python3 scripts/audit_skills.py --root /home/ant/codex-skills`.
  - Check markdown/reference link targets with `rg` and file existence.
- Verification commands:
  - `git diff --check`
  - `python3 .system/skill-creator/scripts/quick_validate.py <skill-dir>`
  - `python3 scripts/audit_skills.py --root /home/ant/codex-skills`
- Notes: Keep `SKILL.md` small and route detailed content to `references/`. Use `para-memory-files` for memory recall/update behavior; this repo documents local skills and validation. Skill sync/push is in scope only when the user asks; otherwise stop at local diff/validation recommendations. Use `quick_validate.py` for narrow single-skill edits; use `audit_skills.py` for trigger rules, shared conventions, or common validation behavior changes.

## Local Tooling Preferences

- Search text with `rg`; if system `rg` is not installed, Codex may have a vendored `rg` in its own package path.
- Prefer `gh` for GitHub PR/CI operations after `gh auth login`.
- Prefer `jq`/`yq` for structured JSON/YAML inspection.
- Prefer project-local package managers and lockfiles over global defaults.
