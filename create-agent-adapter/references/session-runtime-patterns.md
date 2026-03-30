# Session и runtime patterns

## Session management как базовый примитив

Сессионность проектируй сразу. Agent по одной задаче может просыпаться много раз: initial assignment, approval callbacks, comments, re-runs. Каждый wake должен по возможности продолжать предыдущую conversation context.

Ключевые элементы:

- `sessionParams` хранится как opaque `Record<string, unknown>`;
- `sessionCodec.serialize()` пишет session state в хранилище;
- `sessionCodec.deserialize()` поднимает его для следующего запуска;
- `sessionCodec.getDisplayId()` отдает читаемый session id для UI.

### Правила

- reuse session по умолчанию;
- проверяй совместимость resume по `cwd`, чтобы не было cross-project contamination;
- если runtime вернул unknown/stale session, повторяй запуск на fresh session и выставляй `clearSession: true`.

### Типовой паттерн

```ts
const canResumeSession =
  runtimeSessionId.length > 0 &&
  (runtimeSessionCwd.length === 0 || path.resolve(runtimeSessionCwd) === path.resolve(cwd));
const sessionId = canResumeSession ? runtimeSessionId : null;

if (sessionId && !proc.timedOut && exitCode !== 0 && isUnknownSessionError(output)) {
  const retry = await runAttempt(null);
  return toResult(retry, { clearSessionOnMissingSession: true });
}
```

Если runtime сам умеет context compaction или conversation compression, используй это преимущество через resume вместо ручного prompt bloat.

## Server-utils helpers

Импортируй из `@paperclipai/adapter-utils/server-utils`:

| Helper | Purpose |
|--------|---------|
| `asString(val, fallback)` | Safe string extraction |
| `asNumber(val, fallback)` | Safe number extraction |
| `asBoolean(val, fallback)` | Safe boolean extraction |
| `asStringArray(val)` | Safe string array extraction |
| `parseObject(val)` | Safe `Record<string, unknown>` extraction |
| `parseJson(str)` | Safe JSON parsing |
| `renderTemplate(tmpl, data)` | `{{path.to.value}}` template rendering |
| `buildPaperclipEnv(agent)` | Standard `PAPERCLIP_*` env vars |
| `redactEnvForLogs(env)` | Sensitive keys redaction |
| `ensureAbsoluteDirectory(cwd)` | Absolute cwd validation |
| `ensureCommandResolvable(cmd, cwd, env)` | Command resolution check |
| `ensurePathInEnv(env)` | PATH bootstrap |
| `runChildProcess(runId, cmd, args, opts)` | Spawn helper with timeout and logging |

Не читай `ctx.config` напрямую, если это можно выразить через helper'ы.

## Prompt template patterns

- Поддерживай `promptTemplate` как настраиваемый вход для каждого run.
- Рендери его через `renderTemplate()` со стандартным набором переменных: `agentId`, `companyId`, `runId`, `company`, `agent`, `run`, `context`.
- Default prompt должен быть коротким и функциональным.

### `agentConfigurationDoc`

Этот markdown читают LLM-агенты, которые создают или настраивают других агентов. Поэтому пиши его как routing-инструкцию:

- когда adapter подходит;
- когда adapter не подходит;
- какие поля действительно критичны;
- какие опасные флаги есть и почему они опасны.

## Skills injection

Paperclip skills нужно делать доступными runtime агенту, но нельзя загрязнять `cwd` пользователя.

### Предпочтительный порядок

1. tmpdir + runtime flag
2. global config dir самого agent tool
3. env var на skills directory
4. prompt injection как крайний случай

### Почему нельзя писать в cwd

- загрязняет git status;
- может утечь в коммиты;
- смешивает инфраструктуру Paperclip с пользовательским репозиторием.

### Примеры паттернов

#### Claude-style

- создать tmpdir;
- собрать в нем `.claude/skills/`;
- symlink'нуть skills;
- передать runtime через `--add-dir`;
- удалить tmpdir после завершения.

#### Codex-style

- использовать глобальный skills dir (`$CODEX_HOME/skills`);
- symlink'нуть только отсутствующие entries;
- не перетирать пользовательские кастомизации.

## Logging и meta

- Все stdout/stderr агентского процесса пропускай через `onLog(...)`.
- Invocation metadata отправляй через `onMeta(...)` до запуска runtime.
- При логировании env всегда используй `redactEnvForLogs()`.

## Error handling

Нужно различать:

- timeout;
- process error;
- parse failure;
- invalid config;
- missing command / invalid URL;
- stale session.

На failure заполняй `errorMessage` и по возможности клади raw diagnostics в `resultJson`, если это не раскрывает секреты.
