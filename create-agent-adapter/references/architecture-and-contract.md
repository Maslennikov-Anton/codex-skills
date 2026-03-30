# Архитектура и контракт adapter package

## Базовая структура пакета

```text
packages/adapters/<name>/
  src/
    index.ts
    server/
      index.ts
      execute.ts
      parse.ts
      test.ts
    ui/
      index.ts
      parse-stdout.ts
      build-config.ts
    cli/
      index.ts
      format-event.ts
  package.json
  tsconfig.json
```

Adapter связывает orchestration layer в Paperclip с конкретным runtime AI-агента. Каждый adapter должен закрывать три consumer'а: server, UI и CLI.

## Registry точки подключения

| Registry | Location | Interface |
|----------|----------|-----------|
| Server | `server/src/adapters/registry.ts` | `ServerAdapterModule` |
| UI | `ui/src/adapters/registry.ts` | `UIAdapterModule` |
| CLI | `cli/src/adapters/registry.ts` | `CLIAdapterModule` |

## Общие типы из `@paperclipai/adapter-utils`

### Server

```ts
interface AdapterExecutionContext {
  runId: string;
  agent: AdapterAgent;
  runtime: AdapterRuntime;
  config: Record<string, unknown>;
  context: Record<string, unknown>;
  onLog: (stream: "stdout" | "stderr", chunk: string) => Promise<void>;
  onMeta?: (meta: AdapterInvocationMeta) => Promise<void>;
  authToken?: string;
}

interface AdapterExecutionResult {
  exitCode: number | null;
  signal: string | null;
  timedOut: boolean;
  errorMessage?: string | null;
  usage?: UsageSummary;
  sessionId?: string | null;
  sessionParams?: Record<string, unknown> | null;
  sessionDisplayId?: string | null;
  provider?: string | null;
  model?: string | null;
  costUsd?: number | null;
  resultJson?: Record<string, unknown> | null;
  summary?: string | null;
  clearSession?: boolean;
}

interface AdapterSessionCodec {
  deserialize(raw: unknown): Record<string, unknown> | null;
  serialize(params: Record<string, unknown> | null): Record<string, unknown> | null;
  getDisplayId?(params: Record<string, unknown> | null): string | null;
}

interface ServerAdapterModule {
  type: string;
  execute(ctx: AdapterExecutionContext): Promise<AdapterExecutionResult>;
  testEnvironment(ctx: AdapterEnvironmentTestContext): Promise<AdapterEnvironmentTestResult>;
  sessionCodec?: AdapterSessionCodec;
  supportsLocalAgentJwt?: boolean;
  models?: { id: string; label: string }[];
  agentConfigurationDoc?: string;
}
```

### UI

```ts
interface UIAdapterModule {
  type: string;
  label: string;
  parseStdoutLine: (line: string, ts: string) => TranscriptEntry[];
  ConfigFields: ComponentType<AdapterConfigFieldsProps>;
  buildAdapterConfig: (values: CreateConfigValues) => Record<string, unknown>;
}
```

### CLI

```ts
interface CLIAdapterModule {
  type: string;
  formatStdoutEvent: (line: string, debug: boolean) => void;
}
```

## Environment test contract

```ts
type AdapterEnvironmentCheckLevel = "info" | "warn" | "error";
type AdapterEnvironmentTestStatus = "pass" | "warn" | "fail";

interface AdapterEnvironmentCheck {
  code: string;
  level: AdapterEnvironmentCheckLevel;
  message: string;
  detail?: string | null;
  hint?: string | null;
}

interface AdapterEnvironmentTestResult {
  adapterType: string;
  status: AdapterEnvironmentTestStatus;
  checks: AdapterEnvironmentCheck[];
  testedAt: string;
}
```

Правила:

- не бросай исключения для ожидаемых проблем конфигурации;
- `error` только для реально непригодного runtime setup;
- `warn` для важных, но не блокирующих находок;
- финальный статус: `fail` при любом `error`, `warn` при отсутствии `error` и наличии предупреждений, иначе `pass`.

## Root `index.ts`

Root metadata file должен экспортировать:

- `type`
- `label`
- `models`
- `agentConfigurationDoc`

Держи его dependency-free: без Node APIs и без React, потому что он используется всеми consumer'ами.

### `agentConfigurationDoc`

Пиши его как routing logic, а не как описание фич.

Нужны:

- `Use when`
- `Don't use when`
- список ключевых config fields

Один конкретный negative case полезнее длинного рекламного текста.

## Server module

### `server/execute.ts`

Минимальные обязанности:

1. Прочитать config через helper'ы `asString`, `asNumber`, `asBoolean`, `asStringArray`, `parseObject`.
2. Собрать environment: `buildPaperclipEnv(agent)`, runtime context vars, auth token, user overrides.
3. Разобрать session state и решить, можно ли резюмировать сессию.
4. Отрендерить prompt через `renderTemplate(...)`.
5. Вызвать `onMeta(...)` до запуска runtime.
6. Запустить процесс или HTTP-call.
7. Пропарсить stdout в structured result.
8. При stale/unknown session уметь повторить запуск на fresh session.
9. Вернуть полный `AdapterExecutionResult`.

### `server/parse.ts`

Парсер должен уметь:

- доставать session/thread id;
- usage и cost;
- summary;
- error state;
- unknown session detection для retry logic.

### `server/index.ts`

Должен экспортировать:

- `execute`
- `testEnvironment`
- parse helpers
- `sessionCodec`

## UI module

### `ui/parse-stdout.ts`

Преобразует streaming stdout в `TranscriptEntry[]`.

Ожидаемые типы entries:

- `init`
- `assistant`
- `thinking`
- `tool_call`
- `tool_result`
- `user`
- `result`
- `stdout`

### `ui/build-config.ts`

Собирает `adapterConfig` из `CreateConfigValues`.

### `config-fields.tsx`

Использует общие примитивы формы и должен поддерживать:

- create mode через `values` / `set`
- edit mode через `config` / `eff` / `mark`

## CLI module

`cli/format-event.ts` форматирует stdout для `paperclipai run --watch`, обычно с `picocolors`.

## Registration checklist

После создания пакета adapter нужно зарегистрировать в:

- `server/src/adapters/registry.ts`
- `ui/src/adapters/registry.ts`
- `cli/src/adapters/registry.ts`

И проверить, что workspace видит пакет через `pnpm-workspace.yaml`, если это требуется структурой монорепо.
