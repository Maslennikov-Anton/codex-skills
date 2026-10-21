# Python: точный кандидат и проверка окружения

Используй interpreter проекта явно. `pip list --outdated`/`uv pip list --outdated` показывают наличие новых версий; `pip-audit` ищет известные уязвимости и не заменяет этот список.

Для проекта с `uv.lock` после разрешенного выбора кандидата:

```bash
uv lock --upgrade-package 'package==1.2.4'
uv sync --locked
uv pip check --python .venv/bin/python
```

Сначала выполни это в отдельной копии и изучи diff lockfile. Constraints из manifest должны допускать выбранную версию. `uv lock --upgrade` обновляет весь разрешенный граф; это не режим «только патчи». Для patch-only scope явно выбери кандидаты в пределах той же major/minor и проверь транзитивные изменения. Точное ограничение передавай и pip/uv pip при работе с requirements, без миграции проекта на другой менеджер.

Disposable venv проверяет resolver, imports и небольшой контракт. Это не доказывает работоспособность настоящего проекта: нужны его зависимости, плагины, конфиг и релевантные тесты. `pip check`/`uv pip check` обнаруживают несовместимые metadata constraints, но не изменения поведения.

Для offline пилота можно построить минимальные локальные wheels с разными `Requires-Python`/`Requires-Dist` и резолвить с `--no-index --find-links`. Они проверяют методику и отказ resolver; их нельзя выдавать за прогон реального обновления pytest/Allure.

При обновлении pytest проверь совместимость Allure/Hypothesis/xdist и collection/fixtures; при обновлении HTTP-клиента — auth, timeout/retry и формат ошибок; при базовом образе — Python и системные библиотеки отдельно. Проверки выбирай по фактическому проекту.
