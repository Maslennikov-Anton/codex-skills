---
name: yandex-tracker-api
description: >
  Работать с API Yandex Tracker end to end: проверять доступ, подбирать
  корректные auth headers, исследовать очереди и поля, читать и обновлять
  issues, искать issues, добавлять комментарии, загружать вложения, выполнять
  transitions и разбирать типовые API errors. Использовать, когда пользователю
  нужна помощь с интеграцией, отладкой или операционной работой с Yandex
  Tracker через HTTP requests, curl или scripts.
---

# Yandex Tracker API

Используй этот skill, когда задача связана с HTTP API Yandex Tracker.

## Что покрывает этот skill

- Настройку доступа и проверку аутентификации.
- Корректную форму request-а для организаций Yandex 360 и Yandex Cloud.
- Типовые issue workflows: get, search, create, update, comment, attach files, transition status.
- Discovery очередей и полей перед записью.
- Разбор ошибок `401`, `403`, `404`, `409`, `412`, `422`, `423`, `428`, `429`.
- Переиспользуемый локальный helper script для аутентифицированных `curl`-запросов.

## Workflow

1. Прочитай цель пользователя и определи точную операцию и целевой объект.
2. Если credentials или идентификаторы организации отсутствуют, запрашивай только необходимое:
   - auth type: OAuth или IAM;
   - org header: `X-Org-ID` или `X-Cloud-Org-ID`;
   - org id;
   - источник token-а или имена env vars.
3. Сначала проверь доступ через `GET /v3/myself`.
4. Перед созданием или обновлением issues изучи требования очереди:
   - прочитай [references/common-operations.md](references/common-operations.md) для нужных endpoint-ов;
   - если важны queue-specific fields, открой [references/discovery-and-troubleshooting.md](references/discovery-and-troubleshooting.md) и проверь поля очереди.
5. Для повторяемых вызовов предпочитай локальный helper `scripts/tracker_api.sh`.
6. При редактировании issues меняй только те поля, которые запросил пользователь.
7. Для больших поисковых выборок используй search modes, задокументированные в [references/common-operations.md](references/common-operations.md).
8. Если API возвращает ошибку, разложи ее через [references/discovery-and-troubleshooting.md](references/discovery-and-troubleshooting.md) и назови вероятную root cause конкретно.

## Минимальный request contract

- Base URL: `https://api.tracker.yandex.net/v3`
- Auth header:
  - `Authorization: OAuth <token>` for OAuth 2.0
  - `Authorization: Bearer <token>` for IAM tokens
- Organization header:
  - `X-Org-ID: <id>` for Yandex 360
  - `X-Cloud-Org-ID: <id>` for Yandex Cloud Organization

Читай [references/auth-and-request-format.md](references/auth-and-request-format.md), когда нужны auth, headers, pagination или PATCH semantics.

## Helper script

Используй `scripts/tracker_api.sh`, когда нужно выполнять аутентифицированные запросы из терминала.

Обязательные env vars:

- `TRACKER_TOKEN`
- `TRACKER_ORG_ID`

Опциональные env vars:

- `TRACKER_BASE_URL` default: `https://api.tracker.yandex.net/v3`
- `TRACKER_AUTH_SCHEME` default: `OAuth`
- `TRACKER_ORG_HEADER` default: `X-Org-ID`
- `TRACKER_ACCEPT_LANGUAGE` optional, for example `en`

Примеры:

```bash
scripts/tracker_api.sh GET /myself
scripts/tracker_api.sh GET /issues/TEST-1 '?expand=attachments'
scripts/tracker_api.sh POST /issues/_search '' '{"filter":{"queue":"TEST","assignee":"me"}}'
scripts/tracker_api.sh PATCH /issues/TEST-1 '' '{"summary":"New title"}'
scripts/tracker_api.sh POST /issues/TEST-1/comments '' '{"text":"Done","markupType":"md"}'
scripts/tracker_api.sh FILE /issues/TEST-1/attachments/ /tmp/image.png
```

## Какие references открывать

- Широкая coverage map по областям API:
  [references/api-coverage-map.md](references/api-coverage-map.md)
- Матрица endpoint-ов с methods, paths и короткими примерами:
  [references/endpoint-matrix.md](references/endpoint-matrix.md)
- Auth, headers, pagination и правила request body:
  [references/auth-and-request-format.md](references/auth-and-request-format.md)
- Типовые endpoint-ы и примеры, которые легко адаптировать:
  [references/common-operations.md](references/common-operations.md)
- Queue discovery, custom fields, troubleshooting:
  [references/discovery-and-troubleshooting.md](references/discovery-and-troubleshooting.md)

## Правила работы

- Проверяй доступ до более глубокой отладки.
- Не раскрывай token-ы в ответах.
- Предпочитай queue keys и issue keys, когда они стабильны и человекочитаемы.
- Для transitions сначала получай список доступных переходов, затем выполняй нужный по id.
- Для file upload используй multipart form data, а не JSON.
- Явно отмечай, когда вывод основан на docs, а не на live API response.
