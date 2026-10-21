---
name: performance-benchmark
description: "Измерять CPU/memory и проверять оптимизации Linux/Python: profiling, одинаковая нагрузка before/after, шум и scaling; not GUI waits or CI queue capacity."
---

# Проверка производительности

Статус: `experimental`. Сначала найди измеримый bottleneck и зафиксируй одинаковую нагрузку. Не выдавай ускорение, полученное ослаблением проверок или уменьшением объема работы, за оптимизацию.

## Workflow

1. Выбери цель: wall time, CPU, peak memory или scaling; вход, размер и expected output. Установи scope: измерение либо разрешенная оптимизация. Следуй уже данному разрешению, не запрашивай его повторно для той же задачи.
2. Сохрани baseline: revision/source digest, Python/deps, CPU/kernel, режим нагрузки, repeats/warmups, IO/cache conditions. Повторяй одинаковый вход; при scaling меняй размер явно. Длинный GUI/network/queue wait сначала требует соответствующего evidence, а не вывода о CPU.
3. Выбери минимальный profiler по [references/measurement.md](references/measurement.md). Измерения выполняй последовательно без конкурирующих нагрузок. Не смешивай профилируемый wall time и обычный benchmark.
4. Если правка разрешена, измени узкий bottleneck и проверь тот же функциональный контракт. Чередуй baseline/candidate, исключи warmup, сохрани сырые samples и результат, а не только лучший запуск.
5. Для CPU/wall-time сравнения подготовь два JSON по reference и выполни:

   ```bash
   python3 <skill-dir>/scripts/compare_benchmarks.py /tmp/before.json /tmp/after.json
   ```

   Helper откажет при разном workload/environment/protocol, слишком малой выборке или шуме. Он оценивает только wall-time samples; функциональный результат, memory и scaling проверяются отдельно.

6. Верни измеренную разницу, разброс, число повторов, evidence корректности и ограничения. Допустимый результат — «устойчивого выигрыша нет». Статус measurement-win не означает готовность продукта.

Не меняй governor, `perf_event_paranoid`, системные сервисы или зависимости проекта автоматически. При недоступном perf можно использовать stdlib profiler; укажи потерю глубины измерения.

Источники и лицензия: [references/upstream.md](references/upstream.md).
