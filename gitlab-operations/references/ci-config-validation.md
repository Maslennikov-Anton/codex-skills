# Проверка GitLab CI конфигурации

Статус дополнения: `experimental`. Основа — GitLab CI Handbook; provenance в [references/ci-upstream.md](ci-upstream.md). Паттерны ориентированы на GitLab 18.x; сначала проверь версию своего self-managed сервера. Возможности новых релизов не становятся доступными от версии установленного `glab`.

## Узкая правка и компиляция

Прочитай root config и относящиеся `include:local`, учитывай inherited `default`/`extends`. Списки `rules`, `script`, `needs` могут заменяться при merge; наличие ключа в исходном файле не доказывает итоговую конфигурацию. Не перестраивай workflow/stages ради добавления одной job.

1. Локальный YAML parser проверяет синтаксис. Он не знает семантику GitLab; `!reference` требует соответствующего loader, обычный safe_load может его отвергнуть.
2. `POST /projects/:id/ci/lint` проверяет конфиг сервером. Передай JSON `content`; для симуляции добавь `dry_run: true`, реальный `ref`, `include_jobs: true`. Это проверка без создания pipeline. Используй host/project из target repo, сохраняй ответ без credentials.
3. При `glab api --input request.json` явно передай `--header 'Content-Type: application/json'`. Проверь `valid`, `errors`, `warnings`, `merged_yaml` и фактический набор jobs. Exit 0 у HTTP-клиента не означает `valid: true`; JSON с transport/API `error` не является lint response. Сравни с ожидаемыми jobs для контекста pipeline.
4. Симуляция по branch ref не доказывает поведение MR/tag/schedule с другими variables. Проверь нужные контексты штатным способом сервера; не утверждай, что push simulation проверила MR.
5. `shellcheck` проверяет извлеченные shell scripts. Только реальный прогон проверяет runner, pull образов, services, сеть, runtime и доставку artifacts. Не запускай его и не меняй pipeline trigger как побочный эффект lint-задачи.

`needs` на job, исключаемую через `rules`, требует согласованной логики выбора либо осознанного `optional: true`. Optional не должен скрывать действительно обязательный build. Проверяй плохой и исправленный варианты: сервер должен отклонять неправильный DAG и принимать нужную конфигурацию.

Официальный API: <https://docs.gitlab.com/api/lint/>. Версионные особенности сверяй с <https://archives.docs.gitlab.com/>.
