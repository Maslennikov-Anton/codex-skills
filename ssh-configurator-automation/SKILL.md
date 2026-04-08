---
name: ssh-configurator-automation
description: Автоматизировать и тестировать локальное desktop-приложение `ssh-configurator` на Vue 3 + Electron. Использовать, когда Codex должен многократно работать с этим приложением, заполнять формы, инспектировать отрисованный UI, выполнять сценарии через Electron/Chromium DevTools Protocol и избегать ненадёжной пиксельной автоматизации под GNOME Wayland/XWayland.
---

# Автоматизация SSH Configurator

Для этого приложения использовать подход `CDP-first`. Не переходить по умолчанию к кликам через `xdotool` или `wmctrl`, если Electron renderer можно контролировать через DevTools protocol.

## Быстрый старт

Если приложение ещё не запущено с включённым remote debugging, поднять отдельный debug-экземпляр:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/launch_sshcfg_debug.sh
```

Поднять backend на текущем overlay-контуре:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/backend-start.sh
```

Сбросить backend в чистый overlay и поднять заново:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/backend-reset.sh
```

Построить machine-readable registry manual test cases:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/build_case_registry.py
```

Собрать markdown-отчёт из registry:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/render_case_registry_report.py
```

Остановить backend и закрыть debug frontend после завершения работы:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/close_sshcfg_debug.sh
/home/ant/codex-skills/ssh-configurator-automation/scripts/backend-stop.sh
```

Посмотреть текущие интерактивные элементы:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js list-elements
```

Перейти на маршрут и снять текущее состояние страницы:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js goto /diagnostics
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js snapshot
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js read-tables
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js open-console
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js read-console
```

Открыть диалог настроек SSH и прочитать значения формы:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js open-settings
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js switch-settings-tab configuration
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js read-settings-state
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js inspect-settings-dom
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js read-connection-form
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js read-status
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js discover-services
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js set-locale en
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js rename-network-file 9995-manual.network 9995-manual-renamed.network
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js delete-network-file 9995-manual-renamed.network
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js add-user-key "ssh-ed25519 ... codex_temp_key"
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js refresh-known-hosts 192.168.122.10
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js generate-key
```

Актуальное наблюдение по текущей сборке:

- таб `Конфигурация` в `TheSettings.vue` сейчас содержит только selector языка интерфейса
- элементы `Импортировать` и `Экспортировать` в текущем source/runtime DOM не подтверждены
- manual TC на import/export считать кандидатами на product-gap до отдельного подтверждения из другой сборки или актуализированных требований

Установить SSH host:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js set-host 192.168.122.10
```

Нажать кнопку подключения:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js click-connect
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js click-title 'Вывести список'
```

Полностью воспроизвести минимальный рабочий connect-сценарий:

```bash
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js connect-minimal
/home/ant/codex-skills/ssh-configurator-automation/scripts/sshcfg_cdp.js disconnect
```

## Рабочий процесс

1. Предпочитать отдельный debug-экземпляр уже открытому пользовательскому окну без remote debugging.
2. Сначала инспектировать DOM через `list-elements`.
3. Опираться на стабильные селекторы: `id`, классы input-элементов, текст кнопок и видимое состояние маршрута.
4. Для заполнения полей менять значение через DOM setter и диспатчить оба события: `input` и `change`.
5. Проверять результат повторным чтением DOM или снимком окна, если пользователю важно визуальное подтверждение.

## Операционный Контекст

- frontend `ssh-configurator` в тестовом цикле поднимает агент, а не пользователь вручную, если не оговорено иное
- постоянный корневой workspace для долгой агентной работы: `/home/ant/codex-work`
- направление по конфигуратору вести в: `/home/ant/codex-work/configurator`
- внутри направления использовать подпапки по направлениям:
  - `backlog`
  - `coverage`
  - `fixtures`
  - `notes`
- журнал расхождений между manual ТК и текущим продуктом вести отдельно в:
  - `/home/ant/codex-work/configurator/notes/testcase-obsolescence-log.md`
- если кейс не совпадает с текущим UI/поведением, фиксировать это сначала в obsolescence log, а уже потом отражать в coverage/status registry
- текущий базовый backend-образ для тестов: `/home/ant/libvirtimages/vcont_plc.qcow2`
- текущий рабочий libvirt-домен для этого backend-контура: `plc1`
- текущий рабочий overlay для тестового цикла: `/home/ant/libvirtimages/vcont_plc.plc1.overlay.qcow2`
- ручной mount через Virt Manager считать временным workaround, а не целевым workflow
- предпочтительный workflow для backend-тестов:
  - создавать overlay поверх базового qcow2-образа
  - переиспользовать существующую конфигурацию домена `plc1` по CPU/RAM/сети и менять только путь к диску
  - запускать тестовый backend на overlay
  - при необходимости удалять и пересоздавать overlay для чистого прогона
- базовый qcow2-образ считать неизменяемым test fixture; тестовые изменения должны уходить в overlay, а не в base image
- считать текущую штатную цепочку такой: `vcont_plc.qcow2` -> `vcont_plc.plc1.overlay.qcow2` -> `plc1`
- mutating и destructive действия внутри гостя считать допустимыми, если они нужны для покрытия manual test cases и укладываются в границы overlay-контура
- после таких действий агент должен быть готов вернуть стенд в чистое состояние через `backend-reset.sh`
- недопустимо менять base image, произвольные host-системные настройки вне гостя и другие несвязанные libvirt-домены

## Правила работы

- Рассматривать это приложение как web UI внутри Electron, а не как обычное нативное desktop-приложение.
- Предпочитать автоматизацию через CDP/DOM вместо accessibility tree и вместо pointer automation.
- `wmctrl`, `xwd`, `xwdtopnm` и `pnmtopng` использовать только для поиска окна и визуальной проверки.
- Инъекцию мыши или клавиатуры использовать только как fallback, если целевой элемент находится вне renderer DOM.
- Если пользователь просит автоматизировать уже открытый экземпляр приложения, который не был запущен с `--remote-debugging-port`, объяснить, что для надёжной автоматизации нужен debug-экземпляр.
- Селекторы и логику действий хранить в скриптах, а не собирать каждый раз одноразовыми shell-командами.
- Для work coverage objective по manual test cases не останавливать работу на метке `mutating`, если сценарий воспроизводим и откат обеспечивается пересозданием overlay.
- Реальными ограничениями считать только такие блокеры, которые нельзя снять локальной автоматизацией, фикстурами, новым overlay, отдельным backend-стендом или расширением skill-а.

## Скрипты

### `scripts/launch_sshcfg_debug.sh`

Запускает `ssh-configurator` с параметрами:

- `--remote-debugging-port=${SSHCFG_CDP_PORT:-9222}`
- `--user-data-dir=${SSHCFG_USER_DATA_DIR:-/tmp/sshcfg-automation}`

Использовать, когда нужен стабильный automation target.

### `scripts/backend-start.sh`

Поднимает текущий backend-контур для тестов:

- проверяет наличие base image
- при необходимости создаёт overlay
- гарантирует, что домен `plc1` указывает на overlay
- запускает домен, если он выключен

Использовать, когда нужен обычный старт backend без сброса тестового состояния.

### `scripts/backend-reset.sh`

Полностью пересоздаёт текущий backend-контур для чистого прогона:

- останавливает домен `plc1`
- удаляет текущий overlay
- создаёт новый overlay поверх `vcont_plc.qcow2`
- заново привязывает домен `plc1` к overlay
- запускает домен

Использовать, когда нужен clean test cycle без сохранения изменений в гостевой системе.

### `scripts/backend-stop.sh`

Корректно останавливает текущий backend-контур:

- завершает домен `plc1` через `shutdown`
- при необходимости делает `destroy` после timeout

Использовать в конце тестового цикла, когда backend больше не нужен.

### `scripts/close_sshcfg_debug.sh`

Закрывает debug-экземпляр `ssh-configurator`, запущенный с `--remote-debugging-port`.

Использовать в конце тестового цикла, когда frontend больше не нужен.

### `scripts/sshcfg_cdp.js`

Поддерживаемые команды:

- `list-elements`
- `goto <route>`
- `snapshot`
- `read-tables`
- `open-console`
- `read-console`
- `open-settings`
- `switch-settings-tab <connection|configuration>`
- `read-settings-state`
- `inspect-settings-dom`
- `read-connection-form`
- `read-status`
- `discover-services`
- `set-locale <ru|en>`
- `read-selections`
- `read-network-files-state`
- `read-keys-state`
- `read-vm-xmls-state`
- `read-vm-images-state`
- `set-host <value>`
- `click-text <button text>`
- `click-title <button title>`
- `click-connect`
- `connect-minimal`
- `disconnect`
- `select-app-row <rowText> [tableIndex]`
- `select-prime-row <rowText> [tableIndex]`
- `select-network-file <fileName>`
- `prepare-network-file-rename <fileName> <newName>`
- `rename-network-file <fileName> <newName>`
- `delete-network-file <fileName>`
- `read-keys-form-state`
- `submit-prompt <value>`
- `select-first-key`
- `select-key-row <rowIndex>`
- `delete-selected-key`
- `delete-key-row <rowIndex>`
- `add-user-key <publicKey>`
- `refresh-known-hosts <ipAddress>`
- `generate-key`
- `read-prompt-state`
- `reconnect-after-known-hosts-refresh`
- `select-xml-file <fileName>`
- `select-image-file <fileName>`
- `list-safe-actions`
- `run-safe-action <actionKey>`
- `assert-command <actionKey>`
- `inventory-safe-routes`

Скрипт:

- находит CDP page target через `http://127.0.0.1:${SSHCFG_CDP_PORT:-9222}/json/list`
- подключается к renderer websocket
- выполняет DOM-автоматизацию через `Runtime.evaluate`
- умеет открывать диалог настроек SSH через нижнюю панель приложения
- умеет надёжно закрывать диалог настроек SSH с polling-проверкой фактического исчезновения видимого окна
- при необходимости использует fallback-цепочку закрытия: header event click -> native click -> panel toggle
- умеет повторно воспроизводить минимальный рабочий сценарий подключения
- умеет извлекать строки HTML/PrimeVue-таблиц после `list/show` действий
- для части mutating screen-ов умеет подтверждать результат по post-action state таблицы, даже если консольное evidence на этом экране не ловится стабильно
- для `Keys` умеет подтверждать `add_user_key` через последующий `list_user_keys`
- для `Keys` умеет удалять конкретную строку таблицы по индексу и подтверждать результат через уменьшение числа строк и последующий `list_user_keys`
- для `refresh_known_hosts` умеет подтверждать командный эффект, но ожидаемый fingerprint prompt на reconnect в текущем приложении не воспроизводится автоматически
- для невалидного IP в `Keys` фактическое поведение UI сейчас такое: кнопка `Удалить ключи в known_hosts` disable-ится без отдельного error message
- для `generate_key` умеет проходить интерактивные prompt-ы через `TheDialogPrompt`
- подтверждено, что `generate_key` исполняется внутри удалённой SSH shell-сессии и не меняет локальный `/home/ant/.ssh`
- умеет открывать встроенную консоль приложения и читать последние log entries
- умеет выполнять проверенные `safe-read` сценарии по именованным action key
- умеет проверять, какая именно backend-команда реально попала в console log после действия
- умеет делать базовый row selection для DOM-таблиц и PrimeVue таблиц, когда достаточно простого `tr.click()`
- умеет выполнять page-specific selection flow для `network-files` с проверкой `renameTarget` и доступности кнопки `Переименовать`
- умеет выполнять подготовку rename-сценария для `network-files` без фактического запуска rename
- умеет выполнять page-specific selection flow для `keys` через выбор первой строки и проверку доступности `Удалить ключ`
- умеет выполнять page-specific selection flow для `vm/xmls` и `vm/images`, включая чтение списка, попытку выбора и проверку rename/delete state

### `scripts/build_case_registry.py`

Строит machine-readable registry manual test cases из Allure TestOps:

- читает выборку по `Application` и `Story`
- подтягивает `overview`, `testcase` и `scenario`
- импортирует прошлую разметку из markdown-отчёта, если он есть
- нормализует статус в рабочие категории:
  - `automation-pass`
  - `in_progress`
  - `needs-new-backend`
  - `needs-new-helper`
  - `needs-fixture`
  - `needs-human-judgement`
  - `todo`

Использовать как source of truth для покрытия.

### `scripts/render_case_registry_report.py`

Рендерит markdown-отчёт из machine-readable registry.

Использовать, когда нужно быстро получить человекочитаемую сводку без ручной правки таблиц.

## Как расширять skill

Когда нужен новый повторяемый action:

1. Посмотреть DOM через `list-elements`.
2. Найти максимально стабильный селектор.
3. Добавить в `scripts/sshcfg_cdp.js` отдельную явную команду.
4. Повторно запустить скрипт на debug-экземпляре.
5. Если действие пользовательское и видимое, проверить его снимком окна или повторным чтением DOM.

Текущие селекторы и заметки смотри в [dom-notes.md](references/dom-notes.md).
Backend command contract смотри в [backend-commands.json](references/backend-commands.json) и [backend-commands-notes.md](references/backend-commands-notes.md).
Карту маршрутов и наблюдаемое поведение смотри в [route-map.md](references/route-map.md).
Проверенные безопасные действия и их результаты смотри в [safe-actions.md](references/safe-actions.md).
Связку UI action -> SSH command -> console response смотри в [console-evidence.md](references/console-evidence.md).
Полную матрицу `menu -> route -> action -> command -> risk` смотри в [command-matrix.md](references/command-matrix.md).

Validated helper actions:

- использовать `list-safe-actions` для просмотра текущего реестра
- использовать `assert-command <actionKey>`, когда важно доказать связку `UI action -> backend command`
- считать validated только те action-ы, которые уже реально прогнаны через helper
- не складывать такие операционные договорённости в краткосрочную память, если это постоянное правило работы; фиксировать их прямо в skill-е
- для icon-only кнопок внутри `AppAccordion` использовать адресацию по заголовку аккордеона и индексу кнопки внутри `.content`
- считать generic row selection вспомогательным слоем, а не полной заменой page-specific automation
- если после выбора строки нужно доказать переход страницы в новое состояние, добавлять отдельную page-specific команду вместо надежды на generic selection
- считать `select-network-file` validated на текущем хосте, а `select-xml-file` / `select-image-file` пока структурно готовыми, но не позитивно validated из-за отсутствия данных на текущем backend
- считать `prepare-network-file-rename` validated на текущем хосте как недеструктивный preparatory flow
- считать `select-first-key` validated на текущем хосте как рабочий обход для экрана `Keys`, даже при пустом текстовом рендере строки
- считать `delete-selected-key` реализованным helper-ом, но не прогнанным в этой сессии
- после выполнения необходимых действий закрывать debug-экземпляр `ssh-configurator` и останавливать backend-контур, если пользователь явно не просил оставить их запущенными
