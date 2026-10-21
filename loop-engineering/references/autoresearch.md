# Сравнение кандидатов с фиксированным оценщиком

Необязательный experimental mode для измеримого улучшения в рамках согласованного loop contract.
При обычной диагностике, сборе требований или qualification продукта используй основной workflow.

## Контракт до первой правки

- Цель и единицы метрики; направление `min`/`max`; минимальное значимое абсолютное изменение.
- Лимит кандидатов из запроса пользователя, timeout одного запуска и допустимые mutable artifacts.
  Baseline — один дополнительный запуск; максимум времени evaluator: `(1 + candidates) × timeout`, без накладных расходов.
- Независимый oracle: требования, evaluator, все fixtures, selection/runner/config, dependency locks и протокол измерения.
  Замораживай каталоги тестов целиком, чтобы видеть добавление/удаление cases; отдельно включай внешние configs.
- Одинаковые workload, окружение, ресурсные ограничения и обязательные проверки корректности для всех кандидатов.
  Установленные зависимости и сервисы идентифицируй в evaluator: один lockfile не доказывает состояние runtime.
- Owned workspace по `artifact-lifecycle`; state/ledger/logs вне исходников, в `evidence/`. Не помещай большие продукты в evidence.

Первый запуск — исходный artifact. Не переснимай baseline после изменения проверок, ослабления inputs или плохого результата.
Если baseline failed/invalid, останови оптимизацию и разбери причину. Новая сессия требует обоснованного нового контракта;
старые результаты сохраняются. Изменение evaluator — отдельная задача с независимыми основаниями и новым сравнением обеих версий.

## Механический helper

[experiment.py](../scripts/experiment.py), Python >=3.11, Linux, stdlib. Выполняет **одну** foreground-команду за вызов,
без shell. Запускай только разрешённые локальные команды в disposable pilot или подходящем checkout.
Ниже пример **для уже согласованных** двух кандидатов/30 секунд; это не значения по умолчанию:

```bash
python3 /home/ant/codex-skills/loop-engineering/scripts/experiment.py init \
  --root /absolute/pilot --state /absolute/owned/evidence/comparison \
  --protected evaluator.py --protected tests --protected protocol.json \
  --artifact candidate.py --direction min --min-delta 1 \
  --max-experiments 2 --timeout 30 \
  --objective 'AST nodes; supported sum cases must all pass; same Python and fixtures' \
  -- /absolute/python3 evaluator.py
python3 /home/ant/codex-skills/loop-engineering/scripts/experiment.py run \
  --state /absolute/owned/evidence/comparison --label baseline
# Измени только candidate.py, затем вызови run с описанием гипотезы.
```

Evaluator сначала проверяет **весь согласованный набор** (включая число/IDs случаев и запрет неожиданных skips),
сохраняет настоящие failures/statuses и возвращает исходный ненулевой code при провале. Только после успешных обязательных
проверок печатает в stdout один JSON `{"metric": 42}`. Диагностика — stderr. stdout до 64 KiB; число конечное, не bool.
Для существующих test/CI surfaces дополнительно применяй `autotest-engineer` / `test-integrity.md`.

Helper фиксирует содержимое/состав/режим файлов, command, metric policy, artifact identity и хеш окружения/launcher/kernel.
Он проверяет protected inputs до/после запуска и artifact до/после, сохраняет raw stdout/stderr, исходный exit code,
отдельный `evaluation_status`, метрику и решение. Ошибка/timeout/invalid получают `metric: null`, а не выгодный ноль.
Из окружения исключены только `PWD`, `OLDPWD`, `SHLVL`, `_`; child cwd фиксирован, bytecode выключен. Секретные значения
окружения в contract не записываются. Изменение окружения блокирует сравнение, включая `PYTEST_ADDOPTS`.

`ledger.jsonl` дополняется; цепочка digest выявляет случайное редактирование истории/contract. Одновременные запуски
блокируются lock. Незавершённый attempt блокирует продолжение; не удаляй его ради retry. Любая начатая попытка,
включая failed/invalid, расходует лимит. Timeout завершает группу процессов этой команды; evaluator не должен создавать
фоновые службы или отделённые процессы. Лимит нельзя обходить новым state или сменой baseline.

## Решения и исходные статусы

| Decision | Основание | Действие агента |
| --- | --- | --- |
| `baseline` | Исходный artifact, проверки успешны, metric валидна | Сохранить точку сравнения |
| `keep` | Все gates успешны; выигрыш против лучшего сохранённого результата >= min-delta и строго > 0 | Review scope/сложности, затем выбрать кандидата |
| `discard` | Равенство или ухудшение против incumbent | Отклонить идею; вернуть только собственные изменения вручную |
| `no-signal` | Положительная разница меньше порога | Не заявлять улучшение; сменить гипотезу/остановиться |
| `failed` | Ненулевой exit evaluator | Сохранить failed и raw evidence; классифицировать причину |
| `crash` | Timeout или команда не запустилась | Сохранить диагностику; расходовать лимит, без retry до green |
| `invalid` | Подмена inputs/environment/artifact, невалидный metric output | Не сравнивать числа; разобраться в нарушении протокола |

CLI: valid `baseline/keep/discard` → 0; invalid/no-signal/не выполненная проверка → 3; timeout → 124.
Ненулевой exit evaluator передаётся без изменения (signal отображается как `128 + signal`); оригинальное значение
остаётся в JSON. Если guard тоже нарушен, decision может быть invalid при evaluation_status failed: исходное падение
и code всё равно сохраняются. Нулевой exit helper не означает улучшение: читай decision.

`keep` не делает commit/reset/push и не отменяет review. Упрощение при равной метрике можно выбрать отдельным
обоснованным решением, сохранив автоматический `discard` в ledger. Поддержанный дефект остаётся failed, даже если
исследование закончено. Не оптимизируй pass-rate за счёт oracle, selection, mocks, skips или reporting wrapper.

## Границы доказательств

Это инструмент воспроизводимости, а не sandbox или защита от агента, который может переписать helper, contract и ledger.
Он не доказывает корректность самого oracle, полноту выбранных protected paths или честность произвольного evaluator.
Зависимости вне watched paths, внешние сервисы и ресурсный шум требуют отдельных проверок; просмотри полный relevant diff.
Для CPU/time/memory используй `performance-benchmark`: одинаковые workload/environment/protocol, повторения и оценку шума.
Один меньший time sample не даёт оснований для keep; неполные/шумные измерения остаются no-signal.
Helper покрыт contract tests и локальным пилотом; выбор режима моделью и полезность в реальных задачах отдельно не доказаны.

## Источник

Идея фиксированного evaluator, baseline и журнала решений:
[Karpathy autoresearch/program.md](https://github.com/karpathy/autoresearch/blob/068d93da75aa45f72ba482046f108241aaaf1b8e/program.md),
проверено 2026-10-21. Локальные инструкции и helper написаны самостоятельно, исходный код/текст не копируются.
Из upstream не перенесены бесконечный loop, автоматические Git reset/commit, GPU-зависимость и нули вместо crash metrics.
