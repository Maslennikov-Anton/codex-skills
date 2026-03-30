---
name: yandex-tracker-operations
description: >
  Работать с Yandex Tracker end to end: очереди, поля, issue workflows,
  комментарии, вложения, transitions, аутентификация и API-вызовы.
  Использовать, когда пользователю нужна операционная или инженерная работа с
  Yandex Tracker через shell scripts, HTTP requests или автоматизацию. По
  умолчанию предпочитать локальный helper script и повторяемые operational
  workflows, а не разовые ручные запросы.
---

# Yandex Tracker Operations

Используй этот skill, когда задача связана с Yandex Tracker как доменом: очередями, issue workflows, transitions и операционной работой, а не только с одним HTTP endpoint.

## Что покрывает этот skill

- Операционные сценарии вокруг очередей, issues и workflow.
- Аутентификацию, проверку доступа и discovery полей.
- Комментарии, вложения, transitions и повторяемые shell/API workflows.
- Разбор типовых API errors и конфликтов данных.

## Предпочтительный toolchain

1. Локальный helper `scripts/tracker_api.sh`.
2. Повторяемые `curl`/shell workflows с явными headers и env vars.
3. Hand-rolled scripts только если стандартного helper path недостаточно.

## Workflow

1. Определи точную операцию и целевой объект:
   - auth/discovery;
   - issue read/search;
   - issue create/update;
   - comments/attachments;
   - transitions/status workflow.
2. Если credentials или org context неизвестны, начни с [references/auth-and-request-format.md](references/auth-and-request-format.md).
3. Для проверки доступа сначала вызови `GET /v3/myself`.
4. Перед записью в issue или переходом статуса проверь queue-specific fields и доступные переходы через [references/discovery-and-troubleshooting.md](references/discovery-and-troubleshooting.md).
5. Для типовых операций предпочитай готовые формы из [references/common-operations.md](references/common-operations.md) и [references/endpoint-matrix.md](references/endpoint-matrix.md).
6. Если поведение выглядит нестабильным, сначала локализуй причину через troubleshooting, а не списывай проблему на token или API bug.

## Какие references открывать

- Coverage map по областям API:
  [references/api-coverage-map.md](references/api-coverage-map.md)
- Auth, headers, pagination и request semantics:
  [references/auth-and-request-format.md](references/auth-and-request-format.md)
- Типовые операции и адаптируемые примеры:
  [references/common-operations.md](references/common-operations.md)
- Endpoint matrix:
  [references/endpoint-matrix.md](references/endpoint-matrix.md)
- Queue discovery, custom fields и troubleshooting:
  [references/discovery-and-troubleshooting.md](references/discovery-and-troubleshooting.md)

## Практические правила

- Не печатай token-ы в ответах.
- До глубокой отладки сначала проверяй auth и org headers.
- Перед update меняй только те поля, которые пользователь явно запросил.
- Для transitions сначала получай список допустимых переходов.
- Для file upload используй multipart form data, а не JSON.
- Явно отмечай, когда вывод основан на docs, а не на live API response.
