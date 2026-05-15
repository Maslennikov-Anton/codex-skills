---
name: vcont
description: "Работать с VCont runtime: vcontcfg.json, vcont.fboot, XML-команды IDE, функциональные блоки, Modbus, Hot Standby/HSB, синхронизация, лицензирование/trial, логи и автотесты."
---

# VCont

Используй этот skill для задач вокруг VCont runtime: конфигурация, загрузочный `vcont.fboot`, XML-команды IDE, функциональные блоки, Modbus, Hot Standby/HSB, синхронизация между контроллерами, лицензирование/trial-сборки, диагностика по логам и автотесты. Canonical-знания зафиксированы в `references/`; внешние исходные документы могут отсутствовать.

## Рабочий процесс

1. Определи область задачи:
   - Конфигурация runtime, значения по умолчанию `vcontcfg.json`, HSB-параметры и общие runtime-настройки: читай `references/config.md`.
   - Протокол VCStudio/VCont, `vcont.fboot`, подписанный `fboot`, `LOADFILE`/`EXECBOOT`, `AUTH`, роли сессии, XML-команды IDE, создание ФБ, связей, тасков и назначение лупов: читай `references/protocol.md`.
   - Встроенный Modbus TCP server, alias-регистры, `MBREAD`/`MBWRITE`, `modbusbatch` и `modbus_async`: читай `references/modbus.md`.
   - Hot Standby: автомат HSB-состояний, failover, heartbeat, поведение MAIN/RESERVE/STANDALONE: читай `references/hot-standby.md`.
   - Peer-to-peer TCP-канал между контроллерами, модель синхронизации данных и Docker/eCAL: читай `references/synchronization.md`.
   - Диагностика по `vcont.log`, признаки загрузки bootfile, HSB-ролей, heartbeat, sync и ограничения логов как oracle для тестов: читай `references/logs.md`.
   - Лицензирование, internal/licensed/trial-lite/demo-trial-full/no-license поставки, лимиты, license.bin/data.bin, TPM/UUID и отличия bootfile-поведения: читай `references/licensing.md`.
   - Повторяемые тест-кейсы VCont/HSB, включая 3-минутный failover-мониторинг через IDE `READ`: читай `references/test-cases.md`.
   - Автотесты с разными программами VCont: храни варианты `vcont.fboot` в тестовых ресурсах и копируй нужный bootfile в runtime-директории через fixture перед стартом контейнеров.
   - Не опирайся на наличие внешних документов: работай по `references/` как по сохраненной базе знаний.
2. При редактировании или тестировании локальных артефактов проекта сначала изучи текущий репозиторий. Сейчас в проекте нет очевидного дерева исходников приложения; обычно доступны артефакты поставки VCont, конфиги, bootfile, логи и тесты.
3. Если встречается файл `vcont.fboot`, трактуй его как обязательный bootfile VCont для обычной/licensed runtime-проверки: файл с таким именем кладётся рядом с бинарником VCont перед запуском, runtime считывает его при старте и запускает описанную в нём пользовательскую программу. Содержимое `vcont.fboot` — текстовый сценарий XML-команд IDE (`Request`, `FB`, `Connection`, `Alias`, `ASSIGN`, `START`), а не бинарная прошивка.
   - Порядок команд создания ФБ в `vcont.fboot` семантически важен: он задаёт исходную очередность запуска/исполнения блоков внутри лупа. Не сортируй и не переставляй `FB`-команды ради читаемости или нормализации; при генерации bootfile располагай зависимые ФБ в нужной последовательности или явно меняй порядок через `ASSIGN` с `Before`.
4. Для Docker-проверок VCont используй базовый образ Ubuntu 24.04. Это общий baseline для актуальных VCont-поставок, а не отдельное правило для trial. Не используй Ubuntu 22.04 как рабочую среду по умолчанию: актуальные бинарники требуют свежие `glibc`/`libstdc++`, и на 22.04 возможны ошибки загрузчика вида `GLIBC_2.38`, `GLIBC_2.36` или `GLIBCXX_3.4.32 not found`.
5. Для trial/demo-сборок сначала классифицируй пакет: `trial-lite` (`tria-lite`) - 30 минут и запрет `vcont.fboot`; `trial-full` (`tria-full`) - demo, 24 часа, OPC UA, лимит 15 I/O и допускает `vcont.fboot`. Не применяй oracle Trial Lite к Demo / Trial Full.
6. При написании автотестов для VCont ориентируйся на уже готовый проект автотестов VCont: `/home/ant/IdeaProjects/vcont-autotests`. Сначала изучи его структуру, фикстуры, helpers, стиль тестов и команды запуска, затем адаптируй существующие подходы под нужный VCont-сценарий.
   - Если тестам нужны разные пользовательские программы, не создавай отдельный Docker image на каждый тест. Используй один базовый image/runtime и подменяй `vcont.fboot` перед запуском VCont.
   - Для последовательного прогона достаточно каталога вроде `tests/resources/fboot/` и fixture, которая копирует выбранный файл в runtime-директории вида `.work/vcont-runtime/vcontN/vcont-lin.x86_64-arch/vcont.fboot` до `docker compose up`.
   - Если узлам нужны разные программы, fixture принимает mapping по сервисам, например `{"vcont1": "main.vcont.fboot", "vcont2": "reserve.vcont.fboot"}`.
7. Сохраняй закрепленную терминологию: VCont/ВК, PLC/PlcId, HSB_MAIN, HSB_RESERVE, HSB_STANDALONE, heartbeat, таск, луп, функциональный блок (ФБ), internal build, licensed/runtime license, Trial Lite, Demo / Trial Full, no-license режим, `license.bin`, `data.bin`, `ControllerId`, `VARS`, `CopiesMBServer`.
8. Рассматривай факты из `references/` как продуктовые/доменные требования, а не как доказательство, что текущие бинарники их реализуют. Поведение реализации проверяй отдельно, если доступны бинарники, конфиги, логи или тесты.

## Базовая модель

- VCont runtime запускается из поставочного бинарника и конфигурации `vcontcfg.json`; если конфиг не задан явно, runtime ищет `vcontcfg.json` рядом с бинарником.
- Актуальная поставка VCont в локальной HSB-инфре распространяется как Debian-пакет `vcont.lin.x86_64.deb` в каталоге `vcont1/`. Тестовая инфраструктура распаковывает пакет в `.work/vcont-runtime/vcontN/vcont-lin.x86_64-arch` для каждого узла. Старые архивы `.tgz`/`.tar.gz` и распакованные копии runtime в `vcont1/` больше не являются источником правды.
- Актуальная runtime-среда для Docker - Ubuntu 24.04 для всех VCont-поставок. Не используй Ubuntu 22.04 как baseline, если задача явно не про обратную совместимость: актуальные бинарники могут не стартовать из-за требований к версиям `glibc` и `libstdc++`.
- Пользовательская программа VCont может загружаться через файл `vcont.fboot`: он должен называться именно так и лежать рядом с бинарником VCont до запуска, иначе runtime может стартовать без bootfile и писать в лог `No bootfile specified...`.
- `vcont.fboot` задаёт пользовательскую программу через XML-команды IDE: создание ФБ, запись литералов в пины, создание `Connection`/`Alias`, создание и старт ресурсов/тасков. Порядок `CREATE FB` внутри bootfile влияет на исходную очередность запуска/исполнения ФБ внутри лупа; изменение порядка является изменением поведения программы. При загрузке полного проекта из VCStudio для ресурсов формируются `fboot`-файлы; в протокольной модели они подписываются на стороне VCStudio и валидируются на стороне VCont.
- Licensed/runtime сборка должна проходить проверку лицензии и поддерживать запуск с `vcont.fboot`, если это не ограничено конкретной лицензией или конфигурацией; в логах ожидается подтверждение вида `Verification was completed successfully. License type - runtime`.
- Trial Lite и Demo / Trial Full - разные модели. Trial Lite ограничен 30 минутами и не грузит `vcont.fboot`; Demo / Trial Full ограничен 24 часами и 15 точками I/O, но может грузить и исполнять `vcont.fboot`; см. `references/licensing.md`.
- Modbus в VCont включает встроенный `MBSERVER` и клиентские ФБ `MBREAD`/`MBWRITE`; для асинхронного клиента используется режим `modbus_async`, для синхронного - `modbusbatch`.
- Hot Standby использует два или три инстанса VCont. В каждый момент времени только один активный контроллер должен управлять процессом; остальные находятся в резерве.
- Контроллеры в HSB обмениваются heartbeat-данными: диагностикой, текущим HSB-режимом, номером итерации рабочего цикла и `PlcId`.
- HSB-синхронизация передает только данные работы, а не проект: контуры, таски, ФБ и связи не реплицируются между VCont. Пользовательскую программу нужно загрузить во все инстансы VCont, обычно положив нужный `vcont.fboot` рядом с каждым бинарником до запуска.
- Практическое ограничение: HSB не синхронизирует состояние событийных тасков как самостоятельную сущность. Для failover-тестов непрерывность нужно проверять по синхронизируемым DI/DO конкретных ФБ, а не ожидать, что резервный VCont продолжит внутренний event-task контекст.
- `PlcId` используется как приоритет, когда нескольким контроллерам нужно детерминированно выбрать MAIN; большее значение `PlcId` побеждает.

## Зафиксированные знания

Подробности разнесены по reference-файлам. Не требуй внешние документы при будущих задачах:

- `references/protocol.md`: протокол VCStudio/VCont, подписанный `fboot`, `LOADFILE`/`EXECBOOT`, `AUTH`, `UseAuth`, роли сессии, XML-команды IDE.
- `references/hot-standby.md`: режимы Hot Standby, heartbeat, failover, схема 1+1 и 1+2.
- `references/synchronization.md`: peer-to-peer канал, Master/Slave-модель, синхронизация ФБ, Docker/eCAL.
- `references/logs.md`: практическая диагностика `vcont.log`, полезные паттерны, HSB/bootfile assertions и ограничения логов.
- `references/licensing.md`: internal/licensed/trial-lite/demo-trial-full/no-license поведение, `license.bin`/`data.bin`, TPM/UUID, `VARS`, `CopiesMBServer`, bootfile behavior, TestOps case ids.
- `references/test-cases.md`: повторяемые тестовые сценарии, параметры прогонов, oracle и известные ловушки тестового клиента.
- `references/config.md`: значения по умолчанию и смысл параметров `vcontcfg.json`.
- `references/modbus.md`: встроенный `MBSERVER`, alias-регистры, async `MBREAD`/`MBWRITE`, `modbusbatch`, `modbus_async`, ограничения и ошибки.
