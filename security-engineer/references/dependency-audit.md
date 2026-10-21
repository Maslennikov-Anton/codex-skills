# Аудит зависимостей по измеренным данным

Статус: `experimental`. Collector и renderer адаптированы из Trail of Bits Supply Chain Risk Auditor, CC-BY-SA-4.0; [references/dependency-audit-upstream.md](dependency-audit-upstream.md) фиксирует commit, файлы и лицензию. Runtime использует stdlib, Python >=3.11; optional `gh` повышает доступный лимит GitHub API.

Применяй при запросе на аудит зависимостей/уязвимостей/состояния upstream. Обычная правка Python-кода не требует такого аудита. Поддержаны npm, PyPI и Go; exact/transitive coverage ограничена форматами parser, а не количеством файлов в проекте.

1. Определи manifest, lockfile и источник версии. `uv.lock` и npm lockfile дают resolved версии; диапазон из manifest не является установленной версией. Unsupported lockfile и fallback на latest должны остаться явно обозначены.
2. Положи report/cache вне audited repo. Runtime scripts лежат в `scripts/supply_chain/`; читай их только при работе с helper. Задай отдельный output directory и запусти:

   ```bash
   python3 <skill-dir>/scripts/supply_chain/collect.py <project-dir> --json /tmp/audit-run/findings.json --cache /tmp/audit-run/cache
   python3 <skill-dir>/scripts/supply_chain/render.py /tmp/audit-run/findings.json --out /tmp/audit-run/report.md
   ```

   Создай output directory заранее. Для сохраненного cache есть `--offline`; проверь возраст данных в notes. Anonymous и authenticated cache имеют разные ключи: смена auth-контекста может дать offline misses даже при существующих файлах cache. Не выдавай cache за свежую проверку. Scripts не устанавливают зависимости и не исполняют код target проекта.
3. Проверь exit codes, `coverage`, каждый `version_source`, notes и transitive section. `assessed_clean`, `assessed_flagged` и `unassessable` различаются: отсутствие данных не является уязвимостью и не доказывает отсутствие уязвимостей. Полностью неизмеренный/противоречивый отчет должен быть отклонен.
4. Отдели version-matched advisory от проверки latest и от метаданных репозитория. Архивирование/малое число maintainers не является доказательством эксплуатации. CVE требует приоритизации по использованию и доступному исправлению, а не автоматической замены пакета.
5. Добавь вывод по действиям: что проверено, что неизвестно, какой пакет/версию обновить и чем это затронет проект. Используй `dependency-updates`, когда пользователь поручил само обновление.

При transport/rate-limit error допустима ограниченная read-only повторная попытка, если она может дать новые данные; не обходи отказ reconciliation, удаляя неудобные строки. Ошибка collector/renderer — результат проверки инструмента, не clean verdict. Не устанавливай CI gates, не выполняй autofix и не создавай внешние issues в рамках отчета.

Для проверки helpers: `codex-tools-pytest <skill-dir>/scripts/supply_chain -q -p no:cacheprovider`. Upstream tests включают version matching, private/nonregistry specs, cache/timeout errors, неполное coverage и отказ renderer при противоречии данных.
