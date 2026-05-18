---
name: subagent-driven-development
description: "Использовать, когда пользователь разрешил subagents, parallel agents, delegation или agent workflow, и задача содержит независимые subtasks для крупной реализации."
---

# Subagent-Driven Development

Используй этот skill только когда пользователь или более высокий уровень инструкций явно разрешили subagents/delegation для текущей задачи. Цель - ускорить независимые части работы без потери контроля, ownership и проверяемости.

## Gate

Запускай subagents только если одновременно верно:

- разрешение на subagents действует в текущей сессии;
- задача выигрывает от параллельной или делегированной работы;
- есть независимые subtasks с disjoint ownership;
- основной агент не блокируется на делегированном immediate next step;
- результат можно проверить локально перед финальным ответом.

## Workflow

1. Выдели critical path: что делает основной агент сейчас, что можно делегировать, что требует тесной координации.
2. Для каждого subtask задай: цель, входной контекст, expected output, ownership, запрет откатывать чужие изменения, проверки.
3. Делегируй только bounded work:
   - `explorer` -> узкий вопрос по codebase;
   - `worker` -> disjoint code changes;
   - review -> готовый diff или artifact.
4. Пока subagents работают, делай non-overlapping работу локально.
5. После результата проверь evidence/changed files, интегрируй только прошедшее review и закрой thread, если он больше не нужен.
6. Перед финальным ответом проверь общий diff и релевантную verification.

## Review Gates

- Spec compliance: scope, ownership, acceptance criteria, отсутствие лишней функциональности.
- Code quality: local patterns, regressions, тесты по риску, конфликты с параллельными изменениями.

Critical и Important issues исправляй до продолжения; Minor можно оставить follow-up, если correctness не страдает.

## Что делегировать

- Независимый поиск по codebase.
- Bounded реализацию в отдельных файлах/модулях.
- Параллельную проверку гипотез.
- Подготовку тестов отдельного слоя.
- Review уже готового diff.

## Что не делегировать

- Immediate blocking step.
- Архитектурную развилку без решения владельца.
- Изменения в live/external systems без явного разрешения.
- Разрушительные git/file операции.
- Tasks с пересекающимся write ownership.

## Prompt Contract

Каждый worker prompt должен содержать: что сделать, ownership, что не трогать, какие параллельные изменения возможны, какие проверки запустить и что вернуть: summary, changed paths, tests, risks. Для сложных задач см. `references/prompt-contracts.md`.

## Формат ответа

Когда используешь subagents, верни: что делегировано, ownership, что сделал основной агент, какие результаты приняты/изменены/отклонены и какая verification выполнена.
