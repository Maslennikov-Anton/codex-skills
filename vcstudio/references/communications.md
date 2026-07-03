# VCStudio Communications

This file describes Studio-side communication setup. For VCont runtime surfaces produced by that setup, such as `MBSERVER`, aliases, `_PACK` status codes, and OPC UA ID execution, see `studio-vcont-contract.md` and the VCont runtime references.

The current PDF lists these supported communication surfaces:

- Modbus RTU Master over RS-485/RS-232;
- Modbus TCP Client/Server; Modbus TCP Client may connect to Modbus RTU Slave devices through a TCP->RTU gateway-converter setup;
- OPC UA;
- ETHERNET IP, listed but not expanded in the extracted communication chapter.

## Общий Modbus Workflow

Для Modbus algorithms:

1. В resource настроить связь: Modbus RTU через `Modbus Serial` или Modbus TCP через `Modbus TCP`.
2. Создать application.
3. Добавить control loop.
4. В editor loop создать algorithm с blocks из `Communication\Modbus`.

## Modbus RTU Master

Resource editor -> `Modbus Serial`.

`Modbus Serial Ports`: каждый port - отдельная physical line. Port должен физически существовать на controller; для RS можно использовать USB port с RS converter.

Параметры serial port: имя порта (`COM1`, `ttyS0`, `ttyUSB0`, `ttyRS485_1`), скорость (`9600`..`115200`), четность (`N`, `E`, `O`), bits (`8`, реже `7`), stop bits (`1`, иногда `2`).

`Modbus RTU Client`: каждая строка - one RTU slave с project name, port и slave/unit ID обычно `1..247`.

## Modbus TCP Client

Resource editor -> `Modbus TCP` -> table `Modbus TCP Client`.

Controller as client initiates exchange with remote Modbus TCP servers or RTU slaves through TCP->RTU gateway.

Параметры remote device:

- `Имя устройства`: project name, examples `SCADA_Panel`, `METER_A`;
- `IP-адрес`: remote device IP;
- `Порт`: standard `502`, or test/conflict ports like `1502`, `1505`;
- `ID`: usually `1..247`; required for TCP->RTU gateway;
- `Окно`: number of active in-flight requests. Usually `1` is recommended;
- `Таймаут`: response timeout ms, typical `1000..5000`.

## Modbus TCP Server

Controller can act as Modbus TCP server and publish FB port values into internal Runtime memory.

Server is added in resource editor tab `Modbus TCP`, table `Modbus TCP Server`. The current PDF describes server rows as using `Имя сервера` plus `Опции`; `IP-адрес` and `Порт` are shown as inactive for server setup. Put detailed server settings in `Опции` as `parameter=value`, for example `Address=0.0.0.0 Port=1505 Mode=tcp SlaveId=1`. `Address=0.0.0.0` means local/all interfaces. Runtime may later represent this as `MBSERVER` options; treat that as backend artifact, not as the primary GUI instruction.

Each Modbus TCP server has its own address space; `MBSRV1.QX1` is not equal to `MBSRV2.QX1`.

Address map:

| Register | Modbus address | Size | Access | Function | Types |
|---|---:|---:|---|---|---|
| `QX0-QX65535` | `0-65535` | 1 bit | RW | `01`, `05`, `15` | `BOOL` |
| `IX0-IX65535` | `0-65535` | 1 bit | RO | `02` | `BOOL` |
| `IW0-IW65535` | `0-65535` | 16 bit | RO | `04` | `INT`, `WORD` |
| `MW0-MW29999` | `0-29999` | 16 bit | RW | `03`, `06`, `16` | `INT`, `WORD` |
| `MD0-MD9999` | `30000-49998` | 32 bit | RW | `03`, `06`, `16` | `DINT`, `REAL` |
| `ML0-ML3750` | `50000-65000` | 64 bit | RW | `03`, `06`, `16` | `LINT`, `LREAL` |

## Publishing FB Ports To Modbus Memory

Studio can publish input/output ports of almost any FB into internal Runtime memory.

In control loop editor select FB, open `Свойства`, and set port field `Modbus` in format `ServerName.MemoryAddress`, for example `MBSRV1.QX1`. For BOOL values prefer `QX` or `IX` because they are 1-bit areas.

Second GUI method: double-click or right-click the `Modbus` field and use `Регистры`; the selector supports searching registers and renaming them before binding.

## Runtime Artifact Mapping

- `Modbus TCP Server` row in Studio becomes VCont runtime server configuration, commonly an `MBSERVER` FB/options in generated artifacts.
- Runtime `Options` are space-separated key-value pairs such as `Address=192.168.1.10 Port=502 SlaveId=1`. If a parameter has a suitable default, generated artifacts may omit it and let VCont use the default.
- `Modbus TCP Client` row in Studio becomes `MBCLIENTTCP` options. HSB-sensitive runtime parameter: `HsbAlg=1` connects `MAIN`, `STANDALONE`, and `RESERVE` at startup; `HsbAlg=2` connects only `MAIN` and `STANDALONE`.
- `Modbus Serial Ports` row becomes `MBSERIALPORT` options, and `Modbus RTU Client` row becomes `MBCLIENTRTU` options.
- FB port field `Modbus = MBSRV1.QX1` becomes a runtime Modbus alias/binding between the FB port and server register.
- Modbus TCP/RTU client rows provide device names/configuration used by `_PACK` blocks through their `DEVICE` input.
- `Connection alias` from Studio visual references is different from runtime XML `Alias` for Modbus server registers.

## Runtime Options Quick Reference

This section is the Studio-facing mirror of VCont runtime `Options`. Use it when explaining how Studio communication/device settings turn into generated artifacts.

General format:

```text
name1=value1 name2=value2
```

Parameters with suitable defaults may be omitted.

- `MBCLIENTTCP`: `Address` required IPv4; `Port` default `502`, `>=1`; `SlaveId` default `255`, `0..255`; `Window` default `1`, `>=1`; `Timeout` default `1000`, `>0` ms; `HsbAlg` default `1`, values `1` or `2`. `HsbAlg=1` means `MAIN`, `STANDALONE`, and `RESERVE` connect at startup; `HsbAlg=2` means only `MAIN` and `STANDALONE` connect at startup.
- `MBCLIENTRTU`: `Port` required string; `SlaveId` default `255`, `1..247`; `Heartbeat` default `auto`, values `auto`, `off`.
- `MBCLIENTRTUOVERTCP`: `Address` required IPv4; `Port` default `502`, `>=1`; `SlaveId` default `255`, `0..247`; `Timeout` default `1000`, `>0` ms.
- `MBSERIALPORT`: `Device` required path, for example `/dev/ttyUSB0`; `Baud` default `9600`, `>0`; `Parity` default `N`, values `N`, `E`, `O`; `DataBit` default `8`, values `5..8`; `StopBit` default `1`, values `1`, `2`; `Delay` default `0`, `0..10000` ms; `Timeout` default `1000`, `>0` ms; `Mode` default `RS232`, values `RS232`, `RS485`; `RTS` default `OFF`, values `ON`, `OFF`.
- `MBSERVER`: `Address` required; `Port` required, `1..65535`; `Mode` required; `SlaveId` required, `0..247`.
- `EIPDEV`: `Period` required, `<>0` ms; `IP` required IPv4; `Interface` required and checked in the system; `OTAssembly`, `TOAssembly`, `ConfAssembly` required, each `1..255`; `CPU` default `0`, intended `>=1` otherwise warning; `Priority` default `-1`; `RTformat` default `true`, values `true`, `false`.
- `KNXDEV`: `IndividualAddr` required; `GroupAddr` required with DPT information; `Interface` optional network interface name.
- `PRBDEV`: `Config` required, format `/path/file.xml:idx1:idx2;name1;name2`.

## MODBUS Function Blocks

Built-in library folder: `Communication\Modbus`.

`_PACK` blocks access allowed Modbus memory areas for read/write. Blocks with `DEVICE` diagnose connection state in realtime.

`MBWRITE` and `MBREAD` are marked obsolete in the document; prefer `MBWRITE_PACK` and `MBREAD_PACK` for Studio-created algorithms.

`MBWRITE_PACK` write functions: `05`, `06`, `15`, `16`.

`MBREAD_PACK` read functions: `01`, `02`, `03`, `04`.

Common control/config ports: `REQ`, `CNF`, `DEVICE`, `ENABLE`, `ADDRESS`, `FORMAT`, `STATUS`. Write packs use `WD01...` value inputs; read packs use `RD01...` value outputs in the local typelibrary. The PDF table for `MBREAD_PACK` incorrectly repeats write wording and `WD01`, so prefer typelibrary evidence for pin direction. `ADDRESS` format is `start_address:function`.

`MBWRITE_PACK1` and `MBREAD_PACK1` default to one data port. To change data port count, copy the existing block from `Communication\Modbus` into `UserLibrary`, rename/edit it using the generic variable-port workflow, and create variants such as `MBWRITE_PACK3` / `MBREAD_PACK3`.

Formats: `C` bool 1 bit, `F4` real 32 bit, `F8` lreal 64 bit, `S2` int/uint 16 bit, `S4` dint 32 bit.

Common status codes: `0` no connection/wrong fields, `1` OK, `101` illegal function, `102` illegal address, `103` illegal value or bad `FORMAT`, `104` slave failure, `105` acknowledge, `106` busy, `107` negative acknowledge, `108` parity, `110` gateway path unavailable, `111` gateway target no response, `112` bad CRC, `113` bad data, `114` illegal exception, `116` too much data, `117` response from wrong slave, `200+` user codes.

Diagnostic blocks:

- `MBSERIALDIAG`: diagnoses ports from `Modbus Serial Ports`; input focus `PORT`, `RST_CNT`, outputs include `CONNECTED`, `BAUD`, `PARITY`, `TIMOUT`, `DELAY` and counters/errors.
- `MBDEVICERTU`: diagnoses slave devices from `Modbus RTU Client`; input focus `DEVICE`, `RST_CNT`, outputs include `CONNECTED`, `PORT`, `SLAVEID` and counters/errors.
- `MBDEVICETCP`: diagnoses slave devices from `Modbus TCP Client`; input focus `DEVICE`, `RST_CNT`, outputs include `CONNECTED`, `ADDRESS`, `PORT`, `WINDOW`, `TIMOUT`, `PENDING`, `QUEUE`, `DUPLICATES`.

Recognize counters/errors `MSGS_TX`, `MSGS_RX`, `MSGS_TO`, `MSGS_TA`, `T_ERR`, `QUEUE`, `DUPLICATES`, `PENDING`, `EMBBADCRC`, `EMBBADDATA`, `EMBBADEXC`, `EMBUNKEXC`, `EMBMDATA`, `EMBBADSLAVE`. Preserve documented typo `TIMOUT` when answering about port names.

## OPC UA

VC024SA describes Studio working with external OPC servers and an internal OPC server that is automatically created at runtime start and available to external clients. For actual runtime availability and port behavior, answer conservatively: check `studio-vcont-contract.md`, VCont config, active OPC UA blocks, and the current binary.

Blocks:

- `CLIENT`: read/write tags on local or external OPC server by event;
- `SUBSCRIBE`: read tags only when values update on server;
- `PUBLISH`: create/write OPC tags on local server.

Common `ID` format:

```text
opc_ua[ACTION;opc.tcp://IP:4840#;/Objects/TAGS/TAG1,0:s=TAG1]
```

Actions: `READ`, `WRITE`, `SUBSCRIBE`. For local server, IP/port can be omitted. Namespace defaults to `0` if omitted. Identifier types: `i` numeric, `s` string, `b` byte string, `g` GUID.

Guardrails:

- `CLIENT` ports: `INIT` reads `ID` and connects when `QI=TRUE`, disconnects when `QI=FALSE`; `REQ` performs read/write; `SD_1...` are write inputs, `RD_1...` are read outputs, `QO` is operation quality, `STATUS` is status. Configure `CLIENT` with either only inputs or only outputs.
- `SUBSCRIBE` ports: `INIT`, `RSP`, `QI`, `ID`, `RD_1...`, `QO`, `STATUS`; document says `RSP` is unused and there should be no value inputs.
- `PUBLISH` ports: `INIT`, `REQ`, `QI`, `ID`, `SD_1...`, `QO`, `STATUS`; only value inputs and local server target.
