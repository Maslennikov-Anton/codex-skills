# Loading And Monitoring

For the exact handoff from Studio load/monitoring operations into VCont runtime effects, see `studio-vcont-contract.md`.

## Запуск VCont для отладки из VCStudio

Для загрузки logic и отладки нужно запустить VCont с правами администратора. Окно VCont после запуска закрывать нельзя. После запуска runtime доступен через локальный сетевой адрес, порт по умолчанию `61499`.

Resource в Studio должен иметь IP и port, соответствующие target VCont.

## Offline Operations

Offline operations доступны без подключения к resource:

- удаление объектов структуры, включая project/device/resource/application/control loop;
- переименование объектов, кроме project name;
- загрузка resource/application/control loop;
- online load/delete control loop commands;
- подключение к resource.

При попытке удаления/переименования в online mode система не меняется. При попытке full load resource/application/control loop в online mode Studio автоматически разрывает подключение к resource.

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
2. в диалоге `Формирование FBOOT-файла` выбрать objects hierarchy и FBs;
3. подтвердить overwrite, если файл уже существует.

Результат: `vcont.fboot` создается в директории с executable VCont.

Успешность создания: есть `CREATE` для каждой task, в конце есть `START`, нет ошибок.

Чтобы controller считал новый file: выполнить online `Перезагрузка ресурса` или `Сброс ресурса`, либо перезагрузить controller вручную.

`Создать и загрузить файл загрузки` создает `vcont.fboot` и отправляет его в controller. Успешность загрузки bootfile подтверждается фразами `The Load File command was sent successfully` и `Check BootSuccess` плюс отсутствием ошибок.

## Monitoring

Перед monitoring проверь: controller доступен по IP/port, VCont запущен, algorithms загружены.

Подключение к resource: context menu resource -> `Подключиться к ресурсу`, toolbar button или hotkey `Ctrl+O`. Успешное подключение отображается зеленым индикатором рядом с resource name.

Добавление ФБ в monitoring:

1. открыть editor control loop;
2. выделить нужные ФБ или `Ctrl+A`;
3. context menu выделения -> `Мониторинг`.

По умолчанию фон online values желтый.

## Live Writes And Forcing

Изменение входных параметров в online monitoring: double-click input port value field, ввести значение, press `Enter`. Это обычная запись в controller database и она влияет на реальный algorithm.

Forcing: port context menu -> `Форсировать`. Forced signal перехватывает значение, и block использует forced value вместо real value. Отключение: forced port context menu -> `Отключить форсирование`.

## Manual Event Trigger

Manual event generation applies to event-task loops. Единственный независимый источник событий без event input из документа - `E_RESTART`.

Manual trigger: right-click output event port -> `TriggerEvent`. Output event counter increases by one; input event counter shows how many events arrived and how many times block logic executed.


## HSB Warning

Loading or online-loading one Studio resource does not propagate project structure to reserve VCont nodes. HSB synchronizes runtime data/state, not `.vcsys`, control loops, tasks, FBs, or connections. For HSB stands, load the same or compatible generated program/bootfile into every VCont instance before testing failover.

Live writes and forcing are real runtime actions. In HSB they can affect synchronized DI/DO data, but they are not project synchronization. After failover, verify synchronized DI/DO or external effects rather than assuming all Studio-visible context was replicated.

For current HSB role, use the VCont runtime command `HSBSTATUS` through the backend/protocol layer. It returns `MAIN`, `RESERVE`, `STANDALONE`, or `NONE`; `NONE` means HSB is disabled, not that Studio failed to connect or load a project.
