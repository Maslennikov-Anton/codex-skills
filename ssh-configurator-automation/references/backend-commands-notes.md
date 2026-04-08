# Backend Commands Spec

Источник backend-контракта приложения:

- JSON-спека: [backend-commands.json](backend-commands.json)
- исходный файл пользователя: `/home/ant/Загрузки/commands.json`

## Что Это Даёт

- точный список backend-команд
- описание аргументов и их типов
- дефолтные значения для необязательных аргументов
- `allowed_server_types` для части команд
- примеры `happy_path` и `unhappy_path`

## Быстрые Факты

- всего команд в спеке: `83`
- команд с `allowed_server_types`: `40`
- упоминания типов хостов:
  - `Virt-Server`: `30`
  - `Runtime-VM`: `11`
  - `Runtime-Server`: `12`

## Практическая Роль В Skill

- считать `backend-commands.json` более сильным источником истины, чем только `views/*.vue`
- использовать JSON-спеку для:
  - проверки допустимости команды на текущем типе хоста
  - проверки количества и типов аргументов
  - отделения backend-возможностей от того, что просто отрисовано в UI
  - уточнения destructive / mutating / safe-read сценариев

## Ограничения

- не у каждой команды в спеке есть `allowed_server_types`
- наличие команды в JSON не гарантирует, что она реально доступна на конкретном хосте
- итоговую операционную правду всё равно проверять через:
  - UI action
  - console evidence
  - живой backend response

## Как Использовать Дальше

При расширении skill-а:

1. Сначала смотреть `backend-commands.json`
2. Затем сверять с `views/*.vue`
3. Затем подтверждать поведением через `assert-command` / console evidence

Это даёт правильную тройку источников:

- backend spec
- UI wiring
- runtime evidence
