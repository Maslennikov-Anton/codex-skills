# Runtime Options

This reference describes VCont runtime `Options` strings used by generated IDE/XML commands and `vcont.fboot`.

## Syntax

Options are passed as a single space-separated string of key-value pairs:

```text
name1=value1 name2=value2
```

If a parameter has a default value and that value is acceptable, the parameter may be omitted; runtime should then use the default. Treat this as confirmed for `HsbAlg` and as the intended pattern for the option sets below unless current binaries prove otherwise.

Values are not described here as shell syntax. Do not add quotes, escaping, commas, or semicolons unless a specific runtime option format requires it. For paths or names containing spaces, verify current runtime support before relying on them.

## MBCLIENTTCP

Modbus TCP client.

| Parameter | Type | Required | Default | Constraints / values |
|---|---|---:|---|---|
| `Address` | string | yes | - | IPv4 address, for example `192.168.1.1` |
| `Port` | integer | no | `502` | `>= 1` |
| `SlaveId` | integer | no | `255` | `0..255` |
| `Window` | integer | no | `1` | `>= 1` |
| `Timeout` | integer | no | `1000` | `> 0`, milliseconds |
| `HsbAlg` | integer | no | `1` | `1` or `2` |

`HsbAlg` controls which HSB roles connect to the remote Modbus server at startup:

- `1`: `MAIN`, `STANDALONE`, and `RESERVE` connect at startup.
- `2`: only `MAIN` and `STANDALONE` connect at startup; `RESERVE` does not connect until it becomes active.

Example:

```text
Address=192.168.1.10 Port=502 SlaveId=1 Window=1 Timeout=1000 HsbAlg=2
```

## MBCLIENTRTU

Modbus RTU client over a serial port abstraction.

| Parameter | Type | Required | Default | Constraints / values |
|---|---|---:|---|---|
| `Port` | string | yes | - | Runtime port name/reference |
| `SlaveId` | integer | no | `255` | `1..247` |
| `Heartbeat` | string | no | `auto` | `auto`, `off` |

## MBCLIENTRTUOVERTCP

Modbus RTU protocol transported over TCP.

| Parameter | Type | Required | Default | Constraints / values |
|---|---|---:|---|---|
| `Address` | string | yes | - | IPv4 address |
| `Port` | integer | no | `502` | `>= 1` |
| `SlaveId` | integer | no | `255` | `0..247` |
| `Timeout` | integer | no | `1000` | `> 0`, milliseconds |

## MBSERIALPORT

Serial port definition used by Modbus RTU clients.

| Parameter | Type | Required | Default | Constraints / values |
|---|---|---:|---|---|
| `Device` | string | yes | - | Device path, for example `/dev/ttyUSB0` |
| `Baud` | integer | no | `9600` | `> 0` |
| `Parity` | char | no | `N` | `N`, `E`, `O` |
| `DataBit` | integer | no | `8` | `5..8` |
| `StopBit` | integer | no | `1` | `1`, `2` |
| `Delay` | integer | no | `0` | `0..10000`, milliseconds |
| `Timeout` | integer | no | `1000` | `> 0`, milliseconds |
| `Mode` | string | no | `RS232` | `RS232`, `RS485` |
| `RTS` | string | no | `OFF` | `ON`, `OFF` |

## MBSERVER

Built-in Modbus server.

| Parameter | Type | Required | Default | Constraints / values |
|---|---|---:|---|---|
| `Address` | string | yes | - | Bind address |
| `Port` | integer | yes | - | `1..65535` |
| `Mode` | string | yes | - | Runtime-supported mode, commonly `tcp` or `rtu` |
| `SlaveId` | integer | yes | - | `0..247` |

Example:

```text
Address=0.0.0.0 Port=1502 Mode=tcp SlaveId=1
```

## EIPDEV

EtherNet/IP device.

| Parameter | Type | Required | Default | Constraints / values |
|---|---|---:|---|---|
| `Period` | integer | yes | - | `<> 0`, milliseconds |
| `IP` | string | yes | - | IPv4 address |
| `Interface` | string | yes | - | Network interface name; checked in the system |
| `OTAssembly` | integer | yes | - | `1..255` |
| `TOAssembly` | integer | yes | - | `1..255` |
| `ConfAssembly` | integer | yes | - | `1..255` |
| `CPU` | integer | no | `0` | Intended `>= 1`; otherwise warning |
| `Priority` | integer | no | `-1` | Runtime priority value |
| `RTformat` | string | no | `true` | `true`, `false` |

## KNXDEV

KNX device.

| Parameter | Type | Required | Default | Constraints / values |
|---|---|---:|---|---|
| `IndividualAddr` | string | yes | - | KNX individual address |
| `GroupAddr` | string | yes | - | Group address with DPT information |
| `Interface` | string | no | - | Network interface name |

## PRBDEV

PROFIBUS device.

| Parameter | Type | Required | Default | Constraints / values |
|---|---|---:|---|---|
| `Config` | string | yes | - | `/path/file.xml:idx1:idx2;name1;name2` |

