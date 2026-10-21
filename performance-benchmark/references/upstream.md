# Источник и адаптация

Источник: [jc1122/perf-benchmark-skill](https://github.com/jc1122/perf-benchmark-skill/blob/457340024cb604658942f57674aefcc70cc733ad/SKILL.md), commit `457340024cb604658942f57674aefcc70cc733ad`. Проверен 2026-10-21.

Лицензия: MIT; полный upstream текст сохранен в `../LICENSE`.

Изменения локальной адаптации (2026-10-21): Заимствованы matched workload, noise gates и no-win outcome. Большой benchmark engine и install scripts не скопированы; локальный comparator проверяет только wall time и не выдает functional approval. Нет обязательных subagents, системных изменений и автоматического ledger.

Статус experimental: небольшие локальные пилоты проверяют применимость метода и scripts, но не доказывают улучшение выбора skill моделью или экономию токенов.
