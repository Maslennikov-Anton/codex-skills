# Loading And Monitoring

For the exact handoff from Studio load/monitoring operations into VCont runtime effects, see `studio-vcont-contract.md`.

For ST->Lua integration checks, mirror Studio's load path as closely as possible: create/load the Lua-backed FB type, instantiate it under application/control-loop paths, assign/start the task, then verify through Studio-like Watch monitoring. A direct single-pin `READ` can be an explicitly marked runtime oracle, but it is not the Studio UI monitoring protocol.

## Запуск VCont для отладки из VCStudio

Для загрузки logic и отладки нужно запустить VCont с правами администратора. Окно VCont после запуска закрывать нельзя. После запуска runtime доступен через локальный сетевой адрес, порт по умолчанию `61499`.

Resource в Studio должен иметь IP и port, соответствующие target VCont.

## Offline Operations

Offline operations доступны без подключения к resource:

- удаление объектов структуры, включая project/device/resource/application/control loop;
- удаление project физически удаляет файл проекта `.vcsys`;
- переименование объектов, кроме project name;
- загрузка и выгрузка resource/application/control loop;
- online load/delete control loop commands;
- подключение к resource.

При попытке удаления/переименования в online mode система не меняется. При попытке full load resource/application/control loop в online mode Studio автоматически разрывает подключение к resource.

`Выгрузка` и `Получение значений` в актуальном PDF помечены как functionality in development.

## Full Load

Загрузка алгоритмов в контроллер возможна на уровне resource, application или control loop.

Перед загрузкой убедись, что controller доступен по IP/port из resource properties.

Запуск: контекстное меню объекта -> `Загрузить` или кнопка `Загрузить` на toolbar.

После full load:

- Studio отключается от resource;
- initial values записываются в controller database;
- последующее подключение обеспечивает cold start.

Успешность проверяется в `Консоль загрузки`:

- в конце списка команд есть `START` для всех задач resource/application/loop;
- отсутствуют ошибки.

## Online Load And Delete Control Loop

`Онлайн загрузить КУ` загружает новый или измененный control loop без обновления текущих values на initial values.

Запуск: контекстное меню loop в `Структура системы` или context menu внутри editor области loop.

Успешность: в `Консоль загрузки` есть `START` для всех задач loop и нет ошибок.

Source evidence: branch `VCONT-2056`, `NewHierarchyDeploymentService.java`, `StDeployHelper.java`,
`EthernetDeviceManagementCommunicationHandler.java`, `TLSPSKDeviceManagementCommunicationHandler.java`,
`MonitoringManager.java`.

Full resource deploy flow:

1. connect and send JWT token when auth is enabled;
2. `QUERY` existing FBs;
3. if existing FBs are present and user confirms override, send `KILL` per existing FB and then `DELETE` all FBs;
4. create tasks: blank/`0` interval -> `EMB_RES`; otherwise `TASK_RES Options="Period=<interval> CPU=2"`;
5. create user ST FBTypes before instances;
6. create blocks, aliases, parameters, connections, and OPC aliases;
7. assign periodic loops to tasks;
8. `START` each task by sending `START` to destination `<taskName>`.

Observed local ST load command stream for a periodic user ST FB:

```xml
<Request ID="1" Action="QUERY"> <FB Name="*" Type="*"/> </Request>
mainTask;<Request ID="2" Action="KILL"/>
<Request ID="3" Action="DELETE"><FB Name="*" Type="*" /></Request>
<Request ID="4" Action="CREATE"><FB Name="mainTask" Type="TASK_RES" Options="Period=500 CPU=2" /></Request>
<Request ID="5" Action="CREATE"><FBType Name="TEST" >...lua...</Request>
<Request ID="6" Action="CREATE"><FB Name="APP001.LOOP001.TEST" Type="TEST" Options="LUAENGINE=mainTask"/></Request>
mainTask;<Request ID="7" Action="ASSIGN"><Subcontainer Name="APP001.LOOP001" /></Request>
mainTask;<Request ID="8" Action="START" />
```

ST/load emulation rules:

- `KILL`/`DELETE` appears only after `QUERY` returns existing FBs and the user confirms override.
- `KILL` sends the target FB/resource name as request destination and an XML body `<Request Action="KILL"/>`.
- The XML request body and protocol destination are separate fields; do not prefix the XML string with the task name in the wire frame.
- Console logs may display `destination; <Request...>`; the actual wire frame sends `destination` and XML `request` as two protocol strings.
- `CREATE FBType` body is built as `<Request ...><FBType Name="TEST" >...lua...</Request>` by Studio source. Do not normalize it unless the emulation target intentionally differs from Studio output.
- Periodic task ST/Lua FB instances use `Options="LUAENGINE=<task>"` and empty request destination.
- Event-task ST/Lua FB instances omit `LUAENGINE` and send create/start/write operations to destination `<task>`.
- ST loop mode creates one synthetic runtime FB `<APP>.<LOOP>.ST` of type `ST` with Lua embedded in the `CREATE FB` request.
- User ST FB mode creates `FBType <typeName>` first, then instance `<APP>.<LOOP>.<FB>` of that type.
- Periodic loop assignment sends `<Request Action="ASSIGN"><Subcontainer Name="<APP>.<LOOP>" /></Request>` to destination `<task>`.
- Event-driven loops skip periodic `ASSIGN`.

TCP/TLS framing:

- connect to resource `ip:port`;
- send two IEC strings in order: destination, then XML request;
- each string is tag byte `0x50`, then length, then UTF-8 bytes;
- default non-extended length uses 2-byte `writeShort`; extended length uses 4-byte `writeInt`;
- current VCStudio source routes this through `ExtraPreferences.isUseExtendedLength()` in both Ethernet and TLS-PSK handlers; `USE_EXTENDED_LENGTH` defaults to `true` in `ExtraPreferencesInitializer`;
- extended mode changes even small packets: `sendREQ` contains two length-prefixed strings, so the frame grows by 4 bytes versus regular mode;
- `sendPublicKey()` uses the same length-width switch; raw `sendBytes()` file uploads still write the supplied bytes without adding this IEC string envelope;
- regular mode fits VCont builds expecting 2-byte string lengths; extended mode fits VCont builds compiled with large `CIEC_STRING` / 4-byte ASN.1 string lengths;
- when Studio cannot load/connect after this change, first verify Studio and VCont agree on this length mode before debugging XML command semantics;
- response is one IEC string containing XML response;
- when auth is enabled Studio first sends `<Request Action="AUTH"><Auth Token="<jwt>"/></Request>`.

`Онлайн удалить КУ` удаляет algorithm control loop из runtime. Успешность: в `Консоль загрузки` есть `DELETE` для всех задач loop и нет ошибок.

## Runtime Command Mapping

| Studio command | Runtime/API interpretation | Effect |
|---|---|---|
| `Инициализация переменных` | `INITIALIZE`-class command | Clears warm-start data and restarts with initial values. |
| `Сохранение переменных` | `DBSAVE`-class command | Saves runtime DB/state for warm start; does not save `.vcsys`. |
| `Перезагрузка ресурса` | `REBOOT`-class command | Restarts runtime/service. |
| `Сброс ресурса` | `REMOVERES`-class command | Clears load database, deletes bootfile, restarts with initial values. |

For exact Studio(front)/VCont(back) lifecycle, see `studio-vcont-contract.md`.

## Online Operations

Online operations доступны при подключенном resource через контекстное меню resource.

`Инициализация переменных` очищает warm-start data, перезагружает resource и стартует с initial values.

`Сохранение переменных` сохраняет параметры для warm start resource.

`Перезагрузка ресурса` выключает resource; service, настроенный для Runtime, запускает resource заново. Успешная консольная фраза: `Reboot successfully Executed`.

`Сброс ресурса` очищает load database, удаляет bootfile и перезагружает resource с initial values. Успешная консольная фраза: `The Reset Resource command was sent successfully`.

## vcont.fboot

Boot file - набор команд, с помощью которого Runtime создает database. Набор команд идентичен командам, отправляемым при `Загрузка`, и виден в `Консоль загрузки`.

При старте controller читает boot file и создает описанные algorithms.

Runtime package/licensing can change this behavior. VCont Trial Lite does not support `vcont.fboot` autoload; Demo / Trial Full and licensed/internal runtime packages can support it. For trial/demo/licensing questions, cross over through `studio-vcont-contract.md` to the VCont licensing reference.

Создание:

1. resource context menu -> `Создать файл загрузки`;
2. в диалоге `Формирование FBOOT-файла` выбрать objects hierarchy слева и FBs справа;
3. при необходимости воспользоваться кнопками `Выбрать именные` или `Выбрать загруженные`;
4. нажать `Загрузить`;
5. подтвердить overwrite, если файл уже существует.

Результат: `vcont.fboot` создается в директории с executable VCont.

Успешность создания: есть `CREATE` для каждой task, в конце есть `START`, нет ошибок.

Чтобы controller считал новый file: выполнить online `Перезагрузка ресурса` или `Сброс ресурса`, либо перезагрузить controller вручную.

`Создать и загрузить файл загрузки` создает `vcont.fboot` и отправляет его в controller. Flow: resource context menu -> `Создать и загрузить файл загрузки`, подтвердить overwrite если файл существует, затем подтвердить загрузку файла в controller. Успешность загрузки bootfile подтверждается фразами `The Load File command was sent successfully` и `Check BootSuccess` плюс отсутствием ошибок.

## Monitoring

Перед monitoring проверь: controller доступен по IP/port, VCont запущен, algorithms загружены.

Подключение к resource: context menu resource -> `Подключиться к ресурсу`, toolbar button или hotkey `Ctrl+O`. Успешное подключение отображается зеленым индикатором рядом с resource name.

Добавление ФБ в monitoring:

1. открыть editor control loop;
2. выделить нужные ФБ, либо menu `Правка` -> `Выбрать всё`, либо `Ctrl+A`;
3. навести курсор на выделенный block так, чтобы cursor стал значком с четырьмя стрелками;
4. context menu выделения -> `Мониторинг`.

По умолчанию фон online values желтый.

Source-derived monitoring protocol:

- add/remove watch sends `<Request Action="CREATE|DELETE"><Watch Source="<APP>.<LOOP>.<qualifiedPort>" Destination="*" /></Request>` to destination `loop.getTask()`;
- reading monitoring values sends `<Request Action="READ"><Watches/></Request>` with empty destination;
- full monitored source path is `<APP>.<LOOP>.<FB_OR_SUBAPP_PATH>.<PORT>`;
- `element.getQualifiedString()` contributes `<FB_OR_SUBAPP_PATH>.<PORT>`, while Studio prepends application and loop;
- `READ` of individual connections is useful for deterministic test oracles, but it is not the same protocol shape as Studio UI monitoring.

## Live Writes And Forcing

Изменение входных параметров в online monitoring: double-click input port value field, ввести значение, press `Enter`. Это обычная запись в controller database и она влияет на реальный algorithm.

Forcing: port context menu -> `Форсировать`. Forced signal перехватывает значение, и block использует forced value вместо real value. Отключение: forced port context menu -> `Отключить форсирование`.

Source-derived live action protocol:

```xml
<Request ID="<id>" Action="WRITE"><Connection Source="<xml-encoded-value>" Destination="<APP>.<LOOP>.<qualifiedPort>" /></Request>
```

- live write uses destination `<task>` for event-driven tasks and empty destination for periodic tasks;
- write source value is XML-escaped through `DeploymentExecutor.encodeXMLChars`;
- force currently uses the new hierarchy string shape below; it is suspicious XML, but it is what the source emits:

```xml
<Request ID="<id>" Action="FORCE"><Destination="<APP>.<LOOP>.<qualifiedPort>" force="true" /></Request>
<Request ID="<id>" Action="FORCE"><Destination="<APP>.<LOOP>.<qualifiedPort>" force="false" /></Request>
<Request ID="<id>" Action="GETFORCEDPARAM"></Request>
<Request ID="<id>" Action="UNFORCEALL"></Request>
```

Legacy IEC61499 monitoring code has older force/write shapes. For VCStudio project hierarchy and ST integration on `VCONT-2056`, prefer `NewHierarchyDeploymentService` behavior.

## Manual Event Trigger

Manual event generation applies to event-task loops. Единственный независимый источник событий без event input из документа - `E_RESTART`.

In the new hierarchy path, `TriggerEvent` is not an XML action. `MonitoringManager.triggerEvent(...)` calls `writeFBParameter(..., "$e")`, so the emitted command is:

```xml
<Request ID="<id>" Action="WRITE"><Connection Source="$e" Destination="<APP>.<LOOP>.<qualifiedEventPort>" /></Request>
```

Output event counter increases by one; input event counter shows how many events arrived and how many times block logic executed.


## HSB Warning

Loading or online-loading one Studio resource does not propagate project structure to reserve VCont nodes. HSB synchronizes runtime data/state, not `.vcsys`, control loops, tasks, FBs, or connections. For HSB stands, load the same or compatible generated program/bootfile into every VCont instance before testing failover.

Live writes and forcing are real runtime actions. In HSB they can affect synchronized DI/DO data, but they are not project synchronization. After failover, verify synchronized DI/DO or external effects rather than assuming all Studio-visible context was replicated.

For current HSB role, use the VCont runtime command `HSBSTATUS` through the backend/protocol layer. It returns `MAIN`, `RESERVE`, `STANDALONE`, or `NONE`; `NONE` means HSB is disabled, not that Studio failed to connect or load a project.
