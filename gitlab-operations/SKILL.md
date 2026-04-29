---
name: gitlab-operations
description: >
  Работать с GitLab: auth, repositories, issues, merge requests, pipelines,
  releases, variables и API через glab CLI, glab api, scripts или HTTP.
---

# GitLab Operations

Используй этот skill, когда задача связана с работой в GitLab как домене, а не только с одним конкретным инструментом. Предпочтительный toolchain: `glab` CLI, затем `glab api`, затем прямой REST/GraphQL через `curl` или scripts, если CLI не покрывает операцию.

## Что покрывает этот skill

- Аутентификацию и multi-host setup.
- Repo-операции: clone, fork, branch-aware workflows.
- Issues и merge requests.
- CI/CD pipelines, jobs и `.gitlab-ci.yml` patterns.
- Releases и variables.
- REST- и GraphQL-запросы к GitLab API.
- Troubleshooting вокруг token-ов, host resolution, CI auto-login и self-managed инстансов.

## Предпочтительный toolchain

1. Высокоуровневые команды `glab`.
2. `glab api` для точных REST/GraphQL операций.
3. Прямые HTTP-вызовы (`curl`, scripts) только если CLI не покрывает задачу или нужен нестандартный endpoint.
4. MCP/connector path использовать только если задача явно завязана на него или он удобнее текущего сценария.

## Workflow

1. Определи, что именно хочет пользователь:
   - repo workflow;
   - issue/MR workflow;
   - pipeline/job workflow;
   - release/admin workflow;
   - raw API access;
   - проектирование или исправление `.gitlab-ci.yml`.
2. Проверь target:
   - `gitlab.com`;
   - GitLab Dedicated;
   - self-managed GitLab.
3. Если auth может отсутствовать, начни с [references/auth-and-setup.md](references/auth-and-setup.md).
4. Если задача покрывается штатной командой `glab`, предпочитай её raw API-вызовам.
5. Если нужен точный endpoint, переходи на [references/api-mode.md](references/api-mode.md).
6. Если проблема в pipeline design или `.gitlab-ci.yml`, открой [references/ci-cd-patterns.md](references/ci-cd-patterns.md).
7. Если auth или host behavior выглядит нестабильно, до вывода о сломанном token-е открой [references/troubleshooting.md](references/troubleshooting.md).
8. Для automation предпочитай non-interactive flags, env vars и явный repo/hostname context.

## Какие references открывать

- Setup, token precedence, выбор host-а и CI auto-login:
  [references/auth-and-setup.md](references/auth-and-setup.md)
- Типовые `glab` workflows:
  [references/common-workflows.md](references/common-workflows.md)
- Матрица команд:
  [references/command-matrix.md](references/command-matrix.md)
- `glab api` для REST и GraphQL:
  [references/api-mode.md](references/api-mode.md)
- `.gitlab-ci.yml` patterns:
  [references/ci-cd-patterns.md](references/ci-cd-patterns.md)
- Troubleshooting:
  [references/troubleshooting.md](references/troubleshooting.md)

## Практические правила

- Для первичной настройки предпочитай `glab auth login`, но в automation лучше использовать env vars или `--stdin`.
- Предпочитай `-R/--repo`, когда работаешь вне целевого repository.
- Предпочитай `glab mr`, `glab issue`, `glab ci`, `glab release` и `glab variable` перед `glab api`.
- Используй `glab api`, когда CLI не покрывает точную операцию или когда GraphQL подходит лучше.
- Для `.gitlab-ci.yml` сначала уточняй цель pipeline: build/test/release/deploy/security/terraform.
- Не выводи personal access token-ы в ответ.
- Явно отмечай, когда поведение зависит от типа GitLab instance или role permissions.
