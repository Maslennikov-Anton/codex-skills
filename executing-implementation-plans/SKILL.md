---
name: executing-implementation-plans
description: "Использовать, когда есть written implementation plan и его нужно выполнить task-by-task с checkpoints, verification commands и остановкой на blockers."
---

# Executing Implementation Plans

Используй этот skill для выполнения уже написанного implementation plan. Если плана нет или он слишком расплывчатый, сначала используй `implementation-planner`.

## Workflow

1. Прочитай план полностью.
2. Проведи critical review до кода:
   - есть ли exact files;
   - понятны ли tasks;
   - есть ли verification commands;
   - нет ли contradictions, placeholders или missing dependencies.
3. Если есть critical gaps, остановись и уточни план вместо угадывания.
4. Создай рабочий checklist по tasks.
5. Выполняй task-by-task:
   - отметь task in progress;
   - следуй steps в плане;
   - не расширяй scope;
   - запускай verification, указанную в task;
   - фиксируй result;
   - переходи дальше только после pass или явного решения по blocker.
6. После естественного checkpoint или завершения:
   - проверь общий diff;
   - выполни final verification;
   - используй `verification-before-completion` перед claim о завершении.

## Когда использовать subagents

Если план содержит независимые tasks и пользователь разрешил subagents, используй `subagent-driven-development` для выполнения параллельных частей. Этот skill остается coordination layer: план должен быть прочитан, раскритикован и проверен после интеграции.

## Stop Conditions

Остановись и спроси, если:

- task unclear;
- план содержит TODO/TBD/placeholders;
- verification command отсутствует для risky task;
- dependency не установлена или недоступна;
- test/build fails не из-за ожидаемого red step;
- выполнение требует изменения scope;
- два tasks конфликтуют по ownership/files.

## Что не делать

- Не исполняй план на blind trust, если он противоречит codebase.
- Не переписывай план молча, если меняется architecture или scope.
- Не пропускай verification steps.
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
