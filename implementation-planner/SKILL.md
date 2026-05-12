---
name: implementation-planner
description: "Использовать перед multi-step реализацией, когда нужен исполнимый engineering plan: точные файлы, маленькие шаги, команды проверки и expected output."
---

# Implementation Planner

Используй этот skill, когда пользователь просит план реализации или когда перед кодом нужен отдельный engineering execution plan. Это не delivery roadmap и не продуктовый backlog: план должен быть пригоден для выполнения агентом или разработчиком без повторного дизайна.

## Workflow

1. Зафиксируй цель и границы:
   - что должно быть построено;
   - что не входит в scope;
   - какие acceptance criteria подтверждают завершение.
2. Изучи существующую структуру проекта и patterns.
3. Составь file map:
   - какие файлы создать;
   - какие файлы изменить;
   - какие тесты добавить или обновить;
   - какие shared contracts затрагиваются.
4. Разбей работу на маленькие tasks, каждая дает проверяемый результат.
5. Для каждого task укажи:
   - exact paths;
   - конкретное изменение;
   - test-first шаг, если применимо;
   - command для проверки;
   - expected output или критерий pass/fail.
6. Для внешних API/framework decisions добавь source gate: где взять версию и official docs, либо явно пометь unknown.
7. Для high-risk или irreversible шага добавь doubt gate: какой claim нужно проверить до изменения.
8. Проверь план на placeholders и несогласованность names/types.
9. Укажи подход выполнения: inline, batch checkpoints или `subagent-driven-development`.

## Правила качества плана

- Каждый task должен быть self-contained.
- Шаги должны быть маленькими: один action на шаг.
- Указывай реальные file paths, а не "где-то в модуле".
- Для code steps показывай достаточно конкретики, чтобы не осталось "придумай сам".
- Команды проверки пиши в исполнимом виде.
- Expected output должен быть проверяемым.
- Не добавляй архитектурный redesign, если задача требует локального изменения.
- Не планируй TODO/placeholders.
- План должен идти маленькими slices: после каждого рискованного slice есть локальная проверка.
- Не принимай внешние API и framework behavior на память: добавляй `source-driven-development`.
- Если шаг содержит миграцию, удаление данных, security-sensitive изменение или дорогой rollback, добавляй `doubt-driven-development`.

## Запрещенные placeholders

Не пиши:

- `TODO`;
- `TBD`;
- "добавить обработку ошибок";
- "написать тесты";
- "и так далее";
- "аналогично предыдущему";
- "реализовать бизнес-логику";
- "проверить edge cases";
- любые шаги без конкретного файла, действия и verification.

Если деталь неизвестна, сначала исследуй ее или явно вынеси как open question, а не маскируй placeholder.

## Какие references открывать

- Шаблон implementation plan:
  [references/plan-template.md](references/plan-template.md)

## Связь с другими skills

- Для продуктового выбора используй `product-manager`.
- Для delivery/release coordination используй `delivery-manager`.
- Для архитектурного решения с trade-offs используй `solution-architect`.
- Для выполнения плана через агентов используй `subagent-driven-development`.
- Для решений по внешним API/framework/library используй `source-driven-development`.
- Для рискованных claims и irreversible изменений используй `doubt-driven-development`.
- Перед claim о завершении используй `verification-before-completion`.

## Формат ответа

Когда возвращаешь план, включай:

1. Goal и non-goals.
2. File map.
3. Tasks со step checklist.
4. Verification commands и expected output.
5. Open questions или risks.
6. Recommended execution mode.
