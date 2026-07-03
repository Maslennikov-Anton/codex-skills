# VCStudio FB Typelibrary

Этот reference описывает фактическую библиотеку функциональных блоков из
локального репозитория `/home/ant/IdeaProjects/vcstudio` и как пользоваться
полным встроенным catalog.

Полный self-contained snapshot лежит в `fb-typelibrary-catalog.md`. Не открывай
его целиком без необходимости: файл большой. Для конкретного блока сначала ищи
по имени:

```bash
rg -n "^[-] `EIPDIAG`|EIPDIAG" /home/ant/codex-skills/vcstudio/references/fb-typelibrary-catalog.md
```

## Source

Источник snapshot:

`/home/ant/IdeaProjects/vcstudio/data/typelibrary`

На 2026-05-27 в рабочей библиотеке типов найдено:

- `473` `.fbt` файла в `data/typelibrary`;
- `466` блока в `Library`;
- `7` блоков в `UserLibrary`;
- `.dtp` файлов внутри `data/typelibrary` не найдено.

Отдельно в `data/template` есть `7` шаблонных `.fbt` файлов и `Struct.dtp`.
Они не включены в catalog как рабочая библиотека типов, но полезны как пример
структуры новых блоков/типов.

Разбивка `.fbt` по структуре:

- `InterfaceOnly`: `449`
- `Basic`: `17`
- `Composite`: `6`
- `ServiceInterface`: `1`

Крупные разделы библиотеки:

- `Library/Communication/Common`
- `Library/Communication/EthernetIP`
- `Library/Communication/KNX`
- `Library/Communication/Modbus`
- `Library/Standart/Arithmetic`
- `Library/Standart/Comparison`
- `Library/Standart/Conversion/*`
- `Library/Standart/Counters`
- `Library/Standart/Logic`
- `Library/Standart/Pack`
- `Library/Standart/Selection`
- `Library/Standart/String`
- `Library/Standart/Time`
- `Library/Array`
- `Library/Data`
- `Library/Events`
- `Library/Process`
- `Library/Reconfig`
- `Library/System`
- `UserLibrary`

## FBT Format

Каждый `.fbt` - XML с корнем `FBType`.

Важные узлы:

- `FBType/@Name` - тип ФБ, который используется в bootfile как
  `CREATE <FB ... Type="..." />`.
- `FBType/@Comment` - краткое назначение блока.
- `Identification/@Classification` - раздел/класс блока, если указан.
- `InterfaceList/EventInputs/Event` - событийные входы.
- `InterfaceList/EventOutputs/Event` - событийные выходы.
- `Event/With/@Var` - data pins, синхронизированные с событием.
- `InterfaceList/InputVars/VarDeclaration` - входные data pins.
- `InterfaceList/OutputVars/VarDeclaration` - выходные data pins.
- `InterfaceList/InternalVars/VarDeclaration` - внутренние переменные, если есть.
- `BasicFB`, `SimpleFB`, `FBNetwork`, `Service` - признак реализации/типа ФБ в
  `.fbt` snapshot.

## Runtime Mapping

Для VCont bootfile и IDE XML:

- тип блока берется из `FBType/@Name`;
- имя экземпляра задается runtime path, например `APP001.LOOP010.EIPDIAG`;
- входной pin из `InputVars` можно использовать как `WRITE Destination`;
- выходной pin из `OutputVars` можно использовать как `READ Source`;
- связи создаются между output и input pins через `CREATE <Connection ... />`;
- event pins используются для event-flow и `START`/`REQ`/`CNF` patterns;
- `With` показывает, какие data pins логически относятся к событию.

Пример:

```xml
;<Request ID="1" Action="CREATE"><FB Name="APP.LOOP.EIPDIAG" Type="EIPDIAG" /></Request>
;<Request ID="2" Action="WRITE"><Connection Source="PLC_EIP" Destination="APP.LOOP.EIPDIAG.DEVICE" /></Request>
;<Request ID="3" Action="READ"><Connection Source="APP.LOOP.EIPDIAG.MSGS_RX" Destination="*" /></Request>
```

## Guardrails

- Не угадывай pin names. Сначала ищи тип ФБ в `fb-typelibrary-catalog.md`.
- `Comment` в `.fbt` часто краткий или пустой; semantics проверяй по VC024SA,
  generated `vcont.fboot`, runtime logs и тестам.
- `InterfaceOnly` не означает, что блок не работает. Это значит, что в repo
  snapshot видна только interface declaration; реализация может быть в VCont или
  generated runtime.
- Device blocks (`EIPDEV`, `KNXDEV`, Modbus device rows) могут иметь пустой
  `InterfaceList`; их конфигурация живет в runtime `Options`.
- `ANY` и `SyncAnyType="true"` означают, что строгий тип может определяться
  подключением/контекстом; при тестах проверяй фактический runtime type.
- Порядок ФБ в `vcont.fboot` остается runtime-семантикой. Catalog дает интерфейс,
  но не заменяет правила order/task assignment.

## High-Value Blocks For Current VCont Work

EtherNet/IP:

- `EIPDEV`: device block; интерфейс пустой, конфигурация через `Options`.
- `EIPCTRL`: `DEVICE`, `QI`; outputs `IP`, `DVVALID`, `UDPCYCLE`.
- `EIPDIAG`: `DEVICE`, `QI`, `RST_CNT`; outputs `DEVSTATUS`, `MSGS_RX`,
  `TMIN_RX`, `TMAX_RX`, `TAVG_RX`, `MSGS_TX`, `TMAX_TX`, `TMIN_TX`, `TAVG_TX`,
  `VENDORID`, `DEVICETYPE`, `PRODUCTCODE`, `REVISION`, `SERIALNUMBER`,
  `STATUS`, `PRODUCTNAME`.
- `EIPASMREAD`, `EIPASMWRITE`, `EIPDATA`: assembly read/write/data helpers.

Modbus:

- `MBREAD`, `MBWRITE`: large multi-address blocks with `QI`, `ID`, address/data
  pins and per-request quality/status outputs.
- `MBREAD_PACK_1`, `MBWRITE_PACK_1`: compact pack blocks with `DEVICE`,
  `ENABLE`, `ADDRESS`, `FORMAT`, data pins, `STATUS`.
- `MBDEVICETCP`, `MBDEVICERTU`, `MBDEVICERTUTCP`: diagnostics with connection
  counters and queue/timeout outputs.
- `UserLibrary/MBREAD_PACK_50`, `UserLibrary/MBWRITE_PACK_50`: expanded pack
  variants with 50 data pins.

Catalog/document discrepancy to preserve: the current PDF documents
`MBSERIALDIAG` and `MBDEVICERTU`, but the local catalog snapshot has no
`MBSERIALDIAG`, and local `.fbt` files for `MBDEVICERTU`/`MBDEVICERTUTCP`
declare `FBType Name="MBDEVICETCP"` in their XML. For exact pin names, prefer
`fb-typelibrary-catalog.md`; for product-document wording, preserve the PDF
names and mark the mismatch.

OPC UA / Common communication:

- `CLIENT_*`, `SERVER_*`, `PUBLISH_*`, `SUBSCRIBE_*`: `QI`, `ID`, `STATUS`,
  `QO`, `SD_*` and `RD_*` pins depending on variant.

UserLibrary additions:

- `ADD_3`, `AND_3`, `OR_3`, `XOR_3`, `MUX_3`
- `MBREAD_PACK_50`
- `MBWRITE_PACK_50`
