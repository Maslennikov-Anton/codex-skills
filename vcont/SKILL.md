---
name: vcont
description: "Работать с VCont runtime: vcontcfg.json, vcont.fboot, XML-команды IDE, функциональные блоки, Modbus, OPC UA, Profibus/PRBDEV runtime-семантика, Hot Standby/HSB, синхронизация, лицензирование/trial, логи и автотесты."
---

# VCont

Используй этот skill для задач вокруг VCont runtime: конфигурация, `vcont.fboot`, XML-команды IDE, ФБ, Modbus, OPC UA, Profibus/PRBDEV runtime-семантика, Hot Standby/HSB, синхронизация, лицензирование, логи и автотесты. Runtime-facing сведения из VC024SA.B сохранены внутри skill в `references/vc024sa-runtime-contract.md`; внешний DOCX не нужен. Полная пользовательская/GUI-документация VCStudio живет в `vcstudio` skill; общий контракт связки - в `references/studio-vcont-contract.md`.

## Workflow

1. Определи область и открой только нужный reference:
   - `references/index.md` -> карта reference-файлов; открывай первой, если не очевидно, какой файл нужен.
   - `references/studio-vcont-contract.md` -> общий handoff contract Studio(front)/VCont(back): ownership, lifecycle, object mapping, load semantics, online operations, Modbus/OPC UA, HSB boundary.
   - `references/vc024sa-runtime-contract.md` -> runtime-facing контракт из VC024SA.B: связь VCStudio/VCont, bootfile, task/order semantics, online load effects, Modbus/OPC UA runtime blocks and caveats.
   - `references/config.md` -> `vcontcfg.json`, HSB-параметры, runtime defaults.
   - `references/runtime-options.md` -> `Options="name=value ..."` для `MBCLIENTTCP`, `MBCLIENTRTU`, `MBCLIENTRTUOVERTCP`, `MBSERIALPORT`, `MBSERVER`, `EIPDEV`, `KNXDEV`, `PRBDEV`.
   - `references/protocol.md` -> VCStudio/VCont protocol, `vcont.fboot`, `LOADFILE`/`EXECBOOT`, `AUTH`, `HSBSTATUS`, XML-команды IDE, ФБ, связи, таски, лупы.
   - `references/modbus.md` -> `MBSERVER`, `MBCLIENT*`, `HsbAlg`, alias-регистры, Modbus memory map, `MBREAD`/`MBWRITE`, `MBREAD_PACK`/`MBWRITE_PACK`, diagnostic blocks, `modbusbatch`, `modbus_async`, OPC UA runtime-facing ID formats.
   - `references/profibus.md` -> Profibus/PRBDEV тестовая инфра, PTY slave emulator, closed `librtprofibus.a` caveats, counter journal oracle для HSB.
   - `references/hot-standby.md` -> HSB-состояния, `HSBSTATUS`, `GlobalModeManager`, checksum `vcont.fboot`, `HBModeSource`, выбор роли, поведение компонентов при потере активной роли.
   - `references/synchronization.md` -> peer-to-peer TCP, `SyncManager`, ELET full/partial sync packets, Docker/eCAL.
   - `references/logs.md` -> `vcont.log`, bootfile/HSB/heartbeat/sync diagnostics, ограничения логов как oracle.
   - `references/licensing.md` -> internal/licensed/trial-lite/demo-trial-full/no-license, `license.bin`, `data.bin`, TPM/UUID, bootfile behavior.
   - `references/test-cases.md` -> повторяемые сценарии VCont/HSB, включая 3-минутный failover через IDE `READ`.
   - `references/hsb-local-commands.md` -> локальный `vcont-hsb` stand, prepare/start/test/log/report команды и известные порты.
   - `references/bootfile-patterns.md` -> минимальные `vcont.fboot` skeletons, порядок ФБ, таск/луп, HSB/Modbus-oriented patterns.
2. Если задача пришла из пользовательских шагов Studio, `.vcsys`, GUI, Preferences, ST-редактора, UserLibrary, monitoring/forcing UI или backup/history, используй `vcstudio` skill. В `vcont` skill оставляй только то, что влияет на runtime contract, generated `vcont.fboot`, TCP XML-команды, логи, tests или фактическое поведение VCont.
3. Если работаешь с локальными артефактами, сначала изучи текущий repo/package layout. В HSB-инфре актуальный runtime обычно приходит как `vcont.lin.x86_64.deb` и распаковывается в `.work/vcont-runtime/vcontN/vcont-lin.x86_64-arch`.
4. `vcont.fboot` трактуй как обязательный текстовый bootfile XML-команд IDE рядом с бинарником. VCStudio создает его как набор команд загрузки, который runtime читает при старте для создания базы алгоритмов. Порядок `FB`/`CREATE FB` семантически важен; не сортируй и не переставляй команды ради читаемости.
5. Для Docker-проверок по умолчанию используй Ubuntu 24.04. Ubuntu 22.04 не baseline для актуальных бинарников из-за требований `glibc`/`libstdc++`, если задача явно не про обратную совместимость.
6. Для trial/demo сначала классифицируй пакет:
   - Trial Lite (`tria-lite`): 30 минут, `vcont.fboot` запрещен.
   - Demo / Trial Full (`tria-full`): 24 часа, OPC UA, лимит 15 I/O, `vcont.fboot` допускается.
7. Для автотестов сначала изучи `/home/ant/IdeaProjects/vcont-autotests`: структуру, fixtures, helpers, стиль и команды. Для разных программ подменяй `vcont.fboot` fixture-ом перед стартом контейнеров, а не собирай отдельный Docker image на каждый тест.
8. Сохраняй терминологию: VCont/ВК, VCStudio, VCSystem, PLC/PlcId, HSB_MAIN, HSB_RESERVE, HSB_STANDALONE, `HSBSTATUS`, `MAIN`, `RESERVE`, `STANDALONE`, `NONE`, heartbeat, таск, луп, контур управления, ФБ, internal build, licensed/runtime license, Trial Lite, Demo / Trial Full, no-license, `license.bin`, `data.bin`, `ControllerId`, `VARS`, `CopiesMBServer`.
9. Факты из `references/` считай продуктовыми требованиями, а не доказательством поведения текущих бинарников. Реализацию проверяй отдельно по бинарникам, конфигам, логам или тестам.

## Core Model

- Runtime ищет `vcontcfg.json` рядом с бинарником, если конфиг не задан явно.
- VCStudio подключается к resource по IP/port из свойств resource; порт VCont по умолчанию в VC024SA.B указан как `61499`.
- Licensed/runtime сборка обычно должна проходить license verification и поддерживать `vcont.fboot`; trial modes отличаются, см. `references/licensing.md`.
- HSB синхронизирует рабочие данные, но не проект: ФБ, связи и таски должны быть загружены во все инстансы, обычно через bootfile каждого узла.
- Для failover-тестов проверяй непрерывность по синхронизируемым DI/DO конкретных ФБ, а не по внутреннему event-task контексту.
- HSB role election сначала фильтрует кандидатов по готовности/ошибкам/checksum, затем сравнивает heartbeat `count`, потом `PlcId`, потом node `id`; не своди выбор MAIN только к большему `PlcId` или uptime.
