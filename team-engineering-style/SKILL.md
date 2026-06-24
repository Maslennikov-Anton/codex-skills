---
name: team-engineering-style
description: "Use only to define/update durable local engineering standards, technology lifecycle statuses, or resolve conflicts between local skills; not ordinary style cleanup."
---

# Локальный инженерный стиль

Этот skill задает кросс-рольные стандарты команды и правила эволюции локальных skills. Профильные инструкции, проектные workaround-и и доменные детали держи в более узких skills или `references/`.

## Когда использовать

- Нужно зафиксировать устойчивое правило команды.
- Нужно определить статус технологии или подхода.
- Нужно убрать противоречие между несколькими локальными skills.
- Нужно понять, где закрепить правило: конкретный skill, кросс-рольный стандарт или системная инструкция.
- Нужно обновить процесс эволюции skills.

## Приоритеты

- Веди работу на русском языке, если пользователь, внешний формат или интеграция явно не требуют другого языка.
- Если правило относится к одной профессии, обновляй самый узкий skill.
- Если правило одноразовое или не переживает больше одной задачи, не поднимай его в стандарт.
- Более высокий уровень инструкций текущей сессии имеет приоритет над локальным skill. Не закрепляй локальное правило, которое конфликтует с системными ограничениями.

## Defaults

- Agentic engineering lifecycle: refine/spec -> plan when useful -> small implementation slices -> test/debug -> self-review diff/evidence -> verify -> ship. Use `code-review-professional` only for requested, high-risk, shared-contract, or externally reviewed changes.
- Для новых/спорных библиотек и внешних API используй `source-driven-development`.
- Для high-risk, security-sensitive, irreversible или дорогих ошибочных выводов используй `doubt-driven-development`.
- Перед финальным claim о готовности, исправлении, успешных тестах, build/lint, commit, push или PR используй `verification-before-completion`.
- Для локальных qualification/test-product repo источник истины - текущий прогон. Тесты не являются bug inventory; не используй `xfail` и не переводи supported positive-кейсы в negative ради зеленого статуса, если repo policy не говорит обратное.
- Generated/runtime artifacts не удаляй после каждого прогона автоматически. Cleanup - отдельная операция по явной просьбе; по умолчанию артефакты остаются локально и отсеиваются через `.gitignore`.
- Для push/sync-задач в шумных repo используй `gitignore-scoped-push`: явный staged allowlist, проверка ignored preview и remote SHA.

## Технологии

Статусы технологий:

1. `experimental` - пробуем точечно, не выбираем по умолчанию.
2. `preferred` - используем по умолчанию для задач этого класса.
3. `legacy-compatible` - поддерживаем существующее, но не продвигаем в новые решения без причины.
4. `deprecated` - не выбираем для новых решений, только поддерживаем старый код.

Не повышай статус без повторяемого опыта.

## Skill Evolution

1. Зафиксируй trigger: повторяющееся решение, конфликт, устаревшее правило или новый устойчивый стек.
2. Выбери самый узкий уровень фиксации.
3. Обнови минимальный набор skills/reference/scripts.
4. Проверь, что правило не дублирует существующее и не тащит одноразовую проектную специфику.
5. Проверь YAML, ссылки на `references/`, размер `SKILL.md` и понятность `description`.
6. Git commit/push делай только по запросу пользователя или когда это явно входит в текущую задачу.

## Quality Rules

- `SKILL.md` содержит workflow и границы; редкие детали живут в `references/`, повторяемая хрупкая механика - в `scripts/`.
- `description` должен быть коротким и триггерным: цель плюс 3-6 ключевых сигналов, ориентир до 220 символов.
- Не добавляй новый skill, пока тему покрывает существующий более узкий skill.
- Не смешивай профессию, локальную политику и проектный workaround.
- Новое правило должно ускорять работу, снижать ошибки или устранять повторный выбор.

## References

- `references/evolution-process.md` -> детальный процесс развития skills.
- `references/technology-lifecycle.md` -> критерии статусов технологий.
- `references/implementation-done-definition.md` -> done definition и post-implementation checks.
- `references/role-selection-matrix.md` -> выбор роли или связки ролей.
- `references/skill-quality.md` -> чеклист качества skills.

## Формат ответа

Когда обновляешь локальные стандарты, верни: что меняется, где закреплено, какие skills обновлены и как проверить улучшение.
