---
name: vcstudio
description: "Use for VCStudio GUI/project/docs and Studio-bundled ST-to-Lua translator tasks: .vcsys, hierarchy, library, ST editor, translator limitations, load/monitoring UI, Studio-generated fboot; skip runtime-only VCont debug."
---

# VCStudio

Используй skill для проектирования и сопровождения VCStudio: проекты `.vcsys`, ресурсы, приложения, контуры, задачи, библиотека ФБ, Structured Text, загрузка в VCont, мониторинг и Studio-конфигурация Modbus/OPC UA.

## Быстрая маршрутизация

1. Открой `references/index.md` и выбери минимальный набор тематических файлов.
2. Для ST-кода, генерации тестов и ST->Lua compatibility обязательно открой `references/st-language.md`.
   Для пользовательских ST-блоков, содержащих экземпляры других пользовательских ST-блоков, используй раздел `Композиция зависимых пользовательских ST FB`: не объединяй типы в один translator input.
3. Для границы Studio/VCont, фактического исполнения, логов и runtime oracle начни с `references/studio-vcont-contract.md`; runtime-only диагностику передай skill `vcont`.
4. Для редкой или спорной детали руководства сначала используй `references/vc024sa-key-facts.md`, затем `references/vc024sa-section-map.md`; `references/vc024sa-complete.md` открывай только в нужном диапазоне.
5. Для интерфейса конкретного ФБ сначала открой `references/fb-typelibrary.md`, затем найди имя через `rg` в большом generated-каталоге `references/fb-typelibrary-catalog.md`.
6. Для создания проекта, загрузки/мониторинга и настройки протоколов используй соответственно `references/project-workflow.md`, `references/loading-monitoring.md` и `references/communications.md`.
7. Для исходников, сборки и product packaging используй `references/source-repo-map.md`.

## Рабочие правила

- Разделяй пять уровней доказательства: ST editor grammar, Studio interface/wrapper, ST->Lua translation, VCont load и runtime behavior. Parse, exit code `0` или созданный Lua сами по себе не доказывают поддержку конструкции.
- Для Studio-compatible ST проверяй весь путь `VCStudio -> ST->Lua -> Lua FBType -> VCont`; наблюдай результат через Studio-like Watch. Direct `READ` допустим только как явно помеченный runtime oracle.
- Перед созданием или исправлением ST всегда сверяй `Known ST->Lua Translator Limitations`; не сохраняй известное ограничение как expected-positive тест.
- Различай один translator input и весь Studio-проект: один input содержит один top-level `FUNCTION_BLOCK`, но проект может содержать граф зависимых пользовательских ST FB, если каждый тип транслируется отдельно и все типы загружаются до запуска задач.
- В автоматизации сохраняй модель `Resource -> Application -> Loop`: назначай каждый контур periodic/event task, учитывай порядок ФБ и завершай загрузку `START` для соответствующих задач. Online load не должен сбрасывать текущие значения на начальные.
- В GUI-инструкциях используй точные русские подписи из Studio. При расхождении документации с текущей сборкой предпочитай generated `vcont.fboot`, логи, typelibrary и воспроизводимое поведение.
- У актуального руководства устарело оглавление после вставки раздела ST; для разделов `6.7+` используй фактические заголовки из section map/body.
- Не изменяй локальный репозиторий VCStudio или runtime только для ответа на справочный вопрос. Изменения делай лишь по явному запросу пользователя и с проверкой dirty worktree.

## Граница ответственности

- VCStudio владеет моделью проекта, редактором, генерацией конфигурации и пользовательскими load/monitoring операциями.
- VCont владеет исполнением, runtime database, логами, boot behavior, лицензированием и фактической семантикой протоколов.
- Полный текст текущего руководства встроен в references; внешний PDF/DOCX не нужен. Reference-факты являются документационным контрактом, а свойства конкретной версии подтверждай локальными артефактами.
