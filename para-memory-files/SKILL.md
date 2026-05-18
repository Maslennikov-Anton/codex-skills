---
name: para-memory-files
description: >
  Работать с файловой PARA-памятью: сохранять, искать и обновлять знания,
  daily notes, entities, tacit knowledge, planning files и recall через qmd.
---

# Файловая PARA-память

Используй этот skill для durable memory в `$AGENT_HOME`: knowledge graph, daily notes, tacit knowledge и planning files. Не сохраняй одноразовые логи, секреты, tokens, cookies или данные, которые пользователь не просил запоминать.

## When

- Сохранить устойчивое знание о пользователе, проекте, компании или процессе.
- Найти ранее сохраненный контекст через `qmd`.
- Обновить entity, daily note, tacit knowledge или planning file.
- Подготовить handoff между сессиями.
- Решить, что хранить в памяти, а что оставить только в текущем контексте.

## Layers

1. Knowledge graph: `$AGENT_HOME/life/`
   - `projects/` -> активная работа с целью/deadline.
   - `areas/` -> постоянные ответственности, люди, компании.
   - `resources/` -> справочные темы.
   - `archives/` -> неактивные items.
   - Entity folder содержит `summary.md` и `items.yaml`.
2. Daily notes: `$AGENT_HOME/memory/YYYY-MM-DD.md`
   - сырая временная шкала, слой "когда".
3. Tacit knowledge: `$AGENT_HOME/MEMORY.md`
   - operating patterns и предпочтения пользователя, а не факты о мире.

## Rules

- Устойчивые факты сохраняй в `items.yaml`; быстрый контекст держи в `summary.md`.
- Entity создавай, если сущность упоминалась 3+ раза, напрямую связана с пользователем или является значимым проектом/компанией; иначе пиши в daily note.
- Не удаляй факты: помечай `status: superseded` и добавляй `superseded_by`.
- Завершенные projects и неактивные entities переноси в `$AGENT_HOME/life/archives/`.
- Новые operating patterns пользователя обновляй в `$AGENT_HOME/MEMORY.md`.
- Извлеченные инженерные уроки сохраняй в релевантный `AGENTS.md`, `TOOLS.md` или skill/reference, а не только в personal memory.
- Схему `items.yaml`, статусы, access tracking и memory decay см. в `references/schemas.md`.

## Recall

Используй `qmd`, а не обычный grep:

```bash
qmd query "what happened at Christmas"
qmd search "specific phrase"
qmd vsearch "conceptual question"
qmd index $AGENT_HOME
```

## Planning Files

Планы храни в timestamped-файлах `plans/` в корне проекта, вне personal memory. Если есть более новый план, не путай его со старым; при устаревании обнови файл и укажи superseded-by.

## Формат ответа

Верни: что сохранено/найдено/обновлено, слой и файл, статус фактов (`active`, `superseded`, daily-only) и следующий recall/maintenance шаг.
