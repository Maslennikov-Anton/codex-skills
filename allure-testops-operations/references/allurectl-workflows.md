# `allurectl` workflows

Основные источники:

- https://docs.qameta.io/allure-testops/ecosystem/allurectl/
- https://github.com/allure-framework/allurectl

## Когда использовать `allurectl`

Предпочитай `allurectl`, если задача связана с:

- upload test results в Allure TestOps;
- `watch`-режимом в CI;
- созданием и управлением launch во время прогона;
- передачей launch metadata и env в downstream steps.

Не придумывай raw upload flow через API, если задача укладывается в `allurectl`.

## Базовые режимы

- `allurectl upload` — загрузить уже готовые результаты.
- `allurectl watch` — обернуть запуск тестов и автоматически вести ingestion в TestOps.

## Практические правила

- Для CI по умолчанию предпочитай `watch`, если нужно связать execution и launch lifecycle.
- Если результаты уже лежат на диске и нужен просто upload, используй `upload`.
- В automation учитывай env, который `allurectl` делает доступным:
  - `ALLURE_LAUNCH_ID`
  - `ALLURE_LAUNCH_URL`
  - `ALLURE_JOB_RUN_URL`
- Если launch нужен для дальнейших уведомлений, ссылок или post-processing, читай эти env vars, а не пытайся угадывать launch вручную.

## Что уточнять заранее

- `ALLURE_ENDPOINT`
- `ALLURE_TOKEN`
- `ALLURE_PROJECT_ID`
- директорию с результатами
- нужны ли launch tags / launch name / job run metadata

## CI-подсказки

- Если задача про GitHub Actions, GitLab CI или другой CI, сначала проверь, нужен ли `watch` вместо post-factum upload.
- Если ingestion идёт в реальном времени, launch может оставаться открытым до завершения процесса.
- Не считай итог launch окончательным, пока процесс и ingestion не закрыты.
