# Test Project Contract

Используй этот reference, когда тестовый репозиторий сам является поддерживаемым инженерным продуктом.

## Что должно быть согласовано

- coverage matrix по endpoint-ам, user stories или ключевым сценариям;
- список known bugs или другой bug artifact для `xfail`/ожидаемых ограничений;
- `README`, `.env.example`, runtime defaults и CI jobs;
- ignore-правила для generated artifacts.

## Правила поддержки

- Разделяй статусы `covered`, `covered with known bug`, `uncovered`.
- Не храни `allure-results`, временные отчеты, `junit`, `*.egg-info`, локальные кэши и похожие generated-файлы в git.
- Для подтвержденных дефектов допускается `xfail`, но только с конкретным `reason` и воспроизводимым багом.
- Перед массовым изменением тестов сначала собери evidence: фактические ответы, состояние данных и воспроизводимый сценарий.
