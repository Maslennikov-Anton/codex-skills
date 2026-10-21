# Вход для анализа

`analyze` принимает JSONL, одна строка на попытку теста:

```json
{"run_id":"pipeline42-job7-rerun0","run_order":42,"run_complete":true,"result_id":"uuid","test_id":"as_id:820","variant":"parameters-digest","attempt":0,"status":"failed","expected_status":"passed","duration_ms":1200,"revision":"test-git-sha","artifacts":{"vcstudio":"artifact-digest","vcont":"artifact-digest"},"environment":{"runner_profile":"linux-x11-4cpu","config":"profile-digest"}}
```

- `run_id` уникален для отдельного исполнения job/pipeline; test retry остается внутри него. `run_order` задает хронологию запуска, не UUID.
- `test_id` стабилен; `variant` различает параметры, включая режимы работы. Не объединяй параметризованные тесты только по `as_id`.
- `attempt`: 0, 1, … для доказанных test retries; `null`, если порядок неизвестен. Нужна непрерывная последовательность с 0. Дубли номеров и неизвестный порядок дают incomplete.
- `run_complete` — подтверждение, что это завершенное исполнение и экспорт содержит все попытки этого теста. Оно не доказывает, что весь test plan выполнен. Для прерванного/частичного экспорта ставь false.
- Поддержаны статусы passed/failed/broken/skipped/unknown. Неожидаемое skipped/unknown исключает usable-run; ожидаемые неположительные случаи тоже не входят в reliability positive-кейсов. Не меняй тестовые статусы для подготовки данных.
- `duration_ms` неотрицательно или null; неточные/отрицательные значения не заменяются нулем.
- `revision`, `artifacts`, `environment` обязательны. Явное `unknown`/`unavailable`/`n/a` изолирует run от cross-run анализа. Неполные поля не подменяй фиктивным известным значением.
- Повтор одной и той же строки дедуплицируется по run_id/result_id. Противоречащий дубль — ошибка входа. Metadata одного run должно совпадать.

## Адаптер локального Allure

Manifest JSON (пути results_dir относительны manifest либо абсолютны):

```json
{
  "schema_version": 1,
  "runs": [{
    "id": "pipeline42-job7-rerun0", "order": 42, "complete": true,
    "revision": "test-sha", "artifacts": {"vcstudio": "sha256:..."},
    "environment": {"runner_profile": "linux-x11-4cpu", "config": "digest"},
    "results_dir": "allure-results/run42",
    "attempts": {"failed-uuid": 0, "passed-uuid": 1}
  }]
}
```

Если retries точно отключены, вместо attempts укажи `"no_test_retries": true`. Без этих данных номера остаются null: timestamps могут пересекаться, а raw Allure file не гарантирует номер retry. При merge artifacts разных jobs сохрани отдельные run IDs. Если параллельные результаты одного теста являются независимыми исполнениями, не нумеруй их как retry.

Identity: Allure label AS_ID/as_id → testCaseId → fullName. Variant — hash historyId и не-excluded параметров. Значения параметров не печатаются, но даже hashed metadata может быть чувствительным; сохраняй reports локально. Поддерживаются стандартные `*-result.json`, не произвольный TestOps API JSON. Для API нужен отдельный нормализатор по фактической версии endpoint; здесь он не подразумевается.

Адаптер не читает attachments, statusDetails/stack traces и токены. Для expected non-positive outcomes можно явно передать `expected_status_by_uuid`; флаг statusDetails.known/muted не превращает failed positive test в pass.

Проверь denominator по выбранному test plan: отсутствующий тест не создает строку и не обнаруживается скриптом. Incomplete группы не входят в claim о стабильности. Cross-run variability — кандидат для debugging: смена test data или неучтенная среда тоже меняют результат.

Формат полей сверялся с [Allure result file](https://allurereport.org/docs/how-it-works-test-result-file/); это локальный export adapter, не проверка server ingestion.
