---
name: create-agent-adapter
description: >
  Создавать или менять Paperclip agent adapter: пакет адаптера, интерфейсы,
  модули, регистрацию и поддержку CLI/API/custom AI coding tools.
---

# Создание Agent Adapter для Paperclip

Используй этот skill, когда нужно добавить новый adapter package или изменить базовый контракт adapter system в Paperclip. Основная задача skill: быстро привести к правильной структуре пакета, обязательным интерфейсам и точкам регистрации, а подробные примеры и reference-материалы читать только по необходимости.

## Когда использовать

Используй skill, если нужно:

- создать новый adapter package для локального CLI, API-based агента или custom process;
- добавить поддержку нового agent runtime в server, UI и CLI слоях;
- изменить session handling, parse layer или environment test contract адаптера;
- доработать существующий adapter под новые поля config, transcript parsing или runtime-поведение.

Не используй skill, если задача сводится только к обычной backend/UI разработке вне adapter system.

## Что обязательно должно получиться

Каждый adapter должен быть самодостаточным пакетом с реализациями для трех consumers:

- server: `execute`, `testEnvironment`, `sessionCodec`, parse helpers;
- UI: `parseStdoutLine`, `ConfigFields`, `buildAdapterConfig`;
- CLI: `formatStdoutEvent`.

Минимальная структура:

```text
packages/adapters/<name>/
  src/
    index.ts
    server/
    ui/
    cli/
  package.json
  tsconfig.json
```

Adapter обязательно регистрируется в трех registry:

- `server/src/adapters/registry.ts`
- `ui/src/adapters/registry.ts`
- `cli/src/adapters/registry.ts`

## Базовый workflow

1. Определи тип runtime: local CLI, remote API, custom process, hybrid.
2. Выбери имя адаптера:
- adapter type -> `snake_case`
- package -> `@paperclipai/adapter-<kebab-name>`
- directory -> `packages/adapters/<kebab-name>/`
3. Создай пакет с четырьмя export entrypoints: `.`, `./server`, `./ui`, `./cli`.
4. Опиши metadata в root `index.ts`: `type`, `label`, `models`, `agentConfigurationDoc`.
5. Реализуй server core:
- config parsing через `@paperclipai/adapter-utils/server-utils`;
- process/API execution;
- parse output;
- session persistence и retry на stale session;
- `testEnvironment`.
6. Реализуй UI-часть:
- transcript parser;
- config builder;
- adapter-specific config fields.
7. Реализуй CLI formatter для `paperclipai run --watch`.
8. Зарегистрируй adapter во всех registry.
9. Добавь тесты минимум на parsing, session codec и config building.
10. Прогони проверки и убедись, что adapter не загрязняет cwd и безопасно обращается с секретами.

## Ключевые правила

- Root `index.ts` должен быть dependency-free: без Node APIs и без React.
- `agentConfigurationDoc` пиши как routing logic: когда использовать adapter и когда не использовать.
- `config` и stdout агента считай недоверенными данными: парси безопасно, ничего не исполняй динамически.
- Сессионность проектируй сразу как норму, а не как позднюю оптимизацию.
- Не копируй Paperclip skills в рабочую директорию пользователя; используй tmpdir, глобальный config dir или другой изолированный механизм.
- Секреты передавай через environment, а не через prompt template.
- Если runtime поддерживает sandboxing, approvals или network controls, документируй и ограничивай их явно.

## Минимальный checklist

- [ ] `package.json` с exports для `.`, `./server`, `./ui`, `./cli`
- [ ] root `index.ts` с `type`, `label`, `models`, `agentConfigurationDoc`
- [ ] `server/execute.ts`
- [ ] `server/test.ts`
- [ ] `server/parse.ts`
- [ ] `server/index.ts`
- [ ] `ui/parse-stdout.ts`
- [ ] `ui/build-config.ts`
- [ ] `ui/config-fields.tsx`
- [ ] `ui/index.ts`
- [ ] `cli/format-event.ts`
- [ ] `cli/index.ts`
- [ ] регистрация в server/UI/CLI registry
- [ ] тесты на parse/session/config

## Карта reference-файлов

Читай только нужный раздел:

- `references/architecture-and-contract.md` -> структура пакета, интерфейсы и registration contract
- `references/session-runtime-patterns.md` -> session management, server-utils, skills injection, prompt/config patterns
- `references/security-and-testing.md` -> security rules, transcript kinds, testing checklist

## Формат ответа

Когда просят создать или изменить adapter, возвращай:

1. Какой тип adapter runtime выбран и почему.
2. Какие файлы и модули нужно создать или изменить.
3. Какие обязательные контракты server/UI/CLI будут реализованы.
4. Какие риски есть в session handling, secrets, cwd isolation и parsing.
5. Какой минимальный набор тестов и проверок нужен перед завершением.
