---
name: vcont
description: "Работать с VCont runtime: vcontcfg.json, vcont.fboot, XML-команды IDE, функциональные блоки, Modbus, Hot Standby/HSB, синхронизация, лицензирование/trial, логи и автотесты."
---

# VCont

Используй этот skill для задач вокруг VCont runtime: конфигурация, `vcont.fboot`, XML-команды IDE, ФБ, Modbus, Hot Standby/HSB, синхронизация, лицензирование, логи и автотесты. `references/` здесь являются сохраненной доменной базой знаний; внешние исходные документы могут отсутствовать.

## Workflow

1. Определи область и открой только нужный reference:
   - `references/config.md` -> `vcontcfg.json`, HSB-параметры, runtime defaults.
   - `references/protocol.md` -> VCStudio/VCont protocol, `vcont.fboot`, `LOADFILE`/`EXECBOOT`, `AUTH`, XML-команды IDE, ФБ, связи, таски, лупы.
   - `references/modbus.md` -> `MBSERVER`, alias-регистры, `MBREAD`/`MBWRITE`, `modbusbatch`, `modbus_async`.
   - `references/hot-standby.md` -> HSB-состояния, MAIN/RESERVE/STANDALONE, heartbeat, failover.
   - `references/synchronization.md` -> peer-to-peer TCP, sync data model, Docker/eCAL.
   - `references/logs.md` -> `vcont.log`, bootfile/HSB/heartbeat/sync diagnostics, ограничения логов как oracle.
   - `references/licensing.md` -> internal/licensed/trial-lite/demo-trial-full/no-license, `license.bin`, `data.bin`, TPM/UUID, bootfile behavior.
   - `references/test-cases.md` -> повторяемые сценарии VCont/HSB, включая 3-минутный failover через IDE `READ`.
   - `references/hsb-local-commands.md` -> локальный `vcont-hsb` stand, prepare/start/test/log/report команды и известные порты.
   - `references/bootfile-patterns.md` -> минимальные `vcont.fboot` skeletons, порядок ФБ, таск/луп, HSB/Modbus-oriented patterns.
2. Если работаешь с локальными артефактами, сначала изучи текущий repo/package layout. В HSB-инфре актуальный runtime обычно приходит как `vcont.lin.x86_64.deb` и распаковывается в `.work/vcont-runtime/vcontN/vcont-lin.x86_64-arch`.
3. `vcont.fboot` трактуй как обязательный текстовый bootfile XML-команд IDE рядом с бинарником. Порядок `FB`/`CREATE FB` семантически важен; не сортируй и не переставляй команды ради читаемости.
4. Для Docker-проверок по умолчанию используй Ubuntu 24.04. Ubuntu 22.04 не baseline для актуальных бинарников из-за требований `glibc`/`libstdc++`, если задача явно не про обратную совместимость.
5. Для trial/demo сначала классифицируй пакет:
   - Trial Lite (`tria-lite`): 30 минут, `vcont.fboot` запрещен.
   - Demo / Trial Full (`tria-full`): 24 часа, OPC UA, лимит 15 I/O, `vcont.fboot` допускается.
6. Для автотестов сначала изучи `/home/ant/IdeaProjects/vcont-autotests`: структуру, fixtures, helpers, стиль и команды. Для разных программ подменяй `vcont.fboot` fixture-ом перед стартом контейнеров, а не собирай отдельный Docker image на каждый тест.
7. Сохраняй терминологию: VCont/ВК, PLC/PlcId, HSB_MAIN, HSB_RESERVE, HSB_STANDALONE, heartbeat, таск, луп, ФБ, internal build, licensed/runtime license, Trial Lite, Demo / Trial Full, no-license, `license.bin`, `data.bin`, `ControllerId`, `VARS`, `CopiesMBServer`.
8. Факты из `references/` считай продуктовыми требованиями, а не доказательством поведения текущих бинарников. Реализацию проверяй отдельно по бинарникам, конфигам, логам или тестам.

## Core Model

- Runtime ищет `vcontcfg.json` рядом с бинарником, если конфиг не задан явно.
- Licensed/runtime сборка обычно должна проходить license verification и поддерживать `vcont.fboot`; trial modes отличаются, см. `references/licensing.md`.
- HSB синхронизирует рабочие данные, но не проект: ФБ, связи и таски должны быть загружены во все инстансы, обычно через bootfile каждого узла.
- Для failover-тестов проверяй непрерывность по синхронизируемым DI/DO конкретных ФБ, а не по внутреннему event-task контексту.
- `PlcId` используется как приоритет детерминированного выбора MAIN: большее значение побеждает.
