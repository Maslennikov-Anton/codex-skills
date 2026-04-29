---
name: para-memory-files
description: >
  Работать с файловой PARA-памятью: сохранять, искать и обновлять знания,
  daily notes, entities, tacit knowledge, planning files и recall через qmd.
---

# Файловая PARA-память

Постоянная файловая память, организованная по методу PARA Тьяго Форте. Три слоя: knowledge graph, daily notes и tacit knowledge. Все пути заданы относительно `$AGENT_HOME`.

## Три слоя памяти

### Слой 1: Knowledge Graph (`$AGENT_HOME/life/` -- PARA)

Хранилище на основе сущностей. Для каждой entity создается папка с двумя уровнями:

1. `summary.md` -- быстрый контекст, читать в первую очередь.
2. `items.yaml` -- атомарные факты, читать по мере необходимости.

```text
$AGENT_HOME/life/
  projects/          # Active work with clear goals/deadlines
    <name>/
      summary.md
      items.yaml
  areas/             # Ongoing responsibilities, no end date
    people/<name>/
    companies/<name>/
  resources/         # Reference material, topics of interest
    <topic>/
  archives/          # Inactive items from the other three
  index.md
```

**Правила PARA:**

- **Projects** -- активная работа с целью или дедлайном. После завершения переносить в archives.
- **Areas** -- постоянные области ответственности: люди, компании, обязанности. Без даты окончания.
- **Resources** -- справочные материалы и интересующие темы.
- **Archives** -- неактивные элементы из любой категории.

**Правила фактов:**

- Устойчивые факты сразу сохраняй в `items.yaml`.
- Раз в неделю переписывай `summary.md` на основе активных фактов.
- Никогда не удаляй факты. Вместо этого помечай их как superseded (`status: superseded`, добавляй `superseded_by`).
- Когда entity перестает быть активной, переносить ее папку в `$AGENT_HOME/life/archives/`.

**Когда создавать entity:**

- Сущность упоминалась 3+ раза, ИЛИ
- Она напрямую связана с пользователем: семья, коллега, партнер, клиент, ИЛИ
- Это значимый проект или компания в жизни пользователя.
- В остальных случаях просто зафиксируй это в daily notes.

Схему атомарных YAML-фактов и правила memory decay смотри в [references/schemas.md](references/schemas.md).

### Слой 2: Daily Notes (`$AGENT_HOME/memory/YYYY-MM-DD.md`)

Сырая временная шкала событий -- слой "когда".

- Пиши туда по ходу разговоров.
- Во время heartbeats выноси устойчивые факты в Layer 1.

### Слой 3: Tacit Knowledge (`$AGENT_HOME/MEMORY.md`)

Как пользователь действует -- паттерны, предпочтения, извлеченные уроки.

- Это не факты о мире, а факты о пользователе.
- Обновляй слой всякий раз, когда узнаешь новые operating patterns.

## Записывай, а не держи в голове

Память не переживает перезапуск сессии. Файлы переживают.

- Хочешь что-то запомнить -> ЗАПИШИ ЭТО В ФАЙЛ.
- "Запомни это" -> обнови `$AGENT_HOME/memory/YYYY-MM-DD.md` или нужный entity-файл.
- Извлек урок -> обнови `AGENTS.md`, `TOOLS.md` или релевантный skill-файл.
- Ошибся -> задокументируй, чтобы future-you не повторил это.
- Текстовые файлы на диске всегда лучше, чем временный контекст в голове.

## Вспоминание памяти -- через qmd

Используй `qmd`, а не обычный grep по файлам:

```bash
qmd query "what happened at Christmas"   # Semantic search with reranking
qmd search "specific phrase"              # BM25 keyword search
qmd vsearch "conceptual question"         # Pure vector similarity
```

Индексируй свою папку памяти командой `qmd index $AGENT_HOME`

Вектора + BM25 + reranking помогают находить вещи даже при другой формулировке.

## Планирование

Храни планы в timestamped-файлах в `plans/` в корне проекта, вне personal memory, чтобы к ним могли обращаться и другие агенты. Для поиска по планам используй `qmd`. Планы устаревают: если существует более новый план, не путай его со старой версией. Если заметил устаревание, обнови файл и укажи, чем он superseded.
