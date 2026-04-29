---
name: allure-testops-operations
description: >
  Работать с Allure TestOps: auth, проекты, test cases, defects, launches,
  jobs, upload результатов и диагностика через allurectl, HTTP API, shell или CI.
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
- Проекты, test case-ы, defects, launches, jobs и связанные сущности через HTTP API.
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
   - defects/issues operations через API;
   - discovery и исследование текущего инстанса;
   - launch/job troubleshooting;
   - CI integration.
2. Проверь, что файл секретов существует или env vars заданы.
3. Если задача связана с upload результатов или CI-run, сначала открой [references/allurectl-workflows.md](references/allurectl-workflows.md).
4. Если задача связана с API discovery или изменением сущностей, открой [references/api-auth-and-usage.md](references/api-auth-and-usage.md).
5. Для discovery endpoint-ов предпочитай Swagger UI инстанса по адресу `<base-url>/swagger-ui.html`.
6. Если проблема связана с тем, что результаты загружены, но launch или test cases ведут себя странно, открой [references/launch-lifecycle-and-troubleshooting.md](references/launch-lifecycle-and-troubleshooting.md).
7. Если задача связана с defect workflow, сначала открой [references/api-auth-and-usage.md](references/api-auth-and-usage.md) и используй Swagger для подтверждения схем `DefectCreateDto`, `DefectPatchDto` и related issue endpoints текущего инстанса.
8. Перед изменением test case сначала получай текущий объект, а для операций со статусом дополнительно workflow и список допустимых статусов.
9. Для raw upload flow не придумывай hand-rolled API integration, если пользователь явно не требует этого; по умолчанию используй `allurectl`.

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
- Для defect operations сначала выясняй, есть ли у проекта настроенные `issue schema` и внешняя issue integration; без этого не обещай создание внешнего issue.
- Перед изменением статуса test case сначала получай `workflow` кейса и допустимые статусы этого workflow.
- Для create/update test case не допускай пустых `description`, `precondition`, `scenario` и `expectedResult`.
- Для каждого шага manual scenario обеспечивай expected result этого шага.
- Пока launch открыт, не считай ingestion завершённым и не делай выводы по финальной статистике.
- Если test case уже привязан к другому project, не ожидай, что upload в новый project автоматически создаст новый кейс.
- Перед patch test case по умолчанию сначала читай текущий объект и меняй только те поля, которые пользователь явно запросил изменить.
- Для create defect по умолчанию заполняй `name`, `description`, `projectId` и `matcher`, если пользователь просит максимально полную запись.
- Для link endpoint-ов, которые могут вернуть пустое тело, не полагайся на stdout; проверяй результат повторным `GET`.

## Минимальный auth flow для API

Сгенерируй Bearer JWT из пользовательского API token:

```bash
scripts/allure_testops_api.sh auth
```

Вызови API path с полученным JWT:

```bash
scripts/allure_testops_api.sh GET /api/rs/project '?page=0&size=10'
scripts/allure_testops_api.sh GET /api/rs/testcase '?projectId=3&page=0&size=10'
scripts/allure_testops_api.sh GET /api/defect '?projectId=3&page=0&size=10'
scripts/allure_testops_api.sh GET /api/issueschema '?projectId=3&page=0&size=10'
scripts/allure_testops_api.sh defect-list 3
scripts/allure_testops_api.sh defect-get 7
scripts/allure_testops_api.sh defect-close 7
scripts/allure_testops_api.sh defect-reopen 7
scripts/allure_testops_api.sh defect-verify 7
scripts/allure_testops_api.sh defect-matcher-list 7
scripts/allure_testops_api.sh issueschema-list 3
scripts/allure_testops_api.sh testcase-defect-list 1860
scripts/allure_testops_api.sh testcase-unlink-defect 1860 7
scripts/allure_testops_api.sh defect-create-template /tmp/defect.json
scripts/allure_testops_api.sh defect-clone 7 /tmp/defect-copy.json
scripts/allure_testops_api.sh testcase-get 1811
scripts/allure_testops_api.sh testcase-overview-get 1811
scripts/allure_testops_api.sh testcase-workflow 1811
scripts/allure_testops_api.sh testcase-set-status 1811 -2 -1
scripts/allure_testops_api.sh testcase-scenario-get 1811
scripts/allure_testops_api.sh testcase-step-tree 1811
scripts/allure_testops_api.sh testcase-sync-scenario 1811 /tmp/scenario.json
scripts/allure_testops_api.sh testcase-set-step-expected-result 1811 0 "Ожидаемый результат первого шага"
```

## Практический workflow для defect

Для работы с дефектами используй такой порядок:

1. Найди проект и проверь, есть ли уже дефекты:

```bash
scripts/allure_testops_api.sh defect-list 3
```

2. Если нужен внешний issue workflow, сначала проверь issue schema проекта:

```bash
scripts/allure_testops_api.sh issueschema-list 3
```

3. Если issue schema пустой, создавай и веди defect только внутри Allure TestOps и не пытайся вызывать `createissue`.

4. Для максимально заполненного defect payload используй:
   - `projectId`
   - `name`
   - `description`
   - `matcher.name`
   - `matcher.messageRegex`
   - `matcher.traceRegex`

5. После create defect отдельно проверь:
   - сам объект дефекта;
   - matcher-ы дефекта;
   - связь с test case, если ты её создавал.

6. Если привязываешь defect к test case через `POST /api/testcase/{testCaseId}/defect/{defectId}`, учитывай, что endpoint может вернуть пустое тело при `200 OK`; подтверждай связь повторным `GET /api/testcase/{id}/defect`.

Предпочтительные shortcut-команды helper script для defect workflow:

```bash
scripts/allure_testops_api.sh defect-list 3
scripts/allure_testops_api.sh defect-get 7
scripts/allure_testops_api.sh defect-create /tmp/defect.json
scripts/allure_testops_api.sh defect-patch 7 /tmp/defect-patch.json
scripts/allure_testops_api.sh defect-close 7
scripts/allure_testops_api.sh defect-reopen 7
scripts/allure_testops_api.sh defect-verify 7
scripts/allure_testops_api.sh defect-matcher-list 7
scripts/allure_testops_api.sh defect-create-template /tmp/defect.json
scripts/allure_testops_api.sh defect-clone 7 /tmp/defect-copy.json
scripts/allure_testops_api.sh testcase-link-defect 1860 7
scripts/allure_testops_api.sh testcase-defect-list 1860
scripts/allure_testops_api.sh testcase-unlink-defect 1860 7
```
