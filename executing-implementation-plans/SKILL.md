---
name: executing-implementation-plans
description: "Использовать, когда есть written implementation plan и его нужно выполнить task-by-task с checkpoints, verification commands и остановкой на blockers."
---

# Executing Implementation Plans

Используй этот skill для выполнения уже написанного implementation plan. Если плана нет, сначала используй `implementation-planner`; если есть только мелкие gaps, восполни их из локального evidence и продолжай.

## Workflow

1. Прочитай план полностью.
2. Проведи critical review до кода:
   - есть ли exact files;
   - понятны ли tasks;
   - есть ли verification commands;
   - нет ли contradictions, placeholders или missing dependencies.
3. Закрой gaps по repo evidence в пределах согласованной задачи. Уточнение требуется, если недостающий выбор меняет поведение, scope или разрешения.
4. Создай рабочий checklist по tasks.
5. Выполняй task-by-task:
   - отметь task in progress;
   - следуй steps в плане;
   - не расширяй scope;
   - держи изменение маленьким завершенным slice;
   - запускай verification, указанную в task; достаточный свежий результат можно использовать повторно, пока относящиеся к нему код, зависимости, окружение и claim не изменились;
   - фиксируй result;
   - переходи дальше только после pass или явного решения по blocker.
6. После естественного checkpoint или завершения:
   - проверь общий diff;
   - проверь покрытие final claim уже собранным evidence; повтори только устаревшие или недостающие проверки;
   - используй `verification-before-completion` перед claim о завершении.

## Когда использовать subagents

Если план содержит независимые tasks и пользователь разрешил subagents, используй `subagent-driven-development` для выполнения параллельных частей. Этот skill остается coordination layer: план должен быть прочитан, раскритикован и проверен после интеграции.

## Stop Conditions

Остановись и спроси только если gap нельзя безопасно закрыть по локальному evidence:

- task unclear enough to change behavior or scope;
- план содержит TODO/TBD/placeholders в critical path;
- verification command отсутствует для risky task and no equivalent local gate is obvious;
- risky step не имеет source/doubt gate, хотя зависит от внешнего API, миграции, security или irreversible action;
- выполнение требует изменения scope;
- два tasks конфликтуют по ownership/files.

Отсутствующая dependency или падение test/build сначала требуют диагностики. Исправляй причину и повторяй затронутую проверку в рамках уже разрешенной задачи. Спрашивай, если решение требует новых прав, внешнего необратимого действия или существенного расширения scope; при недоступном внешнем сервисе сохрани evidence и продолжай независимые tasks.

## Что не делать

- Не исполняй план на blind trust, если он противоречит codebase.
- Не переписывай план молча, если меняется architecture или scope.
- Не пропускай verification steps.
- Не превращай большой план в один большой diff без промежуточных проверок.
- Не объявляй task complete по факту изменения файлов без проверки.
- Не продолжай после repeated failure без root cause или уточнения.

## Какие references открывать

- Execution checklist:
  [references/execution-checklist.md](references/execution-checklist.md)

## Формат ответа

При выполнении плана возвращай:

1. Какой plan исполнялся.
2. Какие tasks выполнены.
3. Какие verification commands запускались и результат.
4. Какие blockers или изменения scope возникли.
5. Что осталось сделать.
