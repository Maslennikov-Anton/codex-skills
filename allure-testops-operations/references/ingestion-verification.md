# Проверка доставки результатов

Exit 0 `allurectl upload` означает успех команды, но не полноту server-side результатов. Для сравнения одной сохраненной Allure 2 batch с launch:

```bash
python3 scripts/verify_ingestion.py --results /absolute/path/allure-results --launch-id LAUNCH_ID
```

Команда запускается из каталога этого skill. Она читает `ALLURE_TESTOPS_URL`/`ALLURE_TESTOPS_TOKEN` из окружения или `/home/ant/.allure-testops.env` (`--secret-file` для другого пути). Файл поддерживает literal `KEY=value`, кавычки и `export`, без shell substitutions. Значения не попадают в отчет. Не запускай старую команду `auth` с выводом JWT в чат/лог.

Проверяются:

- все страницы `/api/testresult?launchId=...` и `/api/testresult/attachment?testResultId=...`, totals, уникальность IDs и завершение pagination;
- количество и identity каждой execution: `fullName`, `name`, `start`, `stop`; status сохраняется, включая честные failed/broken;
- вложения результата и вложенных steps: имя, media type, размер, SHA256 скачанного content;
- закрытость launch до/после проверки. Открытый launch дает только `verified_snapshot_open_launch`, не финальный verdict об ingestion.

По умолчанию лишние результаты — ошибка. `--allow-extra-results` разрешает другие executions в общем launch, но не дубликаты проверяемой execution. Локальная batch должна содержать все ожидаемые `*-result.json`, retries включаются отдельно по timestamps. Пустая batch, неоднозначная identity, неизвестная API schema или отсутствующий content дают exit 1 / `unverified`; ничего не исправляется автоматически. Результаты без `fullName/start/stop` требуют отдельного подтвержденного identity adapter, а не fallback на имя. Вложения fixtures из `*-container.json` также требуют адаптации execution mapping конкретного инстанса: helper отказывает явно, чтобы не подтвердить неполную проверку.

Только auth exchange использует POST; audit делает GET. Нет upload, restore, close или смены статуса. Проверка metadata + content не проверяет пиксели скриншота, смысл assertions или расположение attachment в execution tree. Закрытый launch подтверждает состояние batch на момент чтения, а не неизменность сервера в будущем.

API shape взят из рабочего локального клиента `src/vcstudio_ui_tests/ci_testops.py`; при изменении инстанса сверяй его Swagger. Live Swagger на дату разработки helper недоступен из текущей среды; неизвестные поля не трактуются как успешная проверка. Unit fixtures проверяют pagination, потерю/подмену вложений, retries и mismatch статусов.
