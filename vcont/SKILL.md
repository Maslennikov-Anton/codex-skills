---
name: vcont
description: "Use for VCont runtime behavior: vcontcfg, fboot/XML load commands, logs, licensing, HSB, Modbus/OPC UA/Profibus semantics, runtime tests."
---

# VCont

Используй этот skill для задач вокруг VCont runtime: конфигурация, `vcont.fboot`, XML-команды IDE, ФБ, Modbus, OPC UA, Profibus/PRBDEV runtime-семантика, Hot Standby/HSB, синхронизация, лицензирование, логи и автотесты. Runtime-facing сведения из VC024SA.B сохранены внутри skill в `references/vc024sa-runtime-contract.md`; внешний DOCX не нужен. Полная пользовательская/GUI-документация VCStudio живет в `vcstudio` skill; общий контракт связки - в `references/studio-vcont-contract.md`.

## Workflow

1. Определи область и открой только нужный reference:
   - `references/index.md` -> карта reference-файлов; открывай первой, если не очевидно, какой файл нужен.
   - `references/studio-vcont-contract.md` -> общий handoff contract Studio(front)/VCont(back): ownership, lifecycle, object mapping, load semantics, зависимые пользовательские ST FB, online operations, Modbus/OPC UA, HSB boundary.
   - `references/vc024sa-runtime-contract.md` -> runtime-facing контракт из VC024SA.B: связь VCStudio/VCont, bootfile, task/order semantics, online load effects, Modbus/OPC UA runtime blocks and caveats.
   - `references/standard-blocks.md` -> фактическая VCont-семантика стандартных runtime-ФБ; открывай для `CTUD`, его level-driven `CU`/`CD`, приоритетов `R`/`LD` и корректных тестовых импульсов.
   - Конфигурация и протокол: `references/config.md`, `references/runtime-options.md`, `references/protocol.md`, `references/bootfile-patterns.md`.
   - Протоколы и runtime-семантика: `references/modbus.md`, `references/profibus.md`.
   - HSB и диагностика: `references/hot-standby.md`, `references/synchronization.md`, `references/logs.md`, `references/hsb-local-commands.md`.
   - Лицензии и сценарии: `references/licensing.md`, `references/test-cases.md`.
2. Если задача пришла из пользовательских шагов Studio, `.vcsys`, GUI, Preferences, ST-редактора, UserLibrary, monitoring/forcing UI или backup/history, используй `vcstudio` skill. В `vcont` skill оставляй только то, что влияет на runtime contract, generated `vcont.fboot`, TCP XML-команды, логи, tests или фактическое поведение VCont.
3. Если работаешь с локальными артефактами, сначала изучи текущий repo/package layout. В HSB-инфре актуальный runtime обычно приходит как `vcont.lin.x86_64.deb` и распаковывается в `.work/vcont-runtime/vcontN/vcont-lin.x86_64-arch`.
4. `vcont.fboot` трактуй как обязательный текстовый bootfile XML-команд IDE рядом с бинарником. VCStudio создает его как набор команд загрузки, который runtime читает при старте для создания базы алгоритмов. Порядок `FB`/`CREATE FB` семантически важен; не сортируй и не переставляй команды ради читаемости.
5. Для Docker-проверок по умолчанию используй Ubuntu 24.04. Ubuntu 22.04 не baseline для актуальных бинарников из-за требований `glibc`/`libstdc++`, если задача явно не про обратную совместимость.
6. Для trial/demo сначала классифицируй пакет:
   - Trial Lite (`tria-lite`): 30 минут, `vcont.fboot` запрещен.
   - Demo / Trial Full (`tria-full`): 24 часа, OPC UA, лимит 15 I/O, `vcont.fboot` допускается.
7. Для задач именно в `/home/ant/IdeaProjects/vcont-autotests` сначала изучи структуру, fixtures, helpers, стиль и команды. Для разных программ подменяй `vcont.fboot` fixture-ом перед стартом контейнеров, а не собирай отдельный Docker image на каждый тест.
8. Для ST->Lua/Studio compatibility claims проверяй load into VCont and IDE `READ` oracle; успешная генерация Lua сама по себе не доказывает runtime compatibility. Ограничения ST syntax и translator semantics (`pragma`, non-ASCII identifiers, `AT %`, `VAR_GLOBAL`/`VAR_EXTERNAL`, nested arrays) принадлежат `vcstudio` skill и его ST language reference; в VCont диагностируй только load/runtime часть контракта.
   Для вложенного пользовательского ST FB проверяй, что все зависимые `FBType` созданы до `START`: успешный `CREATE` родительского типа не доказывает разрешение зависимости во время `execute`.
9. Сохраняй терминологию: VCont/ВК, VCStudio, VCSystem, PLC/PlcId, HSB_MAIN, HSB_RESERVE, HSB_STANDALONE, `HSBSTATUS`, `MAIN`, `RESERVE`, `STANDALONE`, `NONE`, heartbeat, таск, луп, контур управления, ФБ, internal build, licensed/runtime license, Trial Lite, Demo / Trial Full, no-license, `license.bin`, `data.bin`, `ControllerId`, `VARS`, `CopiesMBServer`.
10. Факты из `references/` считай продуктовыми требованиями, а не доказательством поведения текущих бинарников. Реализацию проверяй отдельно по бинарникам, конфигам, логам или тестам.

## Core Model

- Runtime ищет `vcontcfg.json` рядом с бинарником, если конфиг не задан явно.
- VCStudio подключается к resource по IP/port из свойств resource; порт VCont по умолчанию в VC024SA.B указан как `61499`.
- Licensed/runtime сборка обычно должна проходить license verification и поддерживать `vcont.fboot`; trial modes отличаются, см. `references/licensing.md`.
- HSB синхронизирует рабочие данные, но не проект: ФБ, связи и таски должны быть загружены во все инстансы, обычно через bootfile каждого узла.
- Для failover-тестов проверяй непрерывность по синхронизируемым DI/DO конкретных ФБ, а не по внутреннему event-task контексту.
- HSB role election сначала фильтрует кандидатов по готовности/ошибкам/checksum, затем сравнивает heartbeat `count`, потом `PlcId`, потом node `id`; не своди выбор MAIN только к большему `PlcId` или uptime.
