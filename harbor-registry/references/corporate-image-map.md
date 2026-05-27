# Corporate Harbor Image Map

Snapshot source: Harbor API via `/home/ant/.harbor/harbor.env`, refreshed
2026-05-22. This is guidance for choosing internal images first; verify live
with `harbor_inventory.py` or `docker pull` before changing production CI.

## Selection Rules

- Prefer `harbor.isource.dev/...` over Docker Hub, GHCR, Quay, Yandex mirrors,
  or other public registries when an equivalent image exists.
- For Docker Hub official images, API repository names appear as
  `docker/library/<name>`, but pull works in the shorter form
  `harbor.isource.dev/docker/<name>:<tag>`. The explicit
  `harbor.isource.dev/docker/library/<name>:<tag>` form also works.
- For external namespaces, keep the namespace after the Harbor project:
  `harbor.isource.dev/ghcr/astral-sh/ruff:0.13.1-alpine`,
  `harbor.isource.dev/quay/helmpack/chart-testing:<tag>`.
- Avoid `latest` unless the repo already uses it or the image is only published
  with `latest`; prefer explicit tags from Harbor.
- Treat `build-cache` tags as cache artifacts, not runtime or CI images.

## Projects

- `docker`: Docker Hub proxy/cache for base and CI images. Use for Ubuntu,
  Python, Docker-in-Docker, Maven/Gradle/Node, Terraform, Checkov, Swagger,
  OpenAPI generator, Sonar scanner, RabbitMQ, etc.
- `ghcr`: GHCR proxy/cache. Use for GHCR-origin tools such as Ruff, TFLint,
  CycloneDX cdxgen, LiteLLM, sing-box.
- `quay`: Quay proxy/cache. Currently includes chart-testing.
- `library`: internal/shared utility images, including Kaniko executor,
  curl+jq, docker+git, semantic-release, terragrunt, swiss-knife.
- `tools`: internal CI helper images, currently semgrep-to-sarif.
- `vcont`: VCont-owned component images such as OPC UA server.
- `vcont-qa`: VCont QA/runtime images, pymodbus server, fuzzing, vconttest.
- `qatools`: QA tools namespace; currently Allure TestOps image mirror.
- `ai-factory-demo`, `aws`: narrow/special-purpose namespaces.

## Pull-Verified Images

- `harbor.isource.dev/docker/ubuntu:24.04`
  - verified by `docker pull`, digest `sha256:c4a8d5503dfb...`
- `harbor.isource.dev/docker/python:3.12-slim`
  - verified by `docker pull`, digest `sha256:090ba77e2958...`
- `harbor.isource.dev/docker/library/python:3.12-slim`
  - same digest as the short Python ref.
- `harbor.isource.dev/vcont-qa/pymodbus-server:1.0.0`
  - verified by `docker pull`, digest `sha256:af0a918bd0ae...`
- `harbor.isource.dev/ghcr/astral-sh/ruff:0.13.1-alpine`
  - verified by `docker pull`, digest `sha256:b6ba7c154028...`

## Common Corporate Images

### Base And Language Images

- Ubuntu: `harbor.isource.dev/docker/ubuntu:24.04`
  - Use this for current Ubuntu/Noble VCont runtime Dockerfiles.
- Python: `harbor.isource.dev/docker/python:3.12-slim`
  - API tag seen under `docker/library/python`, pushed 2026-05-22.
- Java runtime: `harbor.isource.dev/docker/eclipse-temurin:25-jre-alpine`
  - API tag seen under `docker/library/eclipse-temurin`, pushed 2026-05-21.
- Docker-in-Docker: `harbor.isource.dev/docker/docker:28-dind`
  - API tag seen under `docker/library/docker`, pushed 2026-05-21.
- RabbitMQ management: `harbor.isource.dev/docker/rabbitmq:4-management`
  - API tag seen under `docker/library/rabbitmq`, pushed 2026-05-20.

### VCont And QA

- VCont runtime runner:
  `harbor.isource.dev/vcont-qa/vcont-runtime-runner:<tag>`
  - Ready-to-run Docker images of the VCont application for each application
    snapshot. Prefer these when a task needs a packaged VCont runtime image
    instead of building a runtime image from a local `.deb` or tarball.
  - Fast-moving snapshot stream; latest observed on 2026-05-22:
    `vcont-snapshot-1.1.0.22960`.
  - Earlier known tag from local VCont autotests context:
    `vcont-snapshot-1.1.0.12888`.
- Pymodbus server:
  `harbor.isource.dev/vcont-qa/pymodbus-server:1.0.0`
  - Also tagged `latest`; prefer `1.0.0`.
- VCont QA test image:
  `harbor.isource.dev/vcont-qa/vconttest:v.4.0.15`
  - Also tagged `latest`; prefer explicit `v.4.0.15` unless a repo already
    pins another vconttest tag.
- VCont fuzzing:
  `harbor.isource.dev/vcont-qa/fuzzing:2.0.8`
  - Latest observed tag from API snapshot.
- OPC UA server:
  `harbor.isource.dev/vcont/opcua_server:v1.0.46`
  - Older observed tag: `v1.0.43`.

### CI Utilities

- Kaniko executor: `harbor.isource.dev/library/kaniko-project/executor:debug`
- curl+jq: `harbor.isource.dev/library/alpine/curl-jq:1.0.1`
- Ruff: `harbor.isource.dev/ghcr/astral-sh/ruff:0.13.1-alpine`
- semgrep-to-sarif:
  `harbor.isource.dev/tools/ci/semgrep-sast-to-sarif:1.2.0`
- semantic-release:
  `harbor.isource.dev/library/debian/semantic-release:24.2.5`
- terragrunt: `harbor.isource.dev/library/debian/terragrunt:0.0.2`
- docker+git:
  `harbor.isource.dev/library/alpine/docker-git:28.0.1-cli-alpine3.21`
- swiss-knife: `harbor.isource.dev/library/alpine/swiss-knife:1.0`

## Known Gaps

- Many proxied repos in `docker`, `ghcr`, `quay`, and `qatools` show
  `artifact_count=0` in the API even when pull counts exist. Treat these as
  discoverable proxy entries; verify a concrete tag with `docker pull`.
- `docker/library/ubuntu` API tag listing returned no tags for `24.04`, but
  `docker pull harbor.isource.dev/docker/ubuntu:24.04` succeeds. Prefer pull
  verification for official Docker Hub base images.
