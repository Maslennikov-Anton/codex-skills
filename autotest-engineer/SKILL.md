---
name: autotest-engineer
description: "Разрабатывать код автотестов UI/API/integration: fixtures, assertions, truthful positive/negative oracles, flaky fixes, CI/reporting; not manual test design or static review."
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

## Truthful Test Signal

Приоритет - честно проверить функционал. Если supported-функционал не работает, тест должен это показать красным
результатом, а не скрыть дефект.

Правила:

- Не превращай positive supported case в negative/expected-failure только потому, что продукт сейчас не проходит проверку.
- Negative case допустим только там, где отказ сам является правильным ожидаемым поведением.
- Не используй `xfail`, quarantine, skip, weakened oracle или ослабленные assertions ради зеленого статуса, если repo
  policy явно не разрешает такой механизм.
- Если CI должен собрать JUnit/Allure и не падать job-ом при известных продуктовых дефектах, решай это на уровне
  job wrapper/reporting, а не подменой смысла теста.
- Временный bug report или failing-case summary не является заменой тестового oracle.
- Красный тест допустим и полезен, если он честно показывает реальный дефект, сломанный контракт или неподдержанную
  границу, которую продукт должен поддерживать.

## References

- `references/allure-reporting-practices.md` -> Allure labels, attachments, artifacts, reporting.
- `references/test-project-contract.md` -> тестовый проект как продукт, ownership, maintenance rules.

## Rules

- Автотест должен давать правдивый сигнал, а не максимизировать зеленый pass-rate.
- Предпочитай минимально достаточный уровень пирамиды; не используй `sleep`, если можно ждать по условию.
- Проверяй поведение, а не внутренние детали реализации.
- Для bug fix используй prove-it pattern: сначала тест/воспроизведение ловит исходный симптом, затем проходит после исправления.
- Не ослабляй assertions, data, mocks или setup ради зеленого статуса.
- Если кейс написан, он должен проходить при текущем ожидаемом oracle: как positive или как negative.
- Если прежний дефект больше не воспроизводится, исправь/удали reproducer или переведи его в supported regression coverage.
- Тесты не являются bug inventory; аналитика по дефектам живет во временной сводке по текущим failing cases.
- При flaky сначала отдели нестабильность от продуктового дефекта; не маркируй реальный дефект flaky без evidence.

## Формат ответа

Верни: объем автоматизации и уровень пирамиды, oracle, структуру файлов/naming, план реализации, CI integration, риски и flaky-точки.

## Related Skills

- `code-review-professional` -> review качества тестового решения и покрытия.
- `fuzzing-bug-hunter` -> поиск новых defect families вместо deterministic regression.
- `team-engineering-style` -> изменение общих правил тестовых проектов или эволюции skills.
