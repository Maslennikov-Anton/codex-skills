# Аутентификация и использование

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

5. Для сценария считай обязательным правило: у каждого шага должен быть ожидаемый результат шага. Если API-форма не позволяет задать его в одном запросе на создание шага, делай дополнительный `PATCH` шага и закрывай операцию только после этого.

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

## Важные замечания

- Срок жизни Bearer JWT ограничен конфигурацией инстанса.
- Raw upload тестовых результатов не считается стабильным публичным workflow; по умолчанию предпочитай `allurectl` или официальные CI plugins.
