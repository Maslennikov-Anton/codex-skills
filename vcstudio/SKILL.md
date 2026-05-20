---
name: vcstudio
description: "Работать с VCStudio: проекты .vcsys, иерархия устройство/ресурс/приложение/контур, задачи, ФБ, ST, загрузка vcont.fboot, онлайн-операции, мониторинг, Modbus/OPC UA через Studio, HSB boundary и загрузка каждого узла."
---

# VCStudio

Используй этот skill для задач вокруг среды разработки VCStudio: создание и сопровождение проектов, настройка ресурсов, задач и контуров управления, работа с библиотекой ФБ, Structured Text, загрузка алгоритмов в VCont, мониторинг, форсирование, Modbus/OPC UA-конфигурация через интерфейс Studio.

База знаний самодостаточна: полное извлеченное содержание `VC024SA.B Руководство разработчика VCStudio`, ревизия B, 2025, встроено в `references/vc024sa-complete.md`, а навигация по нему - в `references/vc024sa-section-map.md`. Внешний DOCX для ответов не требуется. Факты из reference-файлов считай продуктовой документацией; поведение конкретного runtime или сборки Studio проверяй отдельно на локальных артефактах.

## Workflow

1. Определи область и открой только нужный reference:
   - `references/index.md` -> карта reference-файлов; открывай первой, если не очевидно, какой файл нужен.
   - `references/studio-vcont-contract.md` -> общий handoff contract Studio(front)/VCont(back): ownership, lifecycle, object mapping, load semantics, online operations, Modbus/OPC UA, HSB boundary.
   - `references/vc024sa-key-facts.md` -> плотная самодостаточная база по VC024SA.B: все основные требования, UI-команды, ST, загрузка, monitoring, Modbus/OPC UA, caveats.
   - `references/vc024sa-section-map.md` -> карта полного встроенного текста VC024SA.B; открывай перед поиском редких деталей.
   - `references/vc024sa-complete.md` -> полный embedded extract VC024SA.B с параграфами и таблицами; открывай для исчерпывающих ответов, точных подписей, таблиц, UI labels и спорных формулировок.
   - `references/project-workflow.md` -> проект `.vcsys`, workspace, авторизация, системные логи, backup/history, иерархия `Project -> Device -> Resource -> Application -> Loop`, задачи, ФБ, связи, порядок выполнения.
   - `references/st-language.md` -> Structured Text в VCStudio, ST->Lua, пользовательские ФБ, синтаксис, типы, массивы, enum/state-machine patterns.
   - `references/loading-monitoring.md` -> запуск VCont из Studio, offline/online операции, создание/загрузка `vcont.fboot`, cold/warm start, connect, мониторинг, изменение значений, форсирование, ручные события.
   - `references/communications.md` -> настройка Modbus Serial/TCP, runtime `Options` mirror, публикация портов ФБ в Modbus memory, `MBREAD_PACK`/`MBWRITE_PACK`, diagnostic blocks, OPC UA `CLIENT`/`SUBSCRIBE`/`PUBLISH`.
2. Если вопрос может относиться к мелкой детали документа VC024SA.B, сначала ищи в тематическом reference, затем в `references/vc024sa-complete.md`. Этот skill должен уметь отвечать сам, без обращения к исходному DOCX. Если вопрос переходит от Studio intent к фактическому runtime behavior (`vcont.fboot`, TCP XML-команды, logs, HSB, лицензирование, trial/demo behavior, автотесты), используй `references/studio-vcont-contract.md` и при необходимости `vcont` skill.
3. При переносе операций Studio в автоматизацию всегда восстанавливай runtime-семантику:
   - иерархия Studio: resource contains applications, applications contain control loops;
   - каждый контур должен быть назначен periodic или event task;
   - order ФБ важен: неявно по добавлению, явно через свойства/order calculation, в `vcont.fboot` через порядок `CREATE` или `ASSIGN Before`;
   - загрузка ресурса/приложения/КУ и создание `vcont.fboot` должны заканчиваться `START` для всех соответствующих задач;
   - онлайн-загрузка КУ не должна сбрасывать текущие значения на начальные.
4. Для GUI-инструкций сохраняй русские названия объектов и команд из Studio: `Структура системы`, `Свойства`, `Библиотека`, `Консоль загрузки`, `Загрузить`, `Онлайн загрузить КУ`, `Создать файл загрузки`, `Создать и загрузить файл загрузки`, `Подключиться к ресурсу`, `Мониторинг`, `Форсировать`.
5. Документация содержит опечатки и местами противоречивые формулировки. Если значение критично для кода или теста, сверяй с generated `vcont.fboot`, логами, typelibrary, поведением текущей сборки Studio/runtime.

## Core Model

- VCSystem состоит из VCStudio как среды разработки и VCont как исполняемой среды Soft PLC.
- Проект VCStudio - единое адресное пространство устройств, ресурсов и логических схем управления; в одном экземпляре VCStudio открыт один проект.
- Resource в Studio содержит IP/port подключения к VCont. Порт VCont по умолчанию в документе: `61499`.
- Periodic task исполняет ФБ циклически с заданным периодом; event task исполняет ФБ по событийным входам. Если удалить period у cyclic task, задача становится событийной.
- Для periodic loop порядок ФБ может быть задан добавлением, свойствами блока или командой расчета порядка. Для event loop порядок задается цепочкой event-связей; разветвления событий дают неопределенность, замыкания могут загрузить ресурс на 100%.
- `vcont.fboot` - набор команд загрузки, который runtime читает при старте для создания базы алгоритмов.
- Runtime package/licensing can change bootfile behavior: VCont Trial Lite does not support `vcont.fboot` autoload, while Demo / Trial Full can. For trial/demo/licensing questions use the VCont licensing reference through the shared contract.
- Offline full load записывает начальные значения параметров в базу контроллера и обеспечивает cold start при следующем подключении.
- Online operations выполняются только при подключенном ресурсе; force и live value write влияют на реальный алгоритм.
