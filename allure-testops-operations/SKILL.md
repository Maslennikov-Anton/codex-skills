---
name: allure-testops-operations
description: >
  Работать с Allure TestOps: auth, проекты, test cases, defects, launches,
  jobs, upload результатов и диагностика через allurectl, HTTP API, shell или CI.
---

# Allure TestOps Operations

Используй этот skill для задач по Allure TestOps как продукту, а не только по одному endpoint. Предпочтительный путь: `allurectl` для upload/watch и lifecycle flows, HTTP API для discovery/object operations, hand-rolled automation только когда официальный или helper path не подходит.

## Defaults

- Локальный файл секретов: `/home/ant/.allure-testops.env`.
- Ожидаемые переменные: `ALLURE_TESTOPS_URL`, `ALLURE_TESTOPS_TOKEN`.
- Не печатай token в ответах.

## Workflow

1. Определи тип задачи: upload/watch, API object operations, defects/issues, discovery, launch/job troubleshooting или CI integration.
2. Проверь env vars или файл секретов.
3. Открой только нужный reference:
   - `references/known-good-workflows.md` -> короткий индекс auth/project discovery, defects, testcase links, manual scenario и launch ingestion.
   - `references/allurectl-workflows.md` -> upload/watch, launch lifecycle в CI, `allurectl`.
   - `references/api-auth-and-usage.md` -> auth, Swagger discovery, test cases, defects, scenario operations, known-good helper workflows.
   - `references/scenario-models.md` -> manual scenario, UI/low-level step model.
   - `references/launch-lifecycle-and-troubleshooting.md` -> ingestion, project binding, странная статистика launch/test cases.
4. Для discovery endpoint-ов предпочитай Swagger UI целевого инстанса: `<base-url>/swagger-ui.html`.
5. Перед изменением test case получай текущий объект; перед сменой статуса дополнительно получай workflow и допустимые статусы.
6. Для defect workflow сначала проверь issue schema и внешнюю issue integration проекта. Без schema не обещай создание внешнего issue.
7. Для raw upload flow не придумывай API-интеграцию, если пользователь явно не попросил; по умолчанию используй `allurectl`.

## Правила

- Для API-вызовов обменивай долгоживущий API token на короткоживущий JWT.
- Подтверждай форму запросов и обязательные параметры через Swagger текущего инстанса.
- Для create/update test case не допускай пустых `description`, `precondition`, `scenario`, `expectedResult`; у каждого шага manual scenario должен быть expected result.
- Пока launch открыт, не считай ingestion завершенным и не делай выводы по финальной статистике.
- Если test case уже привязан к другому project, не ожидай, что upload в новый project автоматически создаст новый кейс.
- Для PATCH сначала читай текущий объект и меняй только поля, которые пользователь просил изменить.
- Для defect по умолчанию заполняй `projectId`, `name`, `description` и matcher, если нужна полноценная запись.
- Link endpoint-ы могут вернуть пустое тело; подтверждай результат повторным `GET`.

## Helper

Для повторяемых API-вызовов используй bundled script вместо ручной сборки `curl`:

```bash
scripts/allure_testops_api.sh auth
scripts/allure_testops_api.sh GET /api/rs/project '?page=0&size=10'
scripts/allure_testops_api.sh defect-list 3
scripts/allure_testops_api.sh testcase-get 1811
```

Полный набор команд и payload patterns см. в `references/api-auth-and-usage.md`.
