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
9. Для manual scenario в Allure 5.23.0 используй как write-endpoint `POST /api/testcase/{id}/scenario`, но не считай `GET /api/testcase/{id}/scenario` единственным источником истины: этот endpoint deprecated.
10. Для проверки того, что карточка test case действительно видит шаги и expected result, используй `GET /api/testcase/{id}/overview` и смотри `scenario.steps[].expectedResult`.
11. Для этого UI expected result шага в редакторе хранится не как plain field у root-step, а как дочерний step под контейнером `expectedResultId` из `GET /api/testcase/{id}/step`.
12. Если пользователь редактирует expected result в UI, фронтенд отправляет `POST /api/testcase/step?withExpectedResult=false` с `parentId=<expectedResultId>` и `bodyJson`, то есть создает дочерний step внутри expected-result container.
13. Если после обновления UI-модели текст шагов в редакторе или low-level дереве пустеет, синхронизируй low-level model через `GET /api/testcase/{id}/step` и `PATCH /api/testcase/step/{stepId}`.
14. Для повторяемых операций со сценарием предпочитай helper-команду `testcase-sync-scenario`, потому что она обновляет обе модели согласованно и после записи перепроверяет `overview`.
15. Для записи expected result шага в том виде, который реально видит UI, используй helper-команду `testcase-set-step-expected-result`.
16. Для загрузки результатов не придумывай raw upload flow самостоятельно; предпочитай `allurectl` или официальные CI plugins.

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
scripts/allure_testops_api.sh testcase-overview-get 1811
scripts/allure_testops_api.sh testcase-workflow 1811
scripts/allure_testops_api.sh testcase-set-status 1811 -2 -1
scripts/allure_testops_api.sh testcase-scenario-get 1811
scripts/allure_testops_api.sh testcase-step-tree 1811
scripts/allure_testops_api.sh testcase-sync-scenario 1811 /tmp/scenario.json
scripts/allure_testops_api.sh testcase-set-step-expected-result 1811 0 "Ожидаемый результат первого шага"
```

## Какие references открывать

- Auth flow и operating rules:
  [references/auth-and-usage.md](references/auth-and-usage.md)
- Модель сценария и синхронизация UI/low-level представлений:
  [references/scenario-models.md](references/scenario-models.md)

## Правила работы

- Всегда обменивай долгоживущий API token на короткоживущий JWT перед API-вызовами.
- Предпочитай `Accept: application/json`.
- Используй Swagger на целевом инстансе, чтобы подтвердить форму запроса и обязательные параметры.
- Перед изменением статуса test case сначала получай `workflow` кейса и допустимые статусы этого workflow, а потом выполняй `PATCH`.
- Для create/update test case не допускай пустых `description`, `precondition`, `scenario` и `expectedResult`.
- Для каждого шага сценария обеспечивай expected result этого шага.
- Для Allure 5.23.0 не считай `/api/testcase/{id}/step` источником истины для manual scenario в UI.
- Для проверки фактического содержимого карточки test case предпочитай `/api/testcase/{id}/overview`, потому что он возвращает `scenario` так, как его собирает backend для UI.
- `GET /api/testcase/{id}/scenario` deprecated и подходит только как вспомогательная проверка, но не как финальный критерий того, что UI увидит expected result.
- Для этого конкретного UI plain `expectedResult` в `overview` недостаточен, чтобы expected result появился в редакторе шагов.
- Ожидаемый результат шага в редакторе materialize-ится как дочерний step под узлом `expectedResultId` в low-level дереве `GET /api/testcase/{id}/step`.
- Не пытайся полагаться только на `PATCH /api/testcase/step/{stepId}?withExpectedResult=true`: на этом инстансе он обновляет `body` шага, но не materialize-ит UI-visible expected result.
- Если нужно, чтобы expected result гарантированно появился в UI, создай или обнови дочерний step под `expectedResultId`.
- После обновления `/api/testcase/{id}/scenario` перепроверяй, не потерялся ли текст шагов в `/api/testcase/{id}/step`. Если потерялся, синхронизируй `body` корневых шагов из `name` UI-сценария.
- После любых изменений сценария перепроверяй `GET /api/testcase/{id}/overview` и убеждайся, что `scenario.steps[].expectedResult` заполнен.
- Перед patch test case по умолчанию сначала читай текущий объект и меняй только те поля, которые пользователь явно запросил изменить.
- Считай загрузку raw test results неподдерживаемой для hand-rolled интеграций, если пользователь явно не настаивает; по умолчанию предпочитай `allurectl`.
