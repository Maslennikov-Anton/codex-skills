# Измерения

- `python3 -m cProfile -o /tmp/profile.pstats script.py` и `pstats`: Python CPU hotspots/call counts; instrumentation искажает время.
- `time.perf_counter()` или `timeit`: повторяемая workload wall time; не включай setup только у одного варианта. Для IO укажи cache/network state.
- `tracemalloc`: peak Python allocations в отдельном запуске; не вся native/process memory.
- `/usr/bin/time -v`: whole-process max RSS (Linux KiB), CPU и wall time; разные процессы/деревья требуют одинаковой методики.
- `perf stat/record`: hardware/CPU counters, если уже разрешены окружением. Valgrind — глубокий отдельный запуск с большим overhead; его времена не сравнивай с обычными.

## JSON для wall-time helper

```json
{
  "revision": "source-sha256-or-git-sha",
  "environment": {"cpu": "model", "kernel": "version", "python": "version", "dependencies": "lock-digest"},
  "workload": {"id": "partition-100k", "input_sha256": "digest", "size": 100000},
  "protocol": {"warmups": 2, "repeats": 7, "unit": "seconds", "method": "alternating perf_counter, setup excluded"},
  "samples_seconds": [0.101, 0.102, 0.1, 0.103, 0.102, 0.101, 0.1]
}
```

Revision различается; environment/workload/protocol должны совпадать. Включай в них существенные параметры: число потоков, команды, governor/SMT при доступности, dataset digest, cache/setup policy. Helper не проверяет правдивость manifest и не доказывает одинаковый output.

По умолчанию минимум 5 samples, CV <= 5%, выигрыш медианы >= 5% и непересекающиеся диапазоны. Это консервативный smoke gate, не статистический confidence interval. Для малых эффектов нужна более длинная калибровка/повторы на другом времени; не подгоняй порог к результату. Аргументы `--max-cv` и `--min-win` задаются долями, например `0.05`.

Exit codes: 0 — measurement-win; 1 — no-win; 2 — inconclusive (несравнимость/шум/мало данных); 3 — некорректный input. JSON сохраняет причины. Даже при exit 0 отдельно приложи functional test/output equivalence и memory/scaling evidence, если они входят в задачу.
