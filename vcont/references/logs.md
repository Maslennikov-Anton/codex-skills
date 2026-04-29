# VCont Logs

Практические знания по `vcont.log` получены на Docker-стенде `vcont-hsb` с двумя инстансами VCont и bootfile `complex_counters.vcont.fboot`. Логи полезны как diagnostic oracle для старта, загрузки программы, HSB-ролей, heartbeat и грубого состояния sync. Они не показывают значения внутренних пользовательских ФБ.

## Где искать

- Основной файл обычно лежит рядом с бинарником: `vcont*/.../vcont-lin.x86_64-arch/vcont.log`.
- При ротации рядом могут быть `vcont.1.log`, `vcont.2.log` и т.д.
- Для тестов лучше читать только свежий диапазон после старта теста: запомнить byte-offset файла до `docker compose up`, затем читать `tail -c +<offset+1> vcont.log`.
- `docker compose logs` почти бесполезен для диагностики VCont: stdout может содержать только короткие служебные строки вроде `Registration thread is started`; значимые данные идут в файловый `vcont.log`.

## Формат строки

Типовая строка:

```text
04-29-2026 23:00:21.329037204 [23] DEV_MGR.cpp:82 LOG_INFO vcont Boot file correctly loaded
```

Поля, которые удобно парсить:

- timestamp: дата и время события;
- thread id в квадратных скобках;
- компонент/исходник: например `ForteBootFileLoader.cpp`, `DEV_MGR.cpp`, `elet.cpp`, `heartbeat_service.cpp`, `statistics_manager.cpp`;
- level: `LOG_INFO`, `LOG_DEBUG`, `LOG_TRACE_L1`, `LOG_WARNING`, `LOG_ERROR`;
- message: человекочитаемый текст.

## Загрузка runtime и bootfile

Полезные признаки:

- `runtime is up and running` - процесс runtime дошел до рабочего старта.
- `Using provided bootfile location set in the command line: vcont.fboot` - runtime получил путь к bootfile.
- `Boot file vcont.fboot opened` - файл найден и открыт.
- `createFB: appending <TYPE> to FB list` - bootfile реально создает ФБ; можно грубо проверить набор типов и число созданных ФБ.
- `Boot file correctly loaded` - главный положительный признак успешной загрузки пользовательской программы.
- `Closing bootfile` - загрузчик завершил чтение файла.
- `No bootfile specified...` - runtime стартовал без bootfile; для тестов с программой это ошибка.

Наблюдение: строка `ForteBootFileLoader.cpp:38 LOG_ERROR Error receiving the lua key` может появляться даже при успешной загрузке, если далее есть `createFB...` и `Boot file correctly loaded`, а контейнер не перезапускается. Ее нельзя использовать как самостоятельный fail-критерий без контекста.

## HSB startup/election

Полезные признаки:

- `HSB processing is started. HSB priority: <N>. Period: <ms>` - HSB-обработка запущена, виден приоритет и период.
- `The mode has been changed to: INITIALIZING` - узел вошел в начальную HSB-фазу.
- `Waiting for node discovery before initial election. Deadline: <ms>` - узел ждет discovery перед выборами.
- `Remote node discovered: <uuid>` - peer обнаружен.
- `MAIN candidate: <uuid> (reason: ...)` - механизм выбора MAIN зафиксировал кандидата и причину.
- `The current copy becomes MAIN.` - текущий инстанс стал MAIN.
- `The current copy becomes RESERVE.` - текущий инстанс стал RESERVE.
- `Global mode changed to MAIN|RESERVE|UNKNOWN` - текущая глобальная HSB-роль; очень шумная строка, может повторяться тысячами раз.

Практически для assertions:

- после старта пары должен быть один узел с устойчивым `MAIN` и второй с `RESERVE`;
- `MAIN candidate` и `becomes MAIN/RESERVE` полезны для анализа election/failover;
- `Global mode changed...` лучше агрегировать или брать последние значения, а не проверять каждую строку.

## Heartbeat

Полезные признаки:

- `Heartbeat sent from node: <uuid>. Mode: MAIN|RESERVE|UNKNOWN, Diagnostics: OK, Priority: <N>, Count: <C>` - локальный узел шлет heartbeat; видны режим, диагностика, приоритет и счетчик.
- `Heartbeat received from node: <uuid>. Mode: MAIN|RESERVE|UNKNOWN, Diagnostics: OK, Priority: <N>, Count: <C>` - локальный узел получает heartbeat от peer.
- `Local node changed mode to <MODE>. Priority is <N>` - heartbeat-сервис увидел смену локальной роли.
- `Remote node <uuid> changed mode to <MODE>. Priority is <N>` - heartbeat-сервис увидел смену роли peer.
- `Remote node <uuid> removed due to missed heartbeats` - peer потерян по heartbeat; полезный признак failover или нестабильности сети/процесса.

Практически для assertions:

- на MAIN обычно много `Heartbeat sent ... Mode: MAIN`;
- на RESERVE обычно много `Heartbeat received ... Mode: MAIN`;
- счетчик `Count` должен расти во времени;
- `Diagnostics: OK` можно использовать как быстрый health-признак;
- `missed heartbeats` после стабилизации пары - подозрительный сигнал, если тест не выключает peer намеренно.

## Stop/start, failover и rejoin

Практические наблюдения после 2-минутного сценария с ручным чередованием `docker compose stop/start` каждые 20 секунд:

- `docker compose stop <service>` завершает контейнер штатно: в Docker state видны `exit=0` и `restart=0`. `RestartCount` не растет при ручном stop/start; его можно использовать для поиска crash-loop, но не как счетчик намеренных отключений.
- Каждый `docker compose start <service>` запускает VCont runtime заново. В логах этого узла повторяются `runtime is up and running`, `Boot file vcont.fboot opened`, `Error receiving the lua key`, `Boot file correctly loaded`, `HSB processing is started`.
- При каждом process restart узел получает новый runtime node UUID. Не делай assertions на стабильность UUID между stop/start; используй UUID только внутри одного runtime-жизненного цикла.
- Heartbeat `Count` растет в рамках текущего runtime-жизненного цикла, но после restart может начаться заново вместе с новым UUID. Для тестов проверяй монотонный рост только между соседними строками одного и того же node UUID.
- Живой peer фиксирует отключение остановленного узла строкой `Remote node <uuid> removed due to missed heartbeats`. В сценарии намеренного stop это ожидаемый положительный признак обнаружения потери peer, а не ошибка сама по себе.
- При возврате остановленного peer живой узел снова пишет `Remote node discovered: <uuid>`, а вернувшийся узел отправляет `SYNC_REQUESTED` и `Request for full synchronization...`.
- Если MAIN остановлен, оставшийся узел выбирает MAIN и пишет `MAIN candidate: <own-or-peer-uuid> (...)` и `The current copy becomes MAIN.`.
- Если peer возвращается, когда уже есть явный MAIN, он обычно становится RESERVE: `MAIN candidate: <main-uuid> (reason: explicit MAIN present)` и `The current copy becomes RESERVE.`.
- После rejoin steady-state снова виден как связка: на MAIN идут `Heartbeat sent ... Mode: MAIN`, на RESERVE идут `Heartbeat received ... Mode: MAIN`.
- `Global mode changed to UNKNOWN` может массово появляться во время startup/rejoin. Для assertions лучше отделять transient window после start/stop от stable window после election.

Полезные проверки для failover-теста по логам:

- на отключенном и затем включенном узле bootfile должен загрузиться заново: новая пара `runtime is up and running` + `Boot file correctly loaded`;
- на живом узле после stop peer должен появиться `removed due to missed heartbeats`;
- после start peer должен появиться `Remote node discovered`;
- после отключения MAIN должен появиться `The current copy becomes MAIN.` на оставшемся узле;
- после восстановления пары один узел должен иметь свежие `Heartbeat sent ... Mode: MAIN`, второй - `Heartbeat received ... Mode: MAIN`;
- в stable window после rejoin не должно быть новых неожиданных `LOG_ERROR`, `LOG_WARNING`, `runtime is up and running` или `removed due to missed heartbeats`.

## Sync/statistics

Полезные признаки:

- `Send: SYNC_REQUESTED` - узел отправил запрос синхронизации.
- `Request for full synchronization has been sent (current mode is INITIALIZING|RESERVE)` - отправлен full sync request.
- `Full synchronization timed out after 1000 ms. No fresh sync packet received.` - sync packet не пришел в течение таймаута; на старте может появляться до стабилизации, после стабилизации требует внимания.
- `Size of send data is <N>` - размер данных, которые statistics/sync готовит к отправке.

Наблюдение на программе из локальных ФБ (`BOOL/INT/NOT/AND/CTU/EQ`): в 5-минутном окне `Size of send data is 0` повторялось на обоих узлах, хотя пользовательская программа была загружена и исполнялась. Значит логи не подтверждают передачу значений внутренних ФБ. Если `Size of send data` станет больше нуля в сценариях с Modbus/alias/серверными данными, это можно использовать только как грубый признак наличия передаваемого payload, но не как проверку конкретных значений.

## Ошибки и warnings

Типовые строки, встреченные на старте:

- `Error receiving the lua key` - не считать фатальным само по себе; проверять наличие `Boot file correctly loaded` и отсутствие restart loop.
- `CEventlessExecutionThread::overrun! wakeup lat: ..., loop lat: ...` - задержка eventless execution thread; на старте встречается вместе с initial sync/election, после стабилизации может быть performance-риск.
- `Full synchronization timed out...` - на старте возможен transient, после стабилизации пары подозрителен.

Для тестов полезно разделять:

- startup grace period: допустить отдельные transient warning/error, если затем есть `Boot file correctly loaded`, HSB роли и контейнеры не рестартуют;
- stable window: после grace period отсутствие новых `LOG_ERROR`, `LOG_WARNING`, `missed heartbeats`, `runtime is up and running` повторно.

## Что можно уверенно вытягивать для автотестов

- runtime стартовал: `runtime is up and running`.
- bootfile найден: `Boot file vcont.fboot opened`.
- bootfile загружен: `Boot file correctly loaded`.
- программа создала ФБ: количество и типы `createFB: appending ...`.
- HSB включен: `HSB processing is started...`.
- peer обнаружен: `Remote node discovered...`.
- роли выбраны: `becomes MAIN`, `becomes RESERVE`, либо последние `Global mode changed to ...`.
- heartbeat живой: `Heartbeat sent/received`, `Diagnostics: OK`, растущий `Count`.
- sync request был: `SYNC_REQUESTED`, `Request for full synchronization...`.
- есть/нет грубого sync payload: `Size of send data is <N>`.
- стабильность процесса: отсутствие restart count, отсутствие повторного `runtime is up and running` в stable window, отсутствие поздних `LOG_ERROR/LOG_WARNING`.

## Чего из логов не видно

- Конкретные значения внутренних счетчиков, флагов и пинов ФБ.
- Подтверждение, что значение конкретного пользовательского ФБ было передано на резерв.
- Полная корректность продолжения бизнес-логики после failover.
- Факт загрузки проекта/контуров/ФБ с другого VCont: HSB синхронизирует данные работы, а не проект, поэтому bootfile нужен на каждом инстансе.

Для проверки continuity данных после failover нужен внешний наблюдаемый канал: Modbus server/alias, API/IDE-запросы, диагностические ФБ с выводом в доступную область или другой readback-механизм. `vcont.log` годится для инфраструктурных assertions вокруг старта, HSB и heartbeat, но не для проверки значений пользовательской программы.
