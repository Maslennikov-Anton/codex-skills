---
name: gitlab-glab-cli
description: >
  Работать с GitLab из терминала через официальный glab CLI. Использовать,
  когда пользователю нужна помощь с аутентификацией в GitLab, управлением
  репозиториями, issues, merge requests, pipelines, releases, variables или
  выполнением аутентифицированных REST- и GraphQL-запросов через `glab api`.
  Покрывает GitLab.com, GitLab Dedicated и self-managed инстансы GitLab.
---

# GitLab CLI (`glab`)

Используй этот skill, когда задача связана с работой в GitLab через официальный `glab` CLI, задокументированный на `https://docs.gitlab.com/cli/`.

## Что покрывает этот skill

- Аутентификацию и multi-host setup.
- Repo-операции: clone, fork, работа с учетом remote.
- Issues и merge requests.
- CI/CD pipelines и jobs.
- Releases.
- Variables.
- Аутентифицированные GitLab REST- и GraphQL-запросы через `glab api`.
- Troubleshooting вокруг token-ов, определения host-а, CI auto-login и self-managed инстансов.

## Workflow

1. Определи, что именно хочет пользователь:
   - обычный repo workflow;
   - workflow для issue/MR;
   - CI/CD workflow;
   - release/admin workflow;
   - raw API access через `glab api`.
2. Проверь, с каким target идет работа:
   - `gitlab.com`;
   - GitLab Dedicated;
   - self-managed GitLab.
3. Если аутентификация может отсутствовать, начни с [references/auth-and-setup.md](references/auth-and-setup.md).
4. Если auth на self-managed GitLab ведет себя нестабильно, до вывода о невалидном token-е открой еще и [references/troubleshooting.md](references/troubleshooting.md).
5. Если существует более высокоуровневая команда `glab`, предпочитай ее raw API-вызовам.
6. Если `glab` не дает чисто выполнить нужную операцию, переходи на `glab api`.
7. Если команда зависит от repo context, проверь, выполняется ли она:
   - внутри нужного Git repository;
   - с `-R/--repo`;
   - с `--hostname` для cross-host работы.
8. Для automation и scripts предпочитай non-interactive flags и env vars вместо prompt-ов.

## Какие references открывать

- Setup, token precedence, выбор host-а и CI auto-login:
  [references/auth-and-setup.md](references/auth-and-setup.md)
- Типовые command workflows:
  [references/common-workflows.md](references/common-workflows.md)
- Матрица команд по областям:
  [references/command-matrix.md](references/command-matrix.md)
- `glab api` for REST and GraphQL:
  [references/api-mode.md](references/api-mode.md)
- Troubleshooting:
  [references/troubleshooting.md](references/troubleshooting.md)

## Практические правила

- Для первичной настройки предпочитай `glab auth login`, но в automation лучше использовать env vars или `--stdin`.
- Предпочитай `-R/--repo`, когда работаешь вне целевого repository.
- Предпочитай `glab mr`, `glab issue`, `glab ci`, `glab release` и `glab variable` перед `glab api`.
- Используй `glab api`, когда CLI не покрывает точную операцию или когда GraphQL подходит лучше.
- Не выводи personal access token-ы в ответ.
- Явно отмечай, когда поведение зависит от типа GitLab instance или role permissions.
