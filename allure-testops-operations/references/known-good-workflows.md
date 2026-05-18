# Allure TestOps Known-Good Workflows

Короткий индекс для типовых задач. Детали endpoint-ов и payloads см. в `api-auth-and-usage.md`, upload/watch - в `allurectl-workflows.md`, ingestion - в `launch-lifecycle-and-troubleshooting.md`.

## Auth And Project Discovery

```bash
scripts/allure_testops_api.sh auth
scripts/allure_testops_api.sh GET /api/rs/project '?page=0&size=10'
```

Правило: долгоживущий API token сначала обменивай на короткоживущий JWT.

## Defect Create Or Update

```bash
scripts/allure_testops_api.sh defect-list 3
scripts/allure_testops_api.sh issueschema-list 3
scripts/allure_testops_api.sh defect-create-template /tmp/defect.json
scripts/allure_testops_api.sh defect-create /tmp/defect.json
scripts/allure_testops_api.sh defect-get 7
scripts/allure_testops_api.sh defect-matcher-list 7
```

Если issue schema пустой, веди defect внутри Allure TestOps и не обещай external issue workflow.

## Link Defect To Test Case

```bash
scripts/allure_testops_api.sh testcase-link-defect 1860 7
scripts/allure_testops_api.sh testcase-defect-list 1860
scripts/allure_testops_api.sh testcase-unlink-defect 1860 7
```

Link endpoint может вернуть пустое тело; подтверждай связь повторным `GET`/helper list.

## Manual Scenario Update

```bash
scripts/allure_testops_api.sh testcase-get 1811
scripts/allure_testops_api.sh testcase-scenario-get 1811
scripts/allure_testops_api.sh testcase-step-tree 1811
scripts/allure_testops_api.sh testcase-sync-scenario 1811 /tmp/scenario.json
scripts/allure_testops_api.sh testcase-set-step-expected-result 1811 0 "Ожидаемый результат"
```

Правило: у каждого шага должен быть expected result; после записи UI-модели перепроверяй low-level step tree.

## Launch Ingestion Verification

- Пока launch открыт, не считай ingestion финальным.
- Проверь project binding, upload/watch output и состояние launch после завершения.
- Если статистика или testcase links выглядят странно, см. `launch-lifecycle-and-troubleshooting.md`.
