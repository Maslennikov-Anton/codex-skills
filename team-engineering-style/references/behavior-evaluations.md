# Поведенческие проверки skills

`audit_skills.py` проверяет структуру, ссылки и лексические trigger smoke cases. Его top matches не доказывают выбор skill моделью или качество выполнения задачи.

## Что измерять отдельно

- **Выбор:** какие `SKILL.md` действительно прочитаны, какие обязательные пропущены, какие нерелевантные загружены.
- **Результат:** независимые проверки артефакта и пользовательских ограничений. Совпадение формулировок ответа с инструкцией не является проверкой результата.
- **Цена:** реальные tokens, wall time и число команд. Повторные команды — диагностический счетчик, а не автоматическое доказательство лишней работы.

`scripts/evaluate_skill_behavior.py` готовит fixtures из `evals/behavior-cases.json` и оценивает сохраненный `codex exec --json` trace. Сам он модель не запускает и разрешений на delegation, сеть или внешние mutations не добавляет. Graders выполняют Python-код результата: используй доверенные cases в sandbox без секретов и доступа к рабочим проектам.

## Воспроизводимый прогон

1. До правки сохрани отдельный snapshot skills. Подготовь одинаковые fixtures для `before`, `candidate` и при необходимости `no-skill`. Зафиксируй реальную модель, версию CLI, effective settings, набор инструментов и доступные skills. Название variant само по себе ничего не отключает.
2. Используй разрешенный независимый harness. Для проверки автоматического выбора не называй ожидаемый skill в prompt. Каталог descriptions должен соответствовать snapshot; исключи случайное обнаружение пользовательских/project skills вне него. Для `no-skill` проверь их фактическое отключение в harness и trace.
3. Передай только `prompt.txt` и `workspace/`. `evaluation.json`, graders и ожидаемые ответы остаются вне среды исполнителя. Сохрани raw JSONL и измеренное время рядом с workspace, не внутри него.
4. Запусти scorer. Он проверяет успешные `command_execution` read events с содержимым skill, а не заявление «использовал skill». Другие форматы trace/MCP чтения требуют адаптера; незавершенный trace дает `inconclusive`. Отсутствие наблюдаемого чтения не доказывает, что модель не имела body другим способом.
5. Проверь результат отдельно: grader для regression oracle должен ловить исходный дефект, проходить на контрактной реализации и ловить mutation прав viewer. Анализ/план/перевод требуют независимой ручной оценки, поэтому имеют `needs_review`, а не автоматический pass.

Из корня skills repo:

```bash
python3 scripts/evaluate_skill_behavior.py prepare \
  --case truthful-positive-oracle --output /tmp/skill-eval-candidate-1 \
  --variant candidate --model ACTUAL_MODEL --harness CLI_VERSION_SETTINGS_FINGERPRINT
# Разрешенный harness выполняет prompt.txt в workspace и сохраняет trace.jsonl.
python3 scripts/evaluate_skill_behavior.py score \
  --run /tmp/skill-eval-candidate-1 \
  --trace /tmp/skill-eval-candidate-1/trace.jsonl \
  --elapsed-seconds 42.5 > /tmp/skill-eval-candidate-1/score.json
python3 scripts/evaluate_skill_behavior.py compare \
  /tmp/skill-eval-before-1/score.json /tmp/skill-eval-candidate-1/score.json
```

Время в примере — placeholder, подставляй измеренное. `score`: exit 0 — оба слоя прошли; exit 1 — fail/needs_review/inconclusive; exit 2 — ошибка входа. `compare` отказывает при разных модели, harness или fixture одного case, смешанных snapshots одного variant и повторном подсчете того же trace. Сохраненный corpus hash включает supporting resources custom skills. Он не подтверждает, что настройки harness действительно соблюдены.

## Как принимать изменение

Набор содержит positive, negative, near-miss и no-skill controls; ожидаемый выбор может включать несколько skills. Разделяй prompts для настройки и отложенной проверки. Для решения о качестве повтори сравнение несколько раз (начальный ориентир — 3); сравни долю успешных результатов, нарушения ограничений, средние затраты и разброс. Малый набор — smoke, не доказательство общего ускорения. Не делай live model runs или отдельного evaluator agent без соответствующего разрешения.

Добавляй case по реальному сбою, а не ради процента покрытия всех названий. Не меняй assertions под ответ candidate. Baseline и candidate должны получать одинаковую задачу без подсказки причины прошлой ошибки. Если поведенческие прогоны не выполнены, сообщай только о проверке инструкций и инструментов, без заявления об улучшении pass-rate или токенов.

Источники подхода: [OpenAI: evaluating skills](https://developers.openai.com/blog/eval-skills), [Agent Skills: optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions), [Anthropic: skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). CLI flags сверяй с установленным `codex exec --help`.
