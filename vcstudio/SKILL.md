---
name: vcstudio
description: "Use for VCStudio GUI/project/docs and Studio-bundled ST-to-Lua translator tasks: .vcsys, hierarchy, library, ST editor, translator limitations, load/monitoring UI, Studio-generated fboot; skip runtime-only VCont debug."
---

# VCStudio

Используй этот skill для задач вокруг среды разработки VCStudio: создание и сопровождение проектов, настройка ресурсов, задач и контуров управления, работа с библиотекой ФБ, Structured Text, загрузка алгоритмов в VCont, мониторинг, форсирование, Modbus/OPC UA-конфигурация через интерфейс Studio.

База знаний самодостаточна: полное извлеченное содержание актуального PDF `Руководство_правки_июнь.pdf` (`VC024SA.B Руководство разработчика по VCStudio_Ред_7_05_26(1).docx`, создан 2026-06-25) встроено в `references/vc024sa-complete.md`, а навигация по нему - в `references/vc024sa-section-map.md`. Внешний PDF/DOCX для ответов не требуется. Факты из reference-файлов считай продуктовой документацией; поведение конкретного runtime или сборки Studio проверяй отдельно на локальных артефактах.

## Workflow

1. Определи область и открой только нужный reference:
   - `references/index.md` -> карта reference-файлов; открывай первой, если не очевидно, какой файл нужен.
   - `references/studio-vcont-contract.md` -> общий handoff contract Studio(front)/VCont(back): ownership, lifecycle, object mapping, load semantics, online operations, Modbus/OPC UA, HSB boundary.
   - `references/vc024sa-key-facts.md` -> плотная самодостаточная база по VC024SA.B: все основные требования, UI-команды, ST, загрузка, monitoring, Modbus/OPC UA, caveats.
   - `references/vc024sa-section-map.md` -> карта полного встроенного текста VC024SA.B; открывай перед поиском редких деталей.
   - `references/vc024sa-complete.md` -> полный embedded extract VC024SA.B с параграфами и таблицами; открывай для исчерпывающих ответов, точных подписей, таблиц, UI labels и спорных формулировок.
   - `references/project-workflow.md` -> проект `.vcsys`, workspace, авторизация, системные логи, backup/history, иерархия `Project -> Device -> Resource -> Application -> Loop`, задачи, ФБ, связи, порядок выполнения.
   - `references/fb-typelibrary.md` -> verified local VCStudio typelibrary из `/home/ant/IdeaProjects/vcstudio`: формат `.fbt`, source counts, runtime mapping, guardrails, high-value communication blocks; открывай при вопросах про входы/выходы/порты/типы ФБ.
   - `references/fb-typelibrary-catalog.md` -> полный generated snapshot всех 473 `.fbt` интерфейсов ФБ; не открывай целиком без необходимости, сначала ищи блок через `rg` по имени.
   - `references/source-repo-map.md` -> verified local VCStudio source repo map: Tycho build, product packaging, plugins/features/tests, custom `ru.isource.*` bundles, EMF model, DTO/JSON layer, CI/release; открывай при вопросах про устройство проекта, сборку, исходники, product packaging или gaps между документацией и кодом.
   - `references/st-language.md` -> Structured Text в VCStudio: editor grammar vs translator grammar, Studio wrapper paths, interfaceSpec/index rules, ST->Lua codegen profile, известные ограничения транслятора, user ST FB vs ST loop behavior.
   - `references/loading-monitoring.md` -> запуск VCont из Studio, full/online load command streams, ST/Lua instance creation, protocol framing, Watch monitoring, live writes, forcing, manual event trigger.
   - `references/communications.md` -> настройка Modbus Serial/TCP, runtime `Options` mirror, публикация портов ФБ в Modbus memory, `MBREAD_PACK`/`MBWRITE_PACK`, diagnostic blocks, OPC UA `CLIENT`/`SUBSCRIBE`/`PUBLISH`.
2. Если вопрос может относиться к мелкой детали документа VC024SA.B, сначала ищи в тематическом reference, затем в `references/vc024sa-complete.md`. Этот skill должен уметь отвечать сам, без обращения к исходному PDF/DOCX. Если вопрос переходит от Studio intent к фактическому runtime behavior (`vcont.fboot`, TCP XML-команды, logs, HSB, лицензирование, trial/demo behavior, автотесты), используй `references/studio-vcont-contract.md` и при необходимости `vcont` skill.
3. При переносе операций Studio в автоматизацию всегда восстанавливай runtime-семантику:
   - иерархия Studio: resource contains applications, applications contain control loops;
   - каждый контур должен быть назначен periodic или event task;
   - order ФБ важен: неявно по добавлению, явно через свойства/order calculation, в `vcont.fboot` через порядок `CREATE` или `ASSIGN Before`;
   - загрузка ресурса/приложения/КУ и создание `vcont.fboot` должны заканчиваться `START` для всех соответствующих задач;
   - онлайн-загрузка КУ не должна сбрасывать текущие значения на начальные.
4. Для GUI-инструкций сохраняй русские названия объектов и команд из Studio: `Структура системы`, `Свойства`, `Библиотека`, `Консоль загрузки`, `Загрузить`, `Онлайн загрузить КУ`, `Онлайн удалить КУ`, `Создать файл загрузки`, `Формирование FBOOT-файла`, `Создать и загрузить файл загрузки`, `Подключиться к ресурсу`, `Мониторинг`, `Форсировать`, `Отключить форсирование`, `TriggerEvent`.
5. Документация содержит опечатки и местами противоречивые формулировки; в актуальном PDF оглавление отстает от фактической нумерации body после вставки раздела ST. Для разделов `6.7+` опирайся на `vc024sa-section-map.md` и фактические заголовки в `vc024sa-complete.md`, а не только на оглавление. Если значение критично для кода или теста, сверяй с generated `vcont.fboot`, логами, typelibrary, поведением текущей сборки Studio/runtime.
6. Для ST->Lua/Studio compatibility claims standalone перевод не считается достаточным: Lua должен загружаться в VCont и проверяться через Studio-like Watch monitoring; direct `READ` можно использовать только как явно помеченный runtime oracle.
7. Перед генерацией, переносом или исправлением ST проверь `Known ST->Lua Translator Limitations` в `references/st-language.md`. Не выдавай распознанный parser token или созданный Lua-файл за поддержку общей памяти, адресной привязки или сложной структуры данных.

## Core Model

- VCSystem состоит из VCStudio как среды разработки и VCont как исполняемой среды Soft PLC.
- Проект VCStudio - единое адресное пространство устройств, ресурсов и логических схем управления; в одном экземпляре VCStudio открыт один проект.
- Resource в Studio содержит IP/port подключения к VCont. Порт VCont по умолчанию в документе: `61499`.
- В актуальном body документа ST находится в разделе `6.7`, запуск VCont - `6.8`, offline operations - `6.9`, online resource operations - `6.10`, monitoring - `6.11`.
- Periodic task исполняет ФБ циклически с заданным периодом; event task исполняет ФБ по событийным входам. Если удалить period у cyclic task, задача становится событийной.
- Для periodic loop порядок ФБ может быть задан добавлением, свойствами блока или командой расчета порядка. Для event loop порядок задается цепочкой event-связей; разветвления событий дают неопределенность, замыкания могут загрузить ресурс на 100%.
- `vcont.fboot` - набор команд загрузки, который runtime читает при старте для создания базы алгоритмов.
- Runtime package/licensing can change bootfile behavior: VCont Trial Lite does not support `vcont.fboot` autoload, while Demo / Trial Full can. For trial/demo/licensing questions use the VCont licensing reference through the shared contract.
- Offline full load записывает начальные значения параметров в базу контроллера и обеспечивает cold start при следующем подключении.
- Online operations выполняются только при подключенном ресурсе; force и live value write влияют на реальный алгоритм.
