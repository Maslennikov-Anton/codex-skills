---
name: allure-testops-api
description: >
  Работать с HTTP API Allure TestOps: аутентифицироваться по пользовательскому
  API token, обменивать его на Bearer JWT, смотреть Swagger на целевом инстансе,
  читать и изменять проекты, test case-ы, launches, jobs и связанные сущности.
  Использовать, когда пользователь просит автоматизировать, исследовать,
  отладить или операционно использовать Allure TestOps через curl, shell scripts
  или Python. Для повторяемых аутентифицированных вызовов предпочитать bundled
  helper script.
---

# Allure TestOps API

Используй этот skill, когда задача связана с HTTP API Allure TestOps.

## Локальные настройки по умолчанию

Для этой машины по умолчанию используй локальный файл секретов:

- `/home/ant/.allure-testops.env`

Ожидаемые переменные:

- `ALLURE_TESTOPS_URL`
- `ALLURE_TESTOPS_TOKEN`

Не печатай token в ответах.

## Workflow

1. Проверь, что файл секретов существует или что env vars заданы.
2. Обмени пользовательский API token на Bearer JWT через `POST /api/uaa/oauth/token`.
3. Используй Bearer JWT для API-вызовов.
4. Сначала определи доступные проекты, например через `GET /api/rs/project`.
5. Для discovery endpoint-ов предпочитай Swagger UI инстанса по адресу `<base-url>/swagger-ui.html`.
6. Перед записью всегда получай текущий объект, а для операций со статусом test case дополнительно получай его workflow и список допустимых статусов этого workflow.
7. При создании или изменении test case считай обязательными для заполнения поля: `description`, `precondition`, `scenario`, `expectedResult`.
8. Для сценария test case считай обязательным правило: у каждого шага должен быть явно прописан ожидаемый результат шага. Не оставляй шаги без expected result.
9. Для загрузки результатов не придумывай raw upload flow самостоятельно; предпочитай `allurectl` или официальные CI plugins.

## Минимальный auth flow

Сгенерируй Bearer JWT из пользовательского API token:

```bash
scripts/allure_testops_api.sh auth
```

Вызови API path с полученным JWT:

```bash
scripts/allure_testops_api.sh GET /api/rs/project '?page=0&size=10'
scripts/allure_testops_api.sh GET /api/rs/testcase '?projectId=3&page=0&size=10'
scripts/allure_testops_api.sh testcase-get 1811
scripts/allure_testops_api.sh testcase-workflow 1811
scripts/allure_testops_api.sh testcase-set-status 1811 -2 -1
```

## Какие references открывать

- Auth flow и operating rules:
  [references/auth-and-usage.md](references/auth-and-usage.md)

## Правила работы

- Всегда обменивай долгоживущий API token на короткоживущий JWT перед API-вызовами.
- Предпочитай `Accept: application/json`.
- Используй Swagger на целевом инстансе, чтобы подтвердить форму запроса и обязательные параметры.
- Перед изменением статуса test case сначала получай `workflow` кейса и допустимые статусы этого workflow, а потом выполняй `PATCH`.
- Для create/update test case не допускай пустых `description`, `precondition`, `scenario` и `expectedResult`.
- Для каждого шага сценария обеспечивай expected result этого шага; если API не позволяет задать его в том же запросе, делай дополнительный patch шага и не оставляй сценарий в промежуточном состоянии.
- Перед patch test case по умолчанию сначала читай текущий объект и меняй только те поля, которые пользователь явно запросил изменить.
- Считай загрузку raw test results неподдерживаемой для hand-rolled интеграций, если пользователь явно не настаивает; по умолчанию предпочитай `allurectl`.
