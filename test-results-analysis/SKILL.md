---
name: test-results-analysis
description: "Анализировать историю результатов CI/Allure: повторяемые падения, retry rescue, cross-run variability и длительности; not upload or single-failure root cause."
---

# История результатов тестов

Статус: `experimental`. Отделяй исходный результат, итог после test retries, повтор pipeline/job и изменение результата между сравнимыми прогонами. Retry rescue — сигнал для исследования, а не доказанная причина flaky.

## Workflow

1. Зафиксируй период, нужный набор case IDs, источник и полноту экспорта. Для GitLab/TestOps используй доступные read-only API или локальные artifacts через профильные operations skills; этот skill не меняет pipeline, тесты или статусы.
2. Сопоставь стабильный test ID, параметры, revision тестов, digest/build VCStudio/VCont, environment/runner profile. Разный SHA, сборка или среда — отдельные группы; не называй новую регрессию нестабильностью из-за смешения версий.
3. Установи семантику retry. Повтор job/pipeline получает отдельный run ID. Порядок файлов и UUID не доказывают номер test retry; при неизвестном порядке вывод должен остаться неопределенным.
4. Нормализуй export по [references/input-format.md](references/input-format.md). Для локальных Allure JSON доступен адаптер с явным manifest. Скрипт использует только stdlib и ничего не запрашивает по сети:

   ```bash
   python3 <skill-dir>/scripts/analyze_history.py allure manifest.json > /tmp/attempts.jsonl
   python3 <skill-dir>/scripts/analyze_history.py analyze /tmp/attempts.jsonl > /tmp/history.json
   ```

5. Проверь выборку вручную: исходные статусы/attempt IDs, denominator, пропущенные и missing tests. Длительности сравнивай на одинаковых исходах и нагрузке; медиана короткого экспорта не является p95 latency системы.

## Вывод

Покажи stable failures, rescued retries, cross-run variability candidates и incomplete/unknown группы, вместе с размером выборки и context. `failed` и `broken` сохраняй отдельно в исходных outcomes. `skipped`, `unknown`, отсутствующие результаты и прерванные запуски не считай успехами. Скрипт не знает ожидаемый полный test plan — полноту и attachments проверяй отдельно через `allure-testops-operations`.

Для причин конкретного падения используй `systematic-debugging`. Не предлагай автоматическую quarantine/xfail или ослабление positive assertions ради метрик. Не печатай токены и сырые error messages; для группировки обычно достаточно IDs и статусов.

Источники и отличия от Microsoft DuckDB workflow: [references/upstream.md](references/upstream.md).
