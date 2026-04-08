# API: аутентификация и использование

Основной источник:

- https://docs.qameta.io/allure-testops/advanced/api/

## Аутентификация

Работа с API Allure TestOps состоит из двух шагов:

1. Обменяй пользовательский API token на Bearer JWT:

```bash
curl -s -X POST "${ENDPOINT}/api/uaa/oauth/token" \
  --header "Expect:" \
  --header "Accept: application/json" \
  --form "grant_type=apitoken" \
  --form "scope=openid" \
  --form "token=${USER_TOKEN}"
```

2. Используй полученный JWT:

```bash
curl -s -G "${ENDPOINT}/api/uaa/me" \
  --header "Accept: application/json" \
  --header "Authorization: Bearer ${JWT_TOKEN}"
```

## Discovery

- Swagger UI доступен по адресу `<base-url>/swagger-ui.html`.
- Типовая стартовая точка для discovery: `GET /api/rs/project?page=0&size=10`.
- Используй Swagger, чтобы подтвердить имена endpoint-ов, обязательные query params и схемы payload для текущей версии инстанса.
- В документации API methods разделены по сервисам: Report Service, UAA Service и All Services.
- Для defect workflow на этом инстансе полезные стартовые endpoint-ы обычно лежат в `All Services`: `/api/defect`, `/api/issueschema`, `/api/issue`, `/api/testcase/{id}/defect`.

## Практический workflow для test case

Для повседневной работы с manual test case в Allure TestOps используй такой порядок:

1. Прочитай текущий test case:

```bash
scripts/allure_testops_api.sh testcase-get 1811
```

2. Если нужно менять статус, сначала прочитай workflow кейса и его статусы:

```bash
scripts/allure_testops_api.sh testcase-workflow 1811
scripts/allure_testops_api.sh GET /api/status '?workflowId=-1&page=0&size=50'
```

3. Только после этого меняй статус:

```bash
scripts/allure_testops_api.sh testcase-set-status 1811 -2 -1
```

4. Если меняешь сам test case, перед `PATCH /api/testcase/{id}` проверяй, что в данных не потеряются обязательные поля:
   - `description`
   - `precondition`
   - `scenario`
   - `expectedResult`

5. Для сценария считай обязательным правило: у каждого шага должен быть ожидаемый результат шага.
6. Для manual scenario используй UI-модель `POST /api/testcase/{id}/scenario`, а не только low-level step API.
7. После записи UI-модели перепроверяй low-level дерево `/api/testcase/{id}/step`, чтобы не потерять текст шагов.
8. Если expected result должен быть виден именно в UI-редакторе шагов, записывай его как дочерний step под `expectedResultId`, а не только как `expectedResult` field в `overview` или `scenario`.

## Практический workflow для defect

Для создания и ведения defect в Allure TestOps используй такой порядок:

1. Определи project id:

```bash
scripts/allure_testops_api.sh GET /api/rs/project '?page=0&size=10'
```

2. Проверь текущие дефекты проекта:

```bash
scripts/allure_testops_api.sh defect-list 3
```

3. Если нужен внешний issue, сначала проверь, есть ли у проекта issue schema:

```bash
scripts/allure_testops_api.sh issueschema-list 3
```

4. Если `content` пустой, не обещай `createissue` или `linkIssue` workflow до появления integration/schema.

5. Создавай defect через `POST /api/defect`. Минимально обязателен `projectId`, но для рабочей записи по умолчанию заполняй:
   - `projectId`
   - `name`
   - `description`
   - `matcher.name`
   - `matcher.messageRegex`
   - `matcher.traceRegex`

Пример максимально заполненного payload:

```json
{
  "projectId": 3,
  "name": "Тестовый дефект: кнопка \"Список всех образов\" не открывает список образов",
  "description": "Тип: тестовый дефект для проверки раздела Defects в Allure TestOps.\n\nКраткое описание:\nПри попытке открыть список всех образов интерфейс не переходит к списку.\n\nПредусловия:\n1. Пользователь авторизован.\n2. Открыт экран управления ВМ.\n\nШаги воспроизведения:\n1. Открыть экран управления ВМ.\n2. Нажать кнопку \"Список всех образов\".\n\nОжидаемый результат:\nОткрывается экран со списком всех образов.\n\nФактический результат:\nНавигация не происходит, пользователь остается на текущем экране.\n\nСерьезность: Major\nПриоритет: Medium\nОкружение: test / web UI / Chrome / Linux",
  "matcher": {
    "name": "Тестовый matcher: список образов",
    "messageRegex": ".*(Список всех образов|images list|navigation failed).*",
    "traceRegex": ".*(RouteNotFound|NavigationError|ImagesListPage).*"
  }
}
```

Пример вызова:

```bash
scripts/allure_testops_api.sh POST /api/defect '' '{"projectId":3,"name":"Тестовый дефект","description":"Подробное описание","matcher":{"name":"Тестовый matcher","messageRegex":".*(navigation failed).*","traceRegex":".*(NavigationError).*"}}'
scripts/allure_testops_api.sh defect-create-template /tmp/defect.json
scripts/allure_testops_api.sh defect-create /tmp/defect.json
```

6. После create defect перепроверь сам объект:

```bash
scripts/allure_testops_api.sh GET /api/defect/7
scripts/allure_testops_api.sh defect-get 7
scripts/allure_testops_api.sh defect-verify 7
```

7. Если при создании передавался matcher, проверь matcher-ы дефекта отдельно:

```bash
scripts/allure_testops_api.sh defect-matcher-list 7
```

8. Если нужно связать defect с manual test case:

```bash
scripts/allure_testops_api.sh testcase-link-defect 1860 7
scripts/allure_testops_api.sh testcase-defect-list 1860
scripts/allure_testops_api.sh testcase-unlink-defect 1860 7
```

9. Для link endpoint-а не рассчитывай на тело ответа. Он может вернуть `200 OK` с пустым body. Подтверждай связь повторным `GET`.

10. Для patch defect используй только реально поддерживаемые поля:
   - `name`
   - `description`
   - `closed`

Пример:

```bash
scripts/allure_testops_api.sh PATCH /api/defect/7 '' '{"closed":true}'
scripts/allure_testops_api.sh defect-patch 7 /tmp/defect-patch.json
scripts/allure_testops_api.sh defect-close 7
scripts/allure_testops_api.sh defect-reopen 7
```

Если нужно быстро переиспользовать существующий defect как основу для нового:

```bash
scripts/allure_testops_api.sh defect-clone 7 /tmp/defect-copy.json
```

## Практика изменения test case

`PATCH /api/testcase/{id}` поддерживает, среди прочего:

- `description`
- `precondition`
- `expectedResult`
- `scenario`
- `statusId`
- `workflowId`

Пример patch только статуса:

```bash
scripts/allure_testops_api.sh PATCH /api/testcase/1811 '' '{"statusId":-2,"workflowId":-1}'
```

Пример подхода для правки кейса:

1. Прочитать текущий объект.
2. Сохранить обязательные поля.
3. Изменить только нужные поля.
4. Проверить итоговый объект повторным `GET`.

## Практика работы со сценарием

Для чтения UI-сценария:

```bash
scripts/allure_testops_api.sh testcase-scenario-get 1811
```

Для чтения low-level дерева шагов:

```bash
scripts/allure_testops_api.sh testcase-step-tree 1811
```

Для записи expected result шага в том формате, который реально использует UI:

```bash
scripts/allure_testops_api.sh testcase-set-step-expected-result 1811 0 "Карточка демонстрационного тест-кейса открыта."
scripts/allure_testops_api.sh testcase-set-step-expected-result 1811 1 "Обязательные поля и шаги сценария заполнены."
```

Для согласованной записи сценария в обе модели:

```bash
scripts/allure_testops_api.sh testcase-sync-scenario 1811 /tmp/scenario.json
```

Практический порядок для manual scenario, если нужно, чтобы UI показывал шаг и ожидаемый результат:

1. Запиши или обнови UI-модель:

```bash
scripts/allure_testops_api.sh testcase-sync-scenario 1811 /tmp/scenario.json
```

2. Для каждого шага отдельно положи UI-visible expected result:

```bash
scripts/allure_testops_api.sh testcase-set-step-expected-result 1811 0 "Карточка демонстрационного тест-кейса открыта."
scripts/allure_testops_api.sh testcase-set-step-expected-result 1811 1 "Обязательные поля и шаги сценария заполнены."
```

## Важные замечания

- Срок жизни Bearer JWT ограничен конфигурацией инстанса.
- На этом инстансе UI ожидает, что expected result будет дочерним step внутри контейнера `expectedResultId`. Просто заполнить `overview.scenario.steps[].expectedResult` недостаточно.
- Raw upload тестовых результатов не считается стабильным публичным workflow; по умолчанию предпочитай `allurectl` или официальные CI plugins.
- `POST /api/defect` принимает `DefectCreateDto`; практически полезный payload обычно богаче, чем минимально обязательный `projectId`.
- `PATCH /api/defect/{id}` поддерживает только `name`, `description`, `closed`.
- Внешний issue workflow зависит от настроенных integration/schema проекта; пустой ответ `/api/issueschema` означает, что дефект можно вести локально в TestOps, но не нужно обещать создание external issue.
- `POST /api/testcase/{testCaseId}/defect/{defectId}` может успешно завершаться с пустым телом; проверяй связь отдельным `GET`.
