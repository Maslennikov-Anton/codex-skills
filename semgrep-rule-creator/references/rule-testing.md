# Тестирование правила

Проверяй синтаксис на установленной версии. Обычно rule YAML и fixture имеют одинаковый stem, например `deny-empty.yaml` и `deny-empty.py`.

```bash
semgrep --test --metrics=off /tmp/rule-fixture/
semgrep scan --metrics=off --config /tmp/rule-fixture/deny-empty.yaml --json /path/to/scoped/source
```

При отдельных directories используй `--test --config <rules-dir> <targets-dir>` и соответствующую структуру имен. `--error` нужен, когда findings должны менять exit code; обычный scan может завершиться 0 с findings. Всегда читай `results`, `errors` и scan scope из JSON.

`todoruleid`/`todook` допускают известные пробелы, но не доказывают, что guard готов: важный для этой задачи случай должен реально проверяться. Для autofix нужен отдельный expected fixed fixture и проверка сохранения поведения; autofix не следует из разрешения на read-only review.

Негативный пример с другой семантикой требует ограничения scope. Например `if allowed and user not in allowed` опасен для deny-by-default allowlist, но может быть корректным для optional filter. AST не знает этот контракт. Сужай правило до доказанной API/области либо явно оставляй его advisory.

Официальные источники: [testing rules](https://docs.semgrep.dev/writing-rules/testing-rules), [rule syntax](https://docs.semgrep.dev/writing-rules/rule-syntax). Документацию подгружай по нужной возможности, а не целиком перед каждым запуском.
