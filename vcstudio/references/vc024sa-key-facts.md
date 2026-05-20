# VC024SA.B Key Facts

This reference is a self-contained distilled knowledge base for `VC024SA.B Руководство разработчика VCStudio`, revision B, 2025. The full VC024SA.B extract lives in the `vcstudio` skill. The `vcont` skill keeps a runtime-facing subset in its own `vc024sa-runtime-contract.md`. For exact wording, table rows, figure captions, or rare Studio details, use `vc024sa-complete.md`.

## Document Identity And Revisions

- System: `VC SYSTEM`.
- Document: `Руководство разработчика VCStudio`.
- Code: `VC024SA`.
- Revision: `B`, year `2025`.
- Revision history:
  - `A`, `20.10.2024`: first revision.
  - `B`, `25.03.2025`: description of new hierarchy.

## VCSystem Model

- VCSystem consists of VCont runtime and VCStudio development environment.
- VCont is a software-implemented controller / Soft PLC for automation, running on realtime/deterministic Linux-family OS environments.
- VCont can run on industrial PCs, servers, and similar compute nodes; it may optionally be configured for redundant mode.
- VCStudio configures controller system settings, communication capabilities, and logic/control schemes.
- VCSystem works together with I/O modules and external systems for acquisition, processing, and operational control.

## Installation And Startup

Hardware/software requirements from the document:

| Component | Hardware | OS/software |
|---|---|---|
| VCStudio | At least 8 GB RAM, HDD 500 GB, x86_64 Core i5+ | Astra Linux 1.7+, Ubuntu 20.04+, Debian 12+, Windows 10+ |
| VCont emulator mode | At least 2 GB RAM, HDD 500 GB, x86_64 Core i5+ | Astra Linux 1.7+, Ubuntu 20.04+, Debian 12+, Windows 10+ |
| VCont operational mode | Target hardware with deterministic realtime capability | Linux-like OS configured for deterministic mode; OS realtime tuning is done only by ISource service engineers |

- Demo distributions are requested via `pasupport@isource.ru` and delivered as archives.
- Linux installation paths: create `/opt/vcstudio/` and `/opt/vcont/`, unpack archives there.
- Windows installation paths: create `vcstudio` and `vcont` folders in the root of the disk; otherwise long paths can cause unpacking errors.
- Linux start command/file: `vcstudio`.
- Windows start command/file: `vcstudio.exe`.

## Project, Workspace, Authorization

- VCStudio project is a set of devices, resources, and control logic schemes with one common address space.
- At program opening the user chooses the project directory/workspace.
- Only one project can be open in one VCStudio instance.
- Default login/password in the document: `admin` / `admin`.
- New project flow: start VCStudio -> authorize -> `Новый проект` -> choose template -> enter project name and folder -> `Создать`.
- Existing project flow: start VCStudio -> authorize -> `Обзор` or project dropdown -> select `.vcsys` file -> `Открыть`.
- Archive files are not cleaned automatically:
  - Studio system messages: `/project_name/.metadata/.log`.
  - Backup/history: `/workspace_name/.metadata/.plugins/org.eclipse.core.resources/.history/`.

## UI Areas And Common Commands

Main VCStudio UI areas:

- `Структура системы`: create/manage devices, resources, applications, loops.
- `Редактор`: object editors.
- `Навигация по контуру`: graphical navigation around loop host/work area.
- `Свойства и сообщения`: object properties and messages.
- `Библиотека`: libraries and function blocks available for loop placement.

Common UI commands and shortcuts:

- Reset windows: `Окно` -> `Сброс перспективы`.
- Preferences: `Окно` -> `Параметры` -> `Общие`.
- Save current editor: `Ctrl+S`.
- Save project: `Shift+Ctrl+S`.
- Connect to resource: `Ctrl+O` or `Подключиться к ресурсу`.
- Select all FBs in loop editor: `Ctrl+A`.
- Global FB search: `Ctrl+F`.
- Monitoring hotkey example in document: `Ctrl+M`.
- Toolbar includes save current editor, save project, close all editors, forced values list, emulation mode, history, zoom, hide event connections, hide data connections, calculate order, connect to resource, add comment, load application, unload application (future), get values (future), and alignment controls.

Preference facts:

- Autosave period recommendation: at least 5 minutes.
- Enable `Ограничить запись истории` to limit history archive growth.
- Themes require `Enable theming`.
- Hotkeys are configured on `Клавиши` tab.
- Connector colors are configurable by data type.
- Monitoring colors and polling are configurable; recommended polling period in the document: `300 мс`.
- Load settings: recommended virtual-controller connection timeout: `10000мс`.
- Control loop settings choose loop language; for `Функциональная блок-схема` a maximum block count before warning can be set.
- Advanced settings: the document says all checkboxes must be enabled or connection to VCont will fail.
- Idle lock maximum: 20 minutes.

## Project Hierarchy

Canonical hierarchy:

```text
Project -> Device -> Resource -> Application -> Control Loop -> Function Blocks
```

- `Project`: common address space; object names must be unique.
- `Device`: server/industrial computer hosting runtime resource.
- `Resource`: runtime environment/application that executes periodic or event tasks.
- `Application`: groups algorithms, e.g. by process unit, and defines loop order.
- `Control Loop`: connected algorithm for one controlled object, or group of signals for one object.

Creation flows:

- Device: project context menu -> `Добавить устройство`; document says device name min/max length is six characters.
- Resource: device context menu -> `Добавить ресурс`; set `IP-адрес` and `Порт` in properties.
- Application: resource context menu -> `Добавить приложение`.
- Control loop: application context menu -> `Добавить контур управления`.

## Tasks And Loops

- Every control loop must be assigned to a task.
- Task types:
  - periodic/cyclic: FBs execute once per period in cyclic order;
  - event: FBs execute when event arrives at event input.
- Tasks are edited in resource editor on tab `Задачи`.
- Periodic/cyclic tasks require a period.
- Important restriction: do not assign the same period to different tasks.
- If the period is deleted from a cyclic task, the task becomes event-based.
- Loop task assignment is set in loop properties field `Задача`.

## Function Blocks And Ports

- FBs are added from `Библиотека`; the library includes IEC 61131-3 blocks and VCont-specific blocks.
- FB search is available through the library search field, by double-clicking the work area and typing a block name, and globally via `Ctrl+F`.
- FB visual model: instance name on first row, inputs on the left, outputs on the right, event ports separated at the top, type and execution number at bottom.
- Hovering a port shows its description.
- Port properties show initial value, data type, comment, default value, incoming/outgoing connections, and allow connection removal.
- Initial values are undefined by default. After runtime start, full load, variable initialization, or resource reset, unconnected/uninitialized inputs usually become `false` for Boolean and `0` for analog/numeric.
- Initial values can be set in FB properties, graphical field near the port, or port properties.

ANY typing:

- `ANY`, `ANY_BIT`, `ANY_MAGNITUDE` ports can accept different allowed data types.
- Arithmetic FBs commonly default to `REAL`; logic FBs commonly default to `BOOL`.
- `ANY_BIT` operations do not accept `REAL`.
- Forced type notation `Тип_данных#Значение` was removed in the current version; type is changed through block properties.

Variable port count:

- Copy an existing FB from base library into `User Library`.
- Rename according to documented pattern `<имя блока>_N_K`, where `N` is input count and `K` is output count. Example: `ADD_5` for ADD with five inputs.
- Edit data/interface and connect new inputs to `REQ` where required.
- For Modbus blocks the same approach is used, e.g. `MBWRITE_PACK3`.

Block type maintenance:

- `Заменить тип блока`: changes type of an existing block without breaking connections and preserves initial values where compatible.
- `Обновить тип блока`: updates input/output count and types on an instance after its type was edited.

## Connections, References, Aliases, Order

- Connections can be data or event connections.
- One output can have multiple connections.
- Connection creation methods: drag line, command `Соединить` / dialog `Создать соединение`, or copy/paste source/destination ports with `Ctrl+C`/`Ctrl+V`.
- `Создать соединение` shows only compatible ports; an empty parameter list means the connection is impossible.
- Inter-loop connection reference names:
  - outgoing loop side: `БЛОК.ПАРАМЕТР`;
  - incoming loop side: `ПРИЛОЖЕНИЕ.КОНТУР.БЛОК.ПАРАМЕТР`.
- Renaming source block/loop/application updates connection-reference names.
- Any connection line can be converted to a reference with `Преобразовать в ссылку`.
- Connection aliases are assigned with `Псевдоним`; useful when references are displayed instead of lines.

Execution order:

- Implicit order is set by adding blocks to the loop.
- Explicit order can be set in block properties or by command `Рассчитать порядок`.
- In generated `vcont.fboot`, order is behavior: preserve `CREATE` order or explicit order commands.

Event-loop guardrails:

- Event loops need event generation.
- `E_RESTART`, usually renamed to `START`, generates one event on output `COLD` after controller startup.
- `E_CYCLE` generates cyclic events when it receives `START` event.
- Example `E_CYCLE` period on `DT`: `1000 ms`.
- To process all FBs in order, connect event inputs sequentially.
- Avoid event branching: execution order is undefined.
- Avoid event closure/cycle: it can process without pauses and drive resource load to 100%.

## Structured Text In VCStudio

- Studio can create FBs and loops in ST and use them with base FB library blocks.
- ST is translated to executable Lua code.
- Benefits described by document: Lua libraries, cross-platform execution, Lua debugging/profiling.
- ST syntax is Pascal-like; IEC 61131-3 keywords are uppercase by convention; whitespace does not affect syntax.
- Assignment: `variable := value;`.
- Multi-line comment: `(* comment *)`.
- Standard function families mentioned: arithmetic `ADD`, `DIV`, `MOD`, `SUB`; bit `ROL`, `SHR`, `AND`, `OR`; string `CONCAT`, `DELETE`, `FIND`; conversions `BOOL_TO_BYTE`, `REAL_TO_INT`.
- Operators:
  - arithmetic: `+`, `-`, `*`, `/`, `mod`;
  - logic: `OR`, `AND`, `XOR`, `NOT`;
  - comparison: `=`, `<>`, `>`, `>=`, `<`, `<=`; result is always `BOOL`.
- Types: `SINT`, `USINT`, `INT`, `UINT`, `DINT`, `UDINT`, `LINT`, `ULINT`, `REAL`, `LREAL`, `BYTE`, `WORD`, `DWORD`, `LWORD`, `BOOL`, `STRING`, `TIME`, `TOD`, `DATE`, `DT`.
- Bit access example: `a.3 := 1;`.
- Strings are character sequences, not arrays.
- Variables initialize to zero by default unless explicit initial value is set.
- Control structures: `IF`/`ELSIF`/`ELSE`, `CASE`, `FOR`, `WHILE`, `REPEAT`.
- `FOR` defaults step to `1` if `BY` is omitted; use negative step for reverse iteration; `EXIT` can terminate loops early.
- `WHILE` and `REPEAT` can be risky in realtime control: while inside the loop, the controller may not observe changed FB inputs and can miss emergency conditions. Typical safe use: initialization or bounded string search.
- Arrays require fixed bounds; dynamic/unbounded arrays are not supported for predictable PLC timing/memory.
- Constant variables can be used as array bounds.
- Arrays can contain FB instances such as timers with initialized `PT` values.
- `ENUM` is used for named state values and state machines. Use explicit numeric values when compatibility matters.
- The source document has only a heading for `STRUCT` in the extracted text; do not invent details beyond what is in `vc024sa-complete.md`.

## VCont Startup, Load, Online Operations, Monitoring

- For debugging/loading, VCont must be started with administrator rights.
- Do not close the VCont window after startup.
- Default runtime port from the document: `61499`.
- Resource properties in Studio must contain the target IP address and port.

Offline operations:

- Available without resource connection: object deletion, rename except project name, load/unload resource/application/loop, online load/delete loop commands, and connection to resource.
- Delete/rename attempts in online mode leave system unchanged.
- Full load in online mode automatically disconnects from resource.

Full load:

- Can be performed at resource, application, or control-loop level.
- Resource load loads algorithms and initial values for the entire resource including applications and loops.
- Application load loads algorithms and initial values for that application and its loops.
- Full load writes initial values to controller database; subsequent connection provides cold start.
- Success in `Консоль загрузки`: `START` commands for all tasks and no errors.
- `Выгрузка` and `Получение значений` are marked as future/in-development functionality in the document.

Online loop operations:

- `Онлайн загрузить КУ`: loads new/changed control-loop algorithm without resetting current values to initial values.
- `Онлайн удалить КУ`: deletes the loop algorithm from runtime.
- Online load success: `START` for all loop tasks and no errors.
- Online delete success: `DELETE` for all loop tasks and no errors.

Online resource operations:

- `Инициализация переменных`: clears warm-start data and restarts resource with initial values.
- `Сохранение переменных`: saves parameters for warm start.
- `Перезагрузка ресурса`: service restarts Runtime; success phrase: `Reboot successfully Executed`.
- `Сброс ресурса`: clears load database, deletes bootfile, restarts with initial values; success phrase: `The Reset Resource command was sent successfully`.

Bootfile:

- Bootfile is a set of commands Runtime uses to create its database.
- It is identical to commands sent during `Загрузка` and visible in `Консоль загрузки`.
- Runtime reads bootfile at startup.
- `Создать файл загрузки` creates `vcont.fboot` in the directory with VCont executable.
- Successful bootfile creation: `CREATE` commands for every task, ending `START`, no errors.
- To make controller read a new bootfile: reboot resource, reset resource, or manually restart controller.
- `Создать и загрузить файл загрузки`: creates and sends `vcont.fboot` to controller; success phrases: `The Load File command was sent successfully` and `Check BootSuccess`.

Monitoring:

- Preconditions: controller reachable by resource IP/port, VCont running, algorithms loaded.
- Connect methods: resource context menu `Подключиться к ресурсу`, toolbar button, `Ctrl+O`.
- Successful connection: green indicator next to resource name.
- Add to monitoring: select FBs in loop editor or `Ctrl+A`, context menu `Мониторинг`.
- Online values have yellow background by default.
- Changing an input value during monitoring is a direct write to controller database and affects the real algorithm.
- `Форсировать` forces a variable, causing the block to use forced value instead of real value. Treat the document's safety wording cautiously in real equipment contexts.
- Disable forcing through `Отключить форсирование`.
- Manual event trigger is for event-task loops; command `TriggerEvent` on output event port.
- Input event counter means how many events arrived and how many times block logic executed.
- Output event port counter simply increments previous value by one.

Service / restore:

- Backups are created when saving the project.
- Restore flow: toolbar `История изменений` -> choose date -> `Заменить`.
- Double-clicking a backup can compare backup `.vcsys` with current `.vcsys`; comparison window is `Сравнение текста`.

## Modbus Configuration In VCStudio

General Modbus workflow:

1. Configure communication in resource: `Modbus Serial` for RTU or `Modbus TCP` for TCP.
2. Create application.
3. Add control loop.
4. In loop editor use blocks from `Communication\Modbus`.

Modbus RTU Master, `Modbus Serial Ports`:

| Parameter | Meaning | Examples |
|---|---|---|
| `Имя порта` | Serial port name; physical port must exist | `COM1`, `COM3`, `ttyS0`, `ttyUSB0`, `ttyRS485_1` |
| `Скорость` | Must match slave devices | `9600`, `19200`, `38400`, `57600`, `115200` |
| `Четность` | Parity mode | `N`, `E`, `O` |
| `Биты данных` | Data bits | usually `8`, rarely `7` |
| `Стопбиты` | Stop bits | usually `1`, sometimes `2` |

Modbus RTU Client slave rows:

| Parameter | Meaning | Examples |
|---|---|---|
| `Имя устройства` | Project name for slave | `MB_AI1`, `MB_DI2`, `PUMP_1`, `METER_A` |
| `Порт` | One configured serial port | as configured |
| `ID` | Slave/unit ID, usually `1..247` | `1`, `6`, `84`, `150`, `224` |

Modbus TCP Client rows:

| Parameter | Meaning | Examples |
|---|---|---|
| `Имя устройства` | Project name for remote device | `SCADA_Panel`, `METER_A` |
| `IP-адрес` | Remote IP | `192.168.0.10`, `192.168.56.12` |
| `Порт` | TCP port | `502`, `1502`, `1505` |
| `ID` | Unit/slave ID; important for TCP->RTU gateway | `1`, `2`, `10` |
| `Окно` | Number of in-flight requests | `1` recommended, rarely `2` or `3` |
| `Таймаут` | Response timeout ms | `1000`, `3000`, `5000` |

Modbus TCP Server rows:

| Parameter | Meaning | Examples |
|---|---|---|
| `Имя сервера` | Project name for server config | `MBSRV1` |
| `IP-адрес` | Listen address; `0.0.0.0` usually means all interfaces | `0.0.0.0`, `192.168.0.20` |
| `Порт` | Listen TCP port | `502`, `1503`, `1505` |
| `Опции` | Detailed runtime options | `Address=0.0.0.0 Port=1505 Mode=tcp SlaveId=1` |

Server memory map:

| Register | Modbus address | Size | Access | Functions | Types |
|---|---:|---:|---|---|---|
| `QX0-QX65535` | `0-65535` | 1 bit | RW | `01`, `05`, `15` | `BOOL` |
| `IX0-IX65535` | `0-65535` | 1 bit | RO | `02` | `BOOL` |
| `IW0-IW65535` | `0-65535` | 16 bit | RO | `04` | `INT`, `WORD` |
| `MW0-MW29999` | `0-29999` | 16 bit | RW | `03`, `06`, `16` | `INT`, `WORD` |
| `MD0-MD9999` | `30000-49998` | 32 bit | RW | `03`, `06`, `16` | `DINT`, `REAL` |
| `ML0-ML3750` | `50000-65000` | 64 bit | RW | `03`, `06`, `16` | `LINT`, `LREAL` |

- Each Modbus TCP server has independent memory; `MBSRV1.QX1` is not the same as `MBSRV2.QX1`.
- Publish FB port value to Runtime memory by setting port property `Modbus` to `ServerName.MemoryAddress`, e.g. `MBSRV1.QX1`.
- Registry can be entered manually or selected through context menu `Регистры`, which supports search and renaming.
- Prefer `QX`/`IX` for Boolean variables to save memory.

## MODBUS Function Blocks

- Built-in library folder: `Communication\Modbus`.
- `_PACK` blocks read/write allowed Modbus memory areas.
- Blocks with `DEVICE` in the name monitor connection state and counters.
- `MBWRITE` and `MBREAD` are documented as obsolete and planned for removal; prefer `MBWRITE_PACK` and `MBREAD_PACK` for Studio-created algorithms.

`MBWRITE_PACK`:

| Port | Meaning |
|---|---|
| `REQ` | Event input initiating write packet |
| `CNF` | Event output for subsequent blocks |
| `DEVICE` | Slave device name from RTU/TCP client table |
| `ENABLE` | `TRUE` connect/enable, `FALSE` disconnect/disable |
| `ADDRESS` | `start_address:function` |
| `FORMAT` | Data format |
| `WD01...` | Values to write |
| `STATUS` | Current status code |

Write functions: `05` Force Single Coil, `06` Preset Single Register, `15` Multiple Coils, `16` Multiple Holding Registers.

`MBREAD_PACK`:

| Port | Meaning |
|---|---|
| `REQ` | Event input initiating read packet; document wording mistakenly says write |
| `CNF` | Event output for subsequent blocks |
| `DEVICE` | Slave device name from RTU/TCP client table |
| `ENABLE` | `TRUE` connect/enable, `FALSE` disconnect/disable |
| `ADDRESS` | `start_address:function` |
| `FORMAT` | Data format |
| `WD01...` | Document table says value for write; verify current block interface for read outputs |
| `STATUS` | Current status code |

Read functions: `01` Read Coils, `02` Read Input Status, `03` Read Holding Register, `04` Read Input Register.

Common formats: `C` bool 1 bit, `F4` real 32 bit, `F8` lreal 64 bit, `S2` int 16 bit, `S4` dint 32 bit, `S2` uint 16 bit as documented duplicate.

Common `_PACK` status codes:

- `0`: no connection or wrong block fields.
- `1`: no errors.
- `101`: illegal function.
- `102`: illegal data address.
- `103`: illegal data value or invalid `FORMAT`.
- `104`: slave device failure.
- `105`: acknowledge.
- `106`: slave busy.
- `107`: negative acknowledge.
- `108`: parity error.
- `110`: gateway path unavailable.
- `111`: gateway target device failed to respond.
- `112`: bad CRC.
- `113`: bad data.
- `114`: illegal exception code.
- `116`: too much data.
- `117`: response from wrong slave.
- `200+`: user error codes.

Diagnostics:

- `MBSERIALDIAG`: `PORT`, `RST_CNT`, `CONNECTED`, `BAUD`, `PARITY`, `TIMOUT`, `DELAY`, `MSGS_TX`, `MSGS_RX`, `MSGS_TO`, `MSGS_TA`, `T_ERR`, `QUEUE`, `DUPLICATES`, `EMBBADCRC`, `EMBBADDATA`, `EMBBADEXC`, `EMBUNKEXC`, `EMBMDATA`, `EMBBADSLAVE`.
- `MBDEVICERTU`: `DEVICE`, `RST_CNT`, `CONNECTED`, `PORT`, `SLAVEID`, `MSGS_TX`, `MSGS_RX`, `MSGS_TO`, `MSGS_TA`, `T_ERR`, `EMBBADCRC`, `EMBBADEXC`, `EMBBADDATA`, `EMBUNKEXC`, `EMBMDATA`, `EMBBADSLAVE`.
- `MBDEVICETCP`: `DEVICE`, `RST_CNT`, `ADDRESS`, `PORT`, `WINDOW`, `TIMOUT`, `CONNECTED`, `MSGS_TX`, `MSGS_RX`, `MSGS_TO`, `PENDING`, `QUEUE`, `DUPLICATES`.

## OPC UA Blocks

- VC024SA describes Studio working with external OPC servers and an internal server automatically created at runtime start.
- VC024SA describes the internal OPC server as available to external clients, but actual runtime availability and port behavior must be verified against VCont config, active OPC UA blocks, and the current binary.
- Blocks: `CLIENT`, `SUBSCRIBE`, `PUBLISH`.
- Blocks have variable port count, adjusted using the same `UserLibrary` copy/edit approach.
- Configure `CLIENT` with either only inputs or only outputs.

Common ID grammar:

```text
opc_ua[ACTION;opc.tcp://IP:Port#;Path,Namespace:IdentifierType=Identifier]
```

- Actions: `READ`, `WRITE`, `SUBSCRIBE`.
- Remote address example: `opc.tcp://IP-сервера:4840#`.
- Local server may omit IP and port.
- Default OPC UA port: `4840`.
- Path example: `/Objects/Tags/"Имя тега"`, `/Objects/TAGS/TAG1`.
- Namespace defaults to `0`; if omitted, the colon is omitted too.
- Identifier types: `i` numeric, `s` string, `b` byte string, `g` GUID.

`CLIENT`:

- Purpose: read/write tags on local or external OPC server by event.
- Ports: `INIT`, `REQ`, `QI`, `ID`, `SD_1...`, `RD_1...`, `QO`, `STATUS`.
- `INIT`: if `QI=TRUE`, reads `ID` and connects; if `QI=FALSE`, disconnects.
- `REQ`: read/write request.
- `QO`: quality of read/write.
- Example ID: `opc_ua[WRITE;opc.tcp://IP-сервера:4840#;/Objects/TAGS/TAG1,0:s=TAG1;/Objects/TAGS/TAG2,0:s=TAG2]`.

`SUBSCRIBE`:

- Purpose: read tags only when values update on server.
- No data inputs; document phrase has a typo but meaning is no value inputs.
- Ports: `INIT`, `RSP`, `QI`, `ID`, `RD_1...`, `QO`, `STATUS`.
- `RSP` is documented as unused.
- Example ID: `opc_ua[SUBSCRIBE;opc.tcp://IP-сервера:4840#;/Objects/TAGS/TAG1,0:s=TAG1;/Objects/TAGS/TAG2,0:s=TAG2]`.

`PUBLISH`:

- Purpose: create/write OPC tags on the local server only.
- Only value inputs.
- Ports: `INIT`, `REQ`, `QI`, `ID`, `SD_1...`, `QO`, `STATUS`.
- Local example: `opc_ua[WRITE;/objects/QT01,0:s=QT01;/objects/QT02,0:i=123456]`.

## Document Caveats To Preserve

- OPC UA is numbered again as `8.1`, conflicting with `8.1 Modbus`.
- Modbus TCP Server text says “настроить клиента” and mentions `Modbus TCP Client` in places although the section is about server.
- Table 6 says server name is used only in CODESYS; keep as document wording but treat as suspicious for VCStudio.
- `Modbus Serial Portrs` appears with a typo.
- `TIMOUT` is documented in diagnostic blocks; do not silently rename to `TIMEOUT` when answering about documented ports.
- `MBDEVIERTU` appears instead of `MBDEVICERTU` in several places; table numbering also has mistakes.
- `MBREAD_PACK` table reuses write wording and even `WD01`; verify current typelibrary for implementation details.
- `FORMAT` lists `S2` for both int and uint.
- OPC UA text has typos in `индификатора/Индификатор` and inconsistent spacing in `opc_ua [WRITE;`.
- Section 8 mentions `ETHERNET IP`, but the extracted text does not expand it.
