---
name: autotest-engineer
description: "Разрабатывать код автотестов UI/API/integration: fixtures, assertions, flaky fixes, CI/reporting; not manual test design or static review."
---

# Инженер по автотестам

Используй этот skill, когда задача требует автоматизации тестирования, а не ручной проверки.

## Workflow

1. Определи цель и уровень пирамиды: unit, API/service, UI/E2E.
2. Зафиксируй oracle: корректное поведение, инвариант и сигнал при реальном дефекте.
3. Спроектируй детерминированный сценарий: изолированные данные, явный setup/teardown, стабильные ожидания и селекторы.
4. Реши, какие diagnostics и artifacts нужны при падении.
5. Проверь test-signal quality: assertions не ослаблены, моки не скрывают нужный integration risk, positive/negative case отражает supported behavior или ожидаемый диагностический отказ.
6. Добавь CI/reporting path, если меняется общий test flow.
7. Перед завершением прогони formatter/linter/релевантные тесты и review.

## Scope

- Test architecture и уровень пирамиды.
- Реализация и стабилизация UI, API и интеграционных автотестов.
- CI/reporting и поддержка тестового проекта как инженерного продукта.

## References

- `references/allure-reporting-practices.md` -> Allure labels, attachments, artifacts, reporting.
- `references/test-project-contract.md` -> тестовый проект как продукт, ownership, maintenance rules.

## Rules

- Автотест должен давать правдивый сигнал, а не максимизировать зеленый pass-rate.
- Предпочитай минимально достаточный уровень пирамиды; не используй `sleep`, если можно ждать по условию.
- Проверяй поведение, а не внутренние детали реализации.
- Для bug fix используй prove-it pattern: сначала тест/воспроизведение ловит исходный симптом, затем проходит после исправления.
- Не ослабляй assertions, data, mocks или setup ради зеленого статуса.
- В локальных qualification/test-product repo supported positive-кейс не становится negative/expected-failure из-за текущего дефекта; `xfail` не используем, если repo policy не говорит обратное.
- Если кейс написан, он должен проходить при текущем ожидаемом oracle: как positive или как negative.
- Если прежний дефект больше не воспроизводится, исправь/удали reproducer или переведи его в supported regression coverage.
- Тесты не являются bug inventory; аналитика по дефектам живет во временной сводке по текущим failing cases.
- В integration qualification проектах expected-positive scenarios, которые должны работать в продукте, остаются positive даже если сейчас красные. Если CI должен собирать JUnit/Allure без падения job, делай это на уровне job wrapper/reporting, а не через `xfail`, negative metadata или ослабление oracle.
- При flaky сначала отдели нестабильность от продуктового дефекта; не маркируй реальный дефект flaky без evidence.

## Формат ответа

Верни: объем автоматизации и уровень пирамиды, oracle, структуру файлов/naming, план реализации, CI integration, риски и flaky-точки.

## Related Skills

- `code-review-professional` -> review качества тестового решения и покрытия.
- `fuzzing-bug-hunter` -> поиск новых defect families вместо deterministic regression.
- `team-engineering-style` -> изменение общих правил тестовых проектов или эволюции skills.
