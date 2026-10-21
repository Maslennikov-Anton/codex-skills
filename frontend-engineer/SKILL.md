---
name: frontend-engineer
description: "Реализовывать веб-интерфейсы: компоненты, состояние, API-интеграция, UX на уровне кода, производительность и качество frontend-кода."
---

# Frontend-разработчик

Используй этот skill, когда нужно именно реализовать или изменить интерфейс в коде, а не проектировать UX-концепт отдельно от реализации.

## Workflow

1. Уточни пользовательский сценарий, ограничения дизайна и контракт API.
2. Изучи текущую UI-архитектуру, design system и conventions проекта.
3. Построй компонентное решение с понятным состоянием и потоками данных.
4. Проверь loading, empty, error и success states.
5. Проверь измененные states и пользовательский путь, затем существующие lint/tests по `verification-before-completion` и self-review. Достаточные результаты того же состояния не повторяй.

## Какие references открывать

Открывай references только когда задача требует глубокой UI/frontend guidance или ты заблокирован.

- Практики реализации и modern frontend checklist:
  [references/implementation-practices.md](references/implementation-practices.md)
- UI quality: responsive, accessibility, states и performance:
  [references/ui-quality-checklist.md](references/ui-quality-checklist.md)

## Базовые правила

- Сохраняй визуальный язык проекта, если пользователь не просит редизайн.
- Учитывай мобильные размеры экрана и клавиатурную доступность по умолчанию.
- При async UI проверь устаревшие ответы, повторный submit и unmount; не добавляй новый state manager ради локальной правки.
- Если задача сводится к flow, wireframes или handoff без кодовой реализации, используй `product-designer`.

## Формат ответа

Укажи измененный пользовательский путь и проверенные состояния. Отделяй фактически проверенные responsive/accessibility свойства от предположений.

## Связь с локальными стандартами

Если задача касается общего инженерного стандарта фронтенда или нового стека команды, дополнительно используй `team-engineering-style`.

Если нужен сильный визуальный и UX-фокус до реализации, дополнительно используй `product-designer`.
