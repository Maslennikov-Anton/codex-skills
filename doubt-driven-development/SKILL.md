---
name: doubt-driven-development
description: "Проверять high-risk решения свежим скептическим pass: claims, assumptions, irreversible changes, security, unfamiliar code и дорогие ошибки."
---

# Doubt-Driven Development

Используй этот skill, когда уверенный вывод может дорого стоить: production/security, irreversible операции, миграции, незнакомая область, сложная архитектура, спорное review feedback или repeated failures.

## Workflow

1. Сформулируй claim:
   - что именно считаешь истинным;
   - на чем основан вывод;
   - что сломается, если claim неверен.
2. Выдели smallest reviewable artifact:
   - diff, plan step, schema change, contract, query, config или reproduction.
3. Проведи doubt pass:
   - проверь альтернативные объяснения;
   - ищи missing preconditions, boundary cases, version mismatch, rollback gaps;
   - при разрешенных subagents можно дать artifact независимому reviewer'у с read-only scope.
4. Reconcile:
   - valid findings исправь или преврати в explicit risk;
   - invalid findings отклони с evidence;
   - если uncertainty сохраняется, уменьши scope или добавь verification.
5. Останови цикл после одного-двух passes, чтобы не уходить в бесконечный review.

## Red Flags

- “Я уверен” заменяет evidence.
- Решение не имеет rollback или recovery path.
- Risky change идет без маленького artifact для проверки.
- Review disagreement закрывается авторитетом, а не аргументом.
- Миграция, security control или data deletion проверены только мысленно.

## Связь с другими skills

- Для review готового diff используй `code-review-professional`.
- Для внешних API и framework behavior используй `source-driven-development`.
- Для доказательства исправления используй `verification-before-completion`.

## Формат ответа

Когда doubt pass влияет на решение, возвращай:

1. Claim.
2. Artifact или границу проверки.
3. Найденные сомнения и решение по ним.
4. Остаточный риск и verification.
