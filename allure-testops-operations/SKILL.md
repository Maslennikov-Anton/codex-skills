---
name: allure-testops-operations
description: >
  Работать с Allure TestOps end to end: аутентификация, проекты, test case-ы,
  launches, jobs, upload результатов и операционная диагностика. Использовать,
  когда пользователю нужна автоматизация, исследование, отладка или
  операционная работа с Allure TestOps через `allurectl`, HTTP API, shell
  scripts или CI-интеграции. По умолчанию предпочитать `allurectl` для upload
  flow и lifecycle launch, а HTTP API — для discovery и объектных операций.
---

# Allure TestOps Operations

Используй этот skill, когда задача связана с Allure TestOps как продуктом, а не только с одним API endpoint. Предпочтительный execution path: `allurectl` для upload/watch и lifecycle flows, затем HTTP API для discovery и операций над объектами, и только потом hand-rolled automation там, где официальный путь реально не покрывает задачу.

## Локальные настройки по умолчанию

Для этой машины по умолчанию используй локальный файл секретов:

- `/home/ant/.allure-testops.env`

Ожидаемые переменные:

- `ALLURE_TESTOPS_URL`
- `ALLURE_TESTOPS_TOKEN`

Не печатай token в ответах.

## Что покрывает этот skill

- Аутентификацию в Allure TestOps и discovery через Swagger.
- Проекты, test case-ы, launches, jobs и связанные сущности через HTTP API.
- Upload flow результатов через `allurectl upload` и `allurectl watch`.
- Launch lifecycle, launch metadata и диагностику проблем с ingestion.
- CI-автоматизацию вокруг Allure TestOps.
- Troubleshooting для кейсов, когда launch создан, но тесты, кейсы или статистика обновились не так, как ожидалось.

## Предпочтительный toolchain

1. `allurectl` для upload/watch и CI launch flows.
2. HTTP API для project/test case/job/launch operations и discovery через Swagger.
3. Bundled helper script для повторяемых API-вызовов.
4. Прямые `curl`/Python сценарии только если это действительно удобнее стандартного helper path.

## Workflow

1. Определи тип задачи:
   - upload/watch результатов;
   - object operations через API;
   - discovery и исследование текущего инстанса;
   - launch/job troubleshooting;
   - CI integration.
2. Проверь, что файл секретов существует или env vars заданы.
3. Если задача связана с upload результатов или CI-run, сначала открой [references/allurectl-workflows.md](references/allurectl-workflows.md).
4. Если задача связана с API discovery или изменением сущностей, открой [references/api-auth-and-usage.md](references/api-auth-and-usage.md).
5. Для discovery endpoint-ов предпочитай Swagger UI инстанса по адресу `<base-url>/swagger-ui.html`.
6. Если проблема связана с тем, что результаты загружены, но launch или test cases ведут себя странно, открой [references/launch-lifecycle-and-troubleshooting.md](references/launch-lifecycle-and-troubleshooting.md).
7. Перед изменением test case сначала получай текущий объект, а для операций со статусом дополнительно workflow и список допустимых статусов.
8. Для raw upload flow не придумывай hand-rolled API integration, если пользователь явно не требует этого; по умолчанию используй `allurectl`.

## Какие references открывать

- API auth, Swagger discovery и object operations:
  [references/api-auth-and-usage.md](references/api-auth-and-usage.md)
- Модель manual scenario и синхронизация UI/low-level представлений:
  [references/scenario-models.md](references/scenario-models.md)
- `allurectl` workflows, upload/watch и CI variables:
  [references/allurectl-workflows.md](references/allurectl-workflows.md)
- Launch lifecycle, project binding и troubleshooting:
  [references/launch-lifecycle-and-troubleshooting.md](references/launch-lifecycle-and-troubleshooting.md)

## Практические правила

- Для upload результатов по умолчанию предпочитай `allurectl`, а не raw API.
- Для API-вызовов всегда обменивай долгоживущий API token на короткоживущий JWT.
- Используй Swagger на целевом инстансе, чтобы подтвердить форму запроса и обязательные параметры.
- Перед изменением статуса test case сначала получай `workflow` кейса и допустимые статусы этого workflow.
- Для create/update test case не допускай пустых `description`, `precondition`, `scenario` и `expectedResult`.
- Для каждого шага manual scenario обеспечивай expected result этого шага.
- Пока launch открыт, не считай ingestion завершённым и не делай выводы по финальной статистике.
- Если test case уже привязан к другому project, не ожидай, что upload в новый project автоматически создаст новый кейс.
- Перед patch test case по умолчанию сначала читай текущий объект и меняй только те поля, которые пользователь явно запросил изменить.

## Минимальный auth flow для API

Сгенерируй Bearer JWT из пользовательского API token:

```bash
scripts/allure_testops_api.sh auth
```

Вызови API path с полученным JWT:

```bash
scripts/allure_testops_api.sh GET /api/rs/project '?page=0&size=10'
scripts/allure_testops_api.sh GET /api/rs/testcase '?projectId=3&page=0&size=10'
scripts/allure_testops_api.sh testcase-get 1811
scripts/allure_testops_api.sh testcase-overview-get 1811
scripts/allure_testops_api.sh testcase-workflow 1811
scripts/allure_testops_api.sh testcase-set-status 1811 -2 -1
scripts/allure_testops_api.sh testcase-scenario-get 1811
scripts/allure_testops_api.sh testcase-step-tree 1811
scripts/allure_testops_api.sh testcase-sync-scenario 1811 /tmp/scenario.json
scripts/allure_testops_api.sh testcase-set-step-expected-result 1811 0 "Ожидаемый результат первого шага"
```
