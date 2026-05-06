---
name: receiving-code-review
description: "Использовать при получении code review feedback, requested changes, inline comments или внешних рекомендаций перед исправлениями, особенно если feedback неясен или спорен."
---

# Receiving Code Review

Используй этот skill, когда нужно обработать ревью-комментарии от пользователя, GitHub/GitLab reviewer, subagent reviewer или внешнего инструмента. Цель: технически проверить feedback, исправить корректное и аргументированно оспорить некорректное.

## Workflow

1. Прочитай весь feedback до действий.
2. Раздели comments на:
   - blocking/critical;
   - important;
   - minor;
   - unclear;
   - likely incorrect.
3. Для каждого item пойми требование:
   - что именно предлагают изменить;
   - какой риск или баг пытаются закрыть;
   - какие файлы и behavior затрагиваются.
4. Проверь feedback по codebase:
   - есть ли usage;
   - ломает ли suggestion совместимость;
   - есть ли существующий тест/контракт;
   - не конфликтует ли с решениями пользователя.
5. Если item неясен, остановись и задай уточнение до partial implementation.
6. Исправляй по одному item или логическим batch'ам, проверяя каждый batch.
7. Перед ответом используй `verification-before-completion`.

## Как реагировать

- Корректный feedback: исправь и кратко укажи, что изменено.
- Некорректный feedback: дай technical pushback с ссылкой на код, тест или контракт.
- Непроверяемый feedback: скажи, чего не хватает для проверки, и предложи следующий шаг.
- Feedback от пользователя: доверяй intent, но уточняй scope, если он неясен.
- Feedback от внешнего reviewer/tool: проверяй особенно внимательно, не внедряй слепо.

## Запрещено

- Соглашаться performative-фразами до проверки.
- Внедрять непонятные items частично, оставляя unclear items "на потом".
- Добавлять "professional" features без подтвержденного usage.
- Игнорировать critical/important findings без объяснения.
- Отвечать top-level comment, если нужен reply в конкретный inline thread.

## GitHub/GitLab threads

- Для inline review comments отвечай в конкретный thread, если инструмент это поддерживает.
- Не смешивай независимые review threads в один общий ответ, если reviewer ожидает thread-level resolution.
- Если feedback уже resolved/stale, проверь актуальный diff перед исправлением.

## Какие references открывать

- Шаблон triage и ответа:
  [references/feedback-triage.md](references/feedback-triage.md)

## Формат ответа

Когда работаешь с review feedback, возвращай:

1. Что принято к исправлению.
2. Что неясно и требует уточнения.
3. Что отклонено с технической причиной.
4. Какие изменения сделаны.
5. Какие проверки выполнены и что осталось непроверенным.
