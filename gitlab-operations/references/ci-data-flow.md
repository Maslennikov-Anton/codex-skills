# GitLab CI: данные, исполнение и скорость

Статус: `experimental`. Адаптация GitLab CI Handbook; attribution в [references/ci-upstream.md](ci-upstream.md).

- Cache ускоряет повторную загрузку зависимостей, может отсутствовать и не является надежным транспортом build outputs. Ключ учитывает lockfile/runtime/platform при необходимости; не клади secrets или виртуальное окружение с несовместимыми абсолютными путями в общий cache.
- Artifacts передают результат между jobs. При `needs` явно проверь, от каких jobs скачиваются нужные artifacts; `dependencies` и `needs` не смешивай без проверки семантики текущей версии. Отдельно проверь paths, expire policy, reports и итоговый compiled YAML.
- `artifacts: when: always` сохраняет диагностику после ошибок script, но не гарантирует доставку при timeout/убитом runner/не созданном файле. Выдели бюджет на cleanup и upload внутри job timeout. Успешный upload не доказывает полноту результатов Allure/TestOps.
- Shell pipeline без `pipefail` может скрыть ошибку первой команды. Если wrapper сознательно сохраняет exit code pytest ради публикации, проверь его контракт отдельно: исходные красные positive cases остаются failed в отчете; фактический pytest exit и финальный job exit фиксируются раздельно. `set -e` не должен прерывать обязательный сбор отчетов.
- `workflow:rules` выбирает типы pipeline, job `rules` выбирают jobs. Сопоставь push/MR/tag/schedule и приоритет правил; финальное широкое `when: always` может создать дубли или неожиданно включить job.
- Повторяй только доказанные transient infrastructure failures. `retry` всех `script_failure` превращает воспроизводимый продуктовый дефект в шум. Существующее согласованное поведение reporting wrapper сохраняется.

## Оптимизация с измерениями

Сначала раздели время: создание pipeline → первый job start → все parallel jobs start → исполнение → публикация. `pending`, resource-group waiting и медленный script требуют разных изменений.

Runner capacity, Kubernetes pod scheduling, `resource_group` locks и CPU/memory requests/limits — отдельные ограничения. Увеличение `parallel` само по себе не создает runner capacity. Меняй один доказанный bottleneck, сравнивай повторные прогоны с одинаковыми inputs и artifacts. Не сокращай набор тестов ради заявления об ускорении.

`parallel:matrix`, child pipelines и `interruptible` применяй по задаче и версии сервера. Публикация, migration или другие non-idempotent jobs требуют отдельного решения об отмене и retry.
