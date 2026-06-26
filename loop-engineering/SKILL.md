---
name: loop-engineering
description: "Использовать для bounded loop engineering: автономно проводить ограниченные итерации улучшения, исследования или доведения артефактов с checkpoints, evidence и stopping rules."
---

# Loop Engineering

Используй этот skill, когда пользователь просит продолжать работу итерациями без постоянного вмешательства: улучшать
код, документацию, исследование, отчеты, конфигурацию, процесс или другой инженерный артефакт маленькими завершенными
slices и регулярно фиксировать evidence.

## Gate

Подходит, если одновременно верно:

- цель задана как улучшение, исследование, диагностика, стабилизация или доведение инженерного результата;
- можно делать маленькие завершенные итерации;
- каждая итерация имеет проверяемый результат;
- пользователь разрешил автономное продолжение или задал лимит итераций/времени/бюджета;
- есть понятные checkpoints и stopping rules.

Не подходит, если нужен один точечный fix, уже есть written implementation plan, root cause критического сбоя не понятен,
или задача требует опасных внешних действий без отдельного разрешения.

## Workflow

1. Зафиксируй loop contract:
   - цель;
   - лимит итераций, времени или бюджета. Бери число из запроса пользователя или явно согласованного contract; не
     подставляй фиксированное число по умолчанию;
   - допустимый scope;
   - какие типы slices допустимы: код, docs, тесты, анализ, исследование, отчеты, конфигурация, эксплуатация;
   - какие проверки доказывают progress.
2. Собери baseline:
   - текущие артефакты, known state, gaps и constraints;
   - известные проверенные и непроверенные зоны;
   - быстрый verification method или command;
   - место, куда писать ledger или summary. Не начинай правки, пока это место не выбрано.
3. Разбей работу на маленькие loop slices. Один slice должен давать один новый факт: улучшенный artifact, уточненную
   границу, обновленную документацию, проверку гипотезы, стабилизированный шаг или минимальный repro.
4. На каждой итерации:
   - выбери следующий slice по максимальной информации за минимальный риск;
   - внеси маленькое изменение;
   - запусти минимальную проверку;
   - классифицируй результат как passed, failed, blocked или no-signal;
   - запиши evidence и следующий рациональный фронт.
5. После каждого checkpoint реши: продолжать, сменить поверхность, перейти в debugging, остановиться по лимиту или
   завершить работу.
6. Перед финальным ответом используй `verification-before-completion` для свежего evidence-backed claim.

## Domain Policies

Loop Engineering управляет итерациями, но не подменяет профильные правила предметной области. Если slice попадает в
область отдельного skill, используй его правила: например, `autotest-engineer` для автотестов, `technical-writer` для
документации, `systematic-debugging` для root cause, `source-driven-development` для свежих внешних источников.

## Stop Conditions

Остановись или запроси решение пользователя, если:

- достигнут лимит итераций/времени/бюджета;
- один и тот же blocker повторился три раза;
- следующий шаг расширяет scope;
- требуется destructive action, production change или внешний publish без разрешения;
- failure непонятен и дальнейшие loop-итерации будут только умножать шум;
- быстрые проверки перестали доказывать progress;
- контекст стал длинным и нужен handoff через `context-hygiene`.

## Subagents

Если пользователь разрешил subagents и есть независимые поверхности, используй `subagent-driven-development`.
Делегируй исследование разных осей, review ledger или проверку гипотез, но основной агент остается владельцем loop
contract, итогового diff и финальной verification.

## Checkpoint Format

Короткий checkpoint после каждой итерации:

- iteration: `N/limit`;
- slice: что проверялось;
- change: какие files/artifacts изменены;
- command: что запускалось;
- result: passed / failed / blocked / no-signal;
- evidence: короткий факт, диагностический слой или observed value;
- next: продолжить, сменить ось, debug, остановиться.

Подробные шаблоны и внешние паттерны: [references/loop-patterns.md](references/loop-patterns.md).

## Related Skills

- `implementation-planner` - если сначала нужен большой план с files/tasks/verification.
- `executing-implementation-plans` - если written plan уже есть.
- `systematic-debugging` - если failure надо расследовать до root cause.
- `fuzzing-bug-hunter` - если цель именно matrix/grammar fuzzing и поиск новых defect families.
- `autotest-engineer` - если основной deliverable это код автотестов или политика правдивого test signal.
- `technical-writer` - если итерации в основном улучшают документацию.
- `context-hygiene` - если loop длинный и нужен handoff/compaction.
- `verification-before-completion` - перед финальным claim о готовности.

## Формат результата

Верни: loop contract, количество выполненных итераций, добавленные/измененные artifacts, findings, verification commands,
остановочные условия и следующий рациональный фронт.
