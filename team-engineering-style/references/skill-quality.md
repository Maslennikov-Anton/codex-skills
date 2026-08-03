# Skill Quality

## Цель

Локальный skill должен уменьшать повторное объяснение и повышать качество действий агента. Если он только пересказывает общеизвестные советы, его не нужно добавлять.

## Чеклист перед добавлением skill

- Есть повторяющийся класс задач или устойчивый workflow.
- Description содержит реальные пользовательские триггеры.
- Тема не покрыта существующим более узким skill.
- Body содержит только essential workflow, а не полный manual.
- Редкие детали вынесены в `references/`.
- Повторяемая хрупкая механика вынесена в `scripts/`.
- Нет секретов, проектных временных workaround'ов и длинных логов.
- Skill проходит `quick_validate.py`.

## Хороший description

Description должен отвечать на два вопроса:

1. Что skill делает.
2. Когда его использовать.

Пиши конкретные триггеры: файлы, инструменты, типы задач, пользовательские формулировки. Ставь самый важный trigger в начало description: список skills имеет ограниченный context budget, и длинные descriptions могут быть усечены. Не прячь условия использования только в body: агент увидит body уже после срабатывания.

Проверяй description на 2-3 реалистичных user prompts. Если новый или измененный skill не всплывает по естественной формулировке задачи, меняй description, а не добавляй общий текст в body.

## Progressive disclosure

Разделяй контекст по частоте использования:

- `SKILL.md`: короткий workflow, границы, список reference-файлов.
- `references/`: подробные варианты, checklist, схемы, примеры.
- `scripts/`: повторяемые операции, где важна детерминированность.
- `assets/`: шаблоны и файлы, которые нужно использовать в результате.

## Признаки плохого skill

- Description слишком общий: "помогает работать лучше".
- Body дублирует базовые инструкции агента.
- Skill пытается покрыть несколько профессий сразу.
- Внутри хранится одноразовое решение из одного проекта.
- Для использования нужно прочитать много reference-файлов заранее.
- После добавления он часто триггерится на нерелевантные задачи.

## Audit Checklist

- Размер: `SKILL.md` содержит только routing, workflow и hard guardrails.
- Description: короткий, конкретный, с реальными trigger terms.
- One job: skill покрывает один повторяемый класс задач, а не несколько профессий или workflow сразу.
- Progressive disclosure: подробные команды, payloads, схемы и edge cases вынесены в `references/` или `scripts/`.
- Duplication: правило не повторяет system/developer instructions и не конфликтует с ними.
- Scope: skill не смешивает профессию, локальную политику, проектный workaround и разовую заметку.
- Links: все `references/*.md` существуют и названы из `SKILL.md`.
- External skills: не устанавливай community skills без read-only review `SKILL.md`, scripts и permission/tool behavior.
- Trigger smoke: для важных изменений проверь sample prompts, чтобы ожидаемый skill попадал в top matches.
- Validation: `quick_validate.py`, `python3 scripts/audit_skills.py --strict --require-smoke-coverage` для repo-wide изменений, проверка ссылок и `git diff --check`.
