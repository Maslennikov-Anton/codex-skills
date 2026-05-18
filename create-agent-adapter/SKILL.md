---
name: create-agent-adapter
description: >
  Создавать или менять Paperclip agent adapter: пакет адаптера, интерфейсы,
  модули, регистрацию и поддержку CLI/API/custom AI coding tools.
---

# Создание Agent Adapter для Paperclip

Используй этот skill, когда нужно создать adapter package или изменить контракт adapter system в Paperclip. Задача skill - держать правильную структуру пакета, обязательные интерфейсы и registry points; подробности читать в `references/` по необходимости.

## When

- Новый adapter package для local CLI, API-based агента или custom process.
- Поддержка нового agent runtime в server, UI и CLI слоях.
- Изменение session handling, parse layer или environment test contract.
- Новые поля config, transcript parsing или runtime behavior существующего adapter.

Не используй для обычной backend/UI разработки вне adapter system.

## Contract

Adapter - самодостаточный пакет:

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

Обязательные consumers:

- server: `execute`, `testEnvironment`, `sessionCodec`, parse helpers.
- UI: `parseStdoutLine`, `ConfigFields`, `buildAdapterConfig`.
- CLI: `formatStdoutEvent`.

Registry points:

- `server/src/adapters/registry.ts`
- `ui/src/adapters/registry.ts`
- `cli/src/adapters/registry.ts`

## Workflow

1. Определи runtime: local CLI, remote API, custom process или hybrid.
2. Выбери names: type -> `snake_case`, package -> `@paperclipai/adapter-<kebab-name>`, dir -> `packages/adapters/<kebab-name>/`.
3. Создай exports: `.`, `./server`, `./ui`, `./cli`.
4. Root `index.ts`: `type`, `label`, `models`, `agentConfigurationDoc`.
5. Server: config parsing через `@paperclipai/adapter-utils/server-utils`, execution, output parsing, session persistence/retry, `testEnvironment`.
6. UI: transcript parser, config builder, adapter-specific fields.
7. CLI: formatter для `paperclipai run --watch`.
8. Зарегистрируй adapter во всех registry.
9. Добавь тесты на parsing, session codec и config building.
10. Проверь, что adapter не загрязняет cwd и безопасно обращается с секретами.

## Rules

- Root `index.ts` dependency-free: без Node APIs и React.
- `agentConfigurationDoc` описывает routing logic: когда использовать adapter и когда не использовать.
- Config и stdout агента недоверенные: безопасный parsing, без dynamic execution.
- Сессионность проектируй сразу; stale session retry должен быть явным.
- Не копируй Paperclip skills в рабочую директорию пользователя; используй tmpdir/global config/изоляцию.
- Секреты передавай через environment, не через prompt template.
- Sandboxing, approvals и network controls документируй и ограничивай явно, если runtime их поддерживает.

## References

- `references/architecture-and-contract.md` -> структура пакета, интерфейсы, registration contract.
- `references/session-runtime-patterns.md` -> session management, server-utils, skills injection, prompt/config patterns.
- `references/security-and-testing.md` -> security rules, transcript kinds, testing checklist.

## Формат ответа

Верни: выбранный runtime, файлы/модули, server/UI/CLI contracts, риски session/secrets/cwd/parsing и минимальные тесты/проверки.
