# Security и testing для adapter'ов

## Trust boundary: stdout и result данных агента

Adapter находится на границе между orchestration layer и LLM-driven runtime. Вывод агента считай недоверенным.

Правила:

- ничего не `eval()` и не исполняй динамически;
- используй safe extraction helpers;
- валидируй session ids, structured fields и result payloads;
- если stdout содержит URL, file paths или shell commands, просто сохраняй их как данные, а не выполняй.

## Secret handling

Секреты не должны попадать в prompt template или в текст, который проходит через LLM.

Правильный путь:

- `PAPERCLIP_API_KEY` и аналоги передавать через env;
- пользовательские секреты из config передавать как env vars;
- при логировании env использовать `redactEnvForLogs()`.

Это sidecar injection pattern: модель работает рядом с секретом, но не видит его значение напрямую.

## Network access

Если runtime поддерживает сетевые ограничения:

- предпочитай allowlist вместо open internet;
- документируй network policy в `agentConfigurationDoc`;
- учитывай, что skills + unrestricted network усиливают риск exfiltration.

## Process isolation

- CLI-based adapter наследует права процесса сервера;
- `cwd` и `env` фактически определяют поверхность доступа;
- dangerous flags вроде обхода approvals/sandboxing нужно явно маркировать как опасные;
- `timeoutSec` и `graceSec` обязательны как safety rails.

## TranscriptEntry kinds

UI viewer ожидает эти типы:

| Kind | Fields | Usage |
|------|--------|-------|
| `init` | `model`, `sessionId` | Agent initialization |
| `assistant` | `text` | Agent text response |
| `thinking` | `text` | Agent reasoning/thinking |
| `user` | `text` | User message |
| `tool_call` | `name`, `input` | Tool invocation |
| `tool_result` | `toolUseId`, `content`, `isError` | Tool result |
| `result` | `text`, usage fields, `costUsd`, error fields | Final result |
| `stderr` | `text` | Stderr output |
| `system` | `text` | System messages |
| `stdout` | `text` | Raw stdout fallback |

Если line parser не смог надежно распарсить событие, возвращай fallback `stdout`, а не пытайся угадывать структуру.

## Минимальный набор тестов

Создавай tests минимум на:

1. output parsing;
2. unknown session detection;
3. config building;
4. session codec round-trip.

Если adapter сложнее обычного CLI wrapper, добавь:

- environment test contract checks;
- cwd-aware resume logic;
- retry on stale session;
- secret redaction behavior;
- transcript parsing fallback.

## Practical done definition

Перед завершением adapter-задачи проверь:

- package зарегистрирован в server/UI/CLI registry;
- `agentConfigurationDoc` покрывает use/do-not-use cases;
- runtime не загрязняет cwd;
- session reuse и stale-session retry работают предсказуемо;
- dangerous options задокументированы;
- базовые parser/session/config tests зелёные.
