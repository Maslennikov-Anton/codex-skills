# Неизменность смысла проверок

Применять при написании/изменении тестов, диагностике падений и изменении selection/CI reporting. Цель — вердикт о тестируемом артефакте, включая честный fail, а не рост pass-rate.

## До изменений

Зафиксируй источник ожидаемого поведения (требование/документ/согласованный контракт), supported inputs, positive/negative смысл, перечень/число выбранных тестов, artifact version/hash и команду запуска. Поведение текущего продукта не становится oracle само по себе.

Для изменений в существующем тестовом проекте сохрани working-tree baseline вне репозитория через `scripts/test_integrity.py` из этого skill:

```bash
python3 /home/ant/codex-skills/autotest-engineer/scripts/test_integrity.py --repo /absolute/repo snapshot --output /absolute/evidence/test-baseline.json
python3 /home/ant/codex-skills/autotest-engineer/scripts/test_integrity.py --repo /absolute/repo check --snapshot /absolute/evidence/test-baseline.json
```

Baseline делается до правок; нельзя перезаписать/переснять его после ослабления. Helper учитывает working tree, включая уже существующие изменения; не требует clean HEAD. Дополнительные нестандартные tracked paths добавляй через `--also-watch relative/path` при snapshot (например custom runner/bridge и конфиг выборки).

## При падении

- Классифицируй: defect артефакта, ошибка harness/test, окружение или пока unknown. Для каждого вывода нужны факты; unknown остаётся unknown.
- Если артефакт нарушает supported contract, positive test остаётся positive и failed. Сохрани raw output, artifact hash, command, expected/actual и минимальное воспроизведение. При задаче на тестирование это полноценный полезный результат.
- Не добавляй skip/xfail/quarantine, `assert True`, ранний return, широкие accepted values/error codes, swallow exception, мок тестируемой границы, retry до успеха или исключение неудобного входа из генератора ради green. Не уменьшай selection/порог покрытия/силу CI gate ради того же эффекта.
- Исправлять ошибочный тест/harness можно: укажи независимое основание из контракта, прежнюю ошибку и почему новый oracle сохраняет силу проверки. Одно лишь «так сейчас возвращает продукт» основанием не является. Не трогай продукт без разрешения на product fix.
- При product fix покажи fail на исходном артефакте и pass на исправленном с тем же oracle. Если продукт недоступен для правки — результат остаётся красным; это не повод менять тест.
- Existing repo policy для ожидаемых исключений не является разрешением скрывать новый supported defect. Для изменения смысла supported expectation нужно прямое решение пользователя/новый согласованный контракт.

## Перед завершением

1. Сравни тестовый diff и selection с baseline. Helper возвращает 0 при неизменности watched files, 2 при любом изменении (нужно review), 3 если проверка не выполнена. Это alarm, не semantic verifier и не замена runner. Даже усиление/добавление тестов требует review, а unchanged не доказывает достаточность assertions.
2. Каждую смену oracle, inputs, mocks, skips, test count, selection, thresholds и result mapping объясни контрактом. AST hints помогают найти переписанные/удалённые assertions и новые skip/catch/mock; неизвестные языки/config получают общий change signal. Просмотри весь diff runner/helpers, которые не попали в watch set.
3. Запиши отдельно: продуктовые passed/failed/broken/skipped (и retries), полноту requested set, здоровье CI/публикации. Exit 0 wrapper не доказывает test pass. Не менять Allure/JUnit statuses. Green wrapper допустим только по ранее явно согласованному reporting contract, а не как новый способ скрыть failure.
4. Отчёт «проверка завершена, найдены дефекты» допустим при failed tests. «Продукт исправлен/все тесты проходят» — только по соответствующему свежему evidence.

## Sources

Собственные инструкции и helper, без vendored кода. Проверены 2026-10-21:

- [python-testing](https://github.com/konstruktoid/prescryb/blob/899dc4f51ef465e6f3c88d1105bf0db530ee9ae4/.agents/skills/python-testing/SKILL.md): fail-before-fix и запрет weaken/skip/xfail ради green; «весь suite green» не переносится как обязательный результат qualification артефактов.
- [constraints](https://github.com/domengabrovsek/agent-config/blob/fb6ffd149e68e2b9ba40da5e85d3461cbb5150f9/skills/constraints/SKILL.md): защищать сам quality bar и ревьюить changes in gates. Чужие thresholds, full workflow и tools не импортируются.
