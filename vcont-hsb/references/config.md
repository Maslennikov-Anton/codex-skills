# vcontcfg.json

## Правила загрузки

Конфигурационный файл среды исполнения выбирается в таком порядке:

1. Параметр командной строки: `-c "path-to-file"`.
2. Если параметр отсутствует, используется `vcontcfg.json` в той же директории, что и `vcont`.
3. Если файл тоже отсутствует, используются встроенные значения по умолчанию.

## Структура по умолчанию

```json
{
  "IpPort": "localhost:61499",
  "SizeFileLog": 104857600,
  "MaxBackupFiles": 4,
  "PathFileLog": "./vcont.log",
  "LevelLog": "info",
  "RealtimeMode": "auto",
  "EventQueueSize": 256,
  "EventQueueEnqueuePolicy": "DropDuplicatesAndFlush",
  "OpcuaServerPort": 4840,
  "OpcuaClientConfigFile": "",
  "DiagnosticsPeriod": 1000,
  "DiagnosticsIface": "*",
  "DebugLibmodbus": "off",
  "AutoDBSaveInterval": 0,
  "LoadDBAtStartup": 1,
  "SaveOutputs": 0,
  "UseMutualTls": 0,
  "CaCert": "./certs/ca/ca_cert.pem",
  "ServerCert": "./certs/server/server_cert.pem",
  "KeyCert": "./certs/server/private/server_key.pem",
  "UseAuth": false,
  "PlcId": 1,
  "EcalPath": "/etc/ecal/ecal.ini",
  "HsbEnable": 0,
  "HsbResourceName": "",
  "HsbSectionName": "hsb_network",
  "HsbSyncTimeout": 1000,
  "HsbMaxMissedHeartbeats": 2,
  "HsbHeartbeatPeriod": 10,
  "HsbMaxNodes": 3,
  "HsbConnErrorsToFailover": 2,
  "HsbCountOnlyHardConnErrors": 1,
  "HsbIgnoreDeviceState": 1,
  "HsbProbeConnectForAll": 0,
  "HsbNetDiagEnable": 0,
  "HsbNetDiagPeriodMs": 200,
  "HsbNetDiagInterfaces": ""
}
```

## Общие параметры

- `IpPort`: адрес сетевого интерфейса и порт, на котором VCont принимает команды от VCStudio.
- `SizeFileLog`, `MaxBackupFiles`, `PathFileLog`, `LevelLog`: настройки логирования на базе quill.
- `RealtimeMode`: поведение realtime-режима.
  - `reatlime`: включает realtime-механизмы, включая привязку к CPU и realtime-приоритет для тасков, где привязка к CPU задана явно. В исходном PDF значение написано именно как `reatlime`.
  - `emulator`: отключает realtime-механизмы даже для тасков с явной привязкой к CPU.
  - `auto`: определяет наличие Linux RT patch и использует realtime при наличии, иначе emulator.
- `EventQueueSize`: размер очереди событий для одного событийного таска.
- `EventQueueEnqueuePolicy`: стратегия добавления событий в очередь.
  - `DropOne`: когда очередь заполнена, новое событие не добавляется.
  - `DropDuplicates`: как `DropOne`, но дубликаты событий, уже находящиеся в очереди, также не добавляются.
  - `DropDuplicatesAndFlush`: как `DropDuplicates`, но при переполнении вся очередь очищается.
- `OpcuaServerPort`, `OpcuaClientConfigFile`: тонкая настройка встроенного OPC UA сервера/клиента; актуальна только при работе соответствующего функционального блока.
- `DiagnosticsPeriod`: период обновления диагностики в миллисекундах для системных метрик и диагностики тасков VCont. Значение по умолчанию - 1000 мс.
- `DiagnosticsIface`: селектор интерфейса диагностики.
- `DebugLibmodbus`: дополнительное логирование libmodbus, значения `on` или `off`.
- `AutoDBSaveInterval`: период автосохранения проекта в SQLite в секундах. `0` отключает автосохранение.
- `SaveOutputs`: сохранять ли данные выходных ножек функциональных блоков. `1` - сохранять, `0` - не сохранять.
- `LoadDBAtStartup`: загружает значения функциональных блоков при старте.
- `UseMutualTls`: включает mutual TLS.
- `CaCert`, `ServerCert`, `KeyCert`: пути к сертификатам для mutual TLS.
- `UseAuth`: включает или отключает авторизацию команд.
- `PlcId`: номер ПЛК в резервной паре/кластере. Используется логикой голосования; большее значение имеет больший приоритет.
- `EcalPath`: путь к `ecal.ini`.

## HSB-параметры

- `HsbEnable`: включает Hot Standby (`1`) или отключает его (`0`).
- `HsbResourceName`: имя топика/ресурса для связи внутри резервной пары. Если в одной сети находятся разные резервные пары, используй уникальные значения. Обычно равно имени ресурса.
- `HsbSectionName`: имя секции параметров сетевого интерфейса в `ecal.ini`; значение по умолчанию в исходных документах - `hsb_network`.
- `HsbSyncTimeout`: таймаут ожидания ответа синхронизации.
- `HsbMaxMissedHeartbeats`: число пропущенных heartbeat, после которого другой инстанс VCont считается offline.
- `HsbHeartbeatPeriod`: пауза перед отправкой следующего heartbeat.
- `HsbMaxNodes`: максимальное число контроллеров в резервной группе, от 1 до 3.
- `HsbConnErrorsToFailover`: число ошибок подключения Modbus, запускающее HSB failover.
- `HsbCountOnlyHardConnErrors`: учитывать для HSB failover только серьезные ошибки подключения Modbus.
- `HsbIgnoreDeviceState`: игнорировать состояние устройства Modbus для HSB failover.
- `HsbProbeConnectForAll`: разрешить проверку подключения Modbus во всех HSB-режимах.
- `HsbNetDiagEnable`: включить сетевую диагностику HSB.
- `HsbNetDiagPeriodMs`: период сетевой диагностики HSB в миллисекундах.
- `HsbNetDiagInterfaces`: отслеживаемые HSB-интерфейсы, разделенные запятой или пробелом, например `enp0s3,enp0s8`.
