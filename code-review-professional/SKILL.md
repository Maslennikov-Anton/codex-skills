---
name: code-review-professional
description: Ревьюить изменения в коде с фокусом на баги, регрессии, архитектурные риски, тестовые пробелы и лишнюю сложность.
---

# Профессиональное ревью кода

Используй этот skill для инженерного review после реализации, когда нужно искать проблемы, а не пересказывать diff.

## Workflow

1. Пойми контекст изменения и затронутые области.
2. Если review запрашивается как отдельный pass, собери review contract:
   - что реализовано;
   - план или требования;
   - base/head SHA или список changed files;
   - какие проверки уже запускались.
3. Оцени риск: низкий, средний или высокий.
4. Проверь:
   - корректность логики;
   - читаемость и простоту решения;
   - архитектурные границы и совместимость контрактов;
   - security implications;
   - performance implications;
   - граничные случаи и обработку ошибок;
   - регрессии и обратную совместимость;
   - достаточность тестов и проверок.
5. Сформируй findings по приоритету и остаточные риски.

## Главный фокус

- баги;
- поведенческие регрессии;
- архитектурные и интеграционные риски;
- недостаточное тестовое покрытие;
- скрытая избыточная сложность;
- нарушение локальных стандартов.

## Five-axis review

Проверяй каждое значимое изменение по пяти осям:

1. Correctness: поведение, edge cases, error paths, regression risk.
2. Simplicity/readability: лишняя сложность, naming, локальные conventions.
3. Architecture: границы модулей, contracts, coupling, migration path.
4. Security: auth/authz, secrets, injection, unsafe defaults, data exposure.
5. Performance: unnecessary work, queries, memory, latency, scalability cliffs.

## Какие references открывать

- Общий инженерный checklist ревью:
  [references/review-checklists.md](references/review-checklists.md)
- Дополнительные проверки для тестовых проектов:
  [references/test-project-review.md](references/test-project-review.md)

## Правила качества ревью

- Findings всегда важнее summary.
- Начинай с проблем, а не с похвалы.
- Привязывай замечания к файлам и строкам, если это возможно.
- Разделяй факты, выводы и предположения.
- Если проблем не найдено или ревью ограничено окружением, явно это отмечай.
- Не принимай “small diff” как low risk без проверки behavior surface.
- Не доверяй session history вместо review contract: review должен опираться на diff, файлы, требования и проверки.
- Для Critical findings блокируй продолжение до исправления или явного решения пользователя.
- Important findings исправляй до merge/финального claim либо явно фиксируй как accepted risk.
- Minor findings можно отметить как follow-up, если они не меняют correctness.

## Severity

- Critical: correctness/security/data-loss/regression issue, который блокирует merge/release или может сломать production/пользовательский critical path.
- Important: реальный баг, риск регрессии, несовместимость контракта, существенный test gap или operational risk, который нужно исправить до финального claim.
- Minor: readability, maintainability, локальная cleanup-правка или low-risk edge case, который не меняет correctness и может быть follow-up.

Не повышай severity из-за стиля, если нет behavioral или operational риска; не понижай severity из-за маленького diff.

## Формат ответа

Когда просят сделать ревью, отвечай так:

1. Findings по приоритету.
2. Открытые вопросы и допущения.
3. Краткий summary изменений.
4. Какие проверки были выполнены и чего не хватило.

## Связь с другими skills

Если ревью-комментарии уже получены и их нужно обработать, используй `receiving-code-review`.

Если review выполняет subagent, prompt должен содержать review contract: implementation summary, plan/requirements, base/head SHA или changed files, expected output и severity format.

Если review упирается в спорный high-risk claim, используй `doubt-driven-development`.
