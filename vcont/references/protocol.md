# Протокольные заметки

Для общей границы Studio(front)/VCont(back), lifecycle и object mapping см. `studio-vcont-contract.md`.

Для ST->Lua qualification сценариев проверочный минимум: загрузить Lua-backed FB так же, как Studio или `vcont.fboot`, создать instance под application/loop path, назначить loop на task, выполнить `START`, затем читать outputs через IDE `READ`. Если generated Lua переводится, но `READ` возвращает `NO_SUCH_OBJECT`, `UNSUPPORTED_TYPE` или не достигает oracle, это runtime/load-path signal, а не повод считать standalone translation достаточной проверкой.

## Модель взаимодействия VCont и VCStudio

Инициатором связи выступает VCStudio. Команды отправляются в VCont TCP-пакетами на адрес/порт, заданный параметром `IpPort` в `vcontcfg.json`.

Ответы VCont бывают двух типов:

- простой ответ, который показывает успешность выполнения команды;
- сложный ответ, который содержит запрошенную информацию, например результат чтения или список объектов.

Перечень команд основан на IEC 61499-1-2012 и расширен продуктовой версией VCont.

## TCP/TLS framing: качество и длина строки

`sendREQ` передаёт две строки: destination и XML request. Ответ — одна строка с XML response. При диагностике проверяй **две независимые настройки формата**: наличие поля качества и ширину длины. Правильной ширины длины недостаточно для совместимости.

| Формат строки | Байты до UTF-8 payload | Заголовок при length=4 |
| --- | --- | --- |
| Прежний, без качества | `50 + length + payload` | 5 байт |
| С качеством | `50 + quality:uint16be + length + payload` | 7 байт |

В сборках, проверенных 6 ноября 2026, Studio пишет `quality=0` (`writeShort(0)`) **перед длиной в каждой из двух строк**, а TCP- и TLS-PSK `handleResponse` читают и пропускают это поле. Например, `abc` в extended mode: `50 00 00 00 00 00 03 61 62 63`. Весь sendREQ вырос на 4 байта относительно прежнего extended-формата.

Это поле **качества данных**, а не расширение длины, TLS-префикс или произвольный padding. В VCont подтверждены `serializeQuality`/`deserializeQuality`: 2 байта big-endian, принимаются коды 0..3; значения >3 отвергаются. Названия и прикладная семантика кодов 1..3 этим исследованием не установлены — не присваивай им значения good/bad по догадке. Перехватчик должен сохранять исходные байты и код качества; получение quality само по себе не доказывает загрузку или корректность значения.

Ширина **самого length** по-прежнему выбирается отдельно:

- regular: 2 байта unsigned big-endian, до 65535 байт payload; с quality заголовок 5 байт;
- extended/large: 4 байта unsigned big-endian; с quality заголовок 7 байт;
- `ExtraPreferences.isUseExtendedLength()` в Studio должен соответствовать `mBytesHeader` / `LARGE_CIEC_STRING` в VCont;
- длина считается по UTF-8 **байтам**, не по числу символов. Tag/quality/length не входят в длину payload.

Из формата следует ещё одна ловушка: при quality=0 новая regular-строка (quality 2 + length 2) совпадает с прежней extended-строкой (length 4) для payload до 65535 байт. Один успешный короткий QUERY не определяет версию формата; проверяй сериализатор/bytecode конкретных артефактов.

Устаревший клиент `50 + uint32 length` на новой сборке может ждать ответ до таймаута: runtime ждёт недостающие данные пакета. Такой же перехватчик может завершиться `unexpected ... frame tag` до отправки первой команды и вызвать `Connection reset / Deployment failed` в Studio. Не трактуй это как продуктовый отказ загрузки, пока не проверен посредник.

### Проверенная область и источники

Подтверждено на VCStudio 1.25.2, bundle `1.25.2.202610210625`, и VCont 2.1.1.39714 (build 2026-11-06 09:16:33):

- Studio tar.gz SHA256 `915b105e175bb597536a8262cc01b79e59ab616a493f5ce1d1686e75a0f7f572`;
- VCont deb SHA256 `c3fd6c5138001827135feee1f4bebef465b2538d9c97d55067badf21ed9c9194`;
- runtime executable SHA256 `e8452c73bae0ba7f47b7c7af38b785a3fb00db99fd75daa35f9c4636de40b2ba`.

Локальные checkout VCont `0a3de2f7` и Studio `c181db764` этого поля ещё не содержат. Номер bundle/имя deb не определяют формат: проверяй поставленные артефакты.

Для повторной проверки распакуй deb в owned scratch без установки, найди `serializeQuality`, `deserializeQuality`, `serializeDataPoint`, `serializeValueString` и `deserializeValueString` через `nm -C`, затем изучи адреса через `objdump -d --demangle`. В поставленном Studio JAR используй `javap -c -p` для `EthernetDeviceManagementCommunicationHandler` и `TLSPSKDeviceManagementCommunicationHandler`: в `sendREQ` после `writeByte(80)` будет отдельный `writeShort(0)` перед `writeStringLength`; в `handleResponse` — отдельный `readShort` перед `readStringLength`.

Проверяй исключения отдельно: у исследованного Ethernet `sendPublicKey()` нет дополнительного quality-поля в отправляемом ключе, а `sendBytes()` пишет сырые байты. Не добавляй IDE-заголовок к загрузке файла/ключа автоматически.

Сохраняй предельный размер, чтение фрагментов TCP и общий deadline. Для другого артефакта выбирай подтверждённый формат явно; не делай эвристический fallback после таймаута. Известная ошибка маски `0xFF00` в некоторых source snapshots `VCONT-1627` также требует проверки конкретного бинарника.

## Загрузка программы через fboot

Когда пользователь в VCStudio выбирает загрузку полного проекта в ресурс или ресурсы, VCStudio должна сформировать `fboot`-файл для каждого ресурса. Каждый такой файл должен быть подписан ЭЦП.

Подписание `fboot` выполняется по схеме:

1. Рассчитать хэш-сумму `fboot`-файла.
2. Подписать хэш закрытым ключом на стороне VCStudio.
3. Передать на контроллер `fboot` вместе с сертификатом/подписью отправителя VCStudio.

Зафиксированные требования к криптографии из документа:

- ключи на первом этапе генерируются через `ssh-keygen` или аналогичное ПО;
- должен использоваться алгоритм EdDSA;
- открытый ключ при первичной настройке передается в VCont через конфигуратор;
- для расчета хэш-функции используется OpenSSL; в документе указан алгоритм `ES-256`.

Формулировка про `ES-256` сохранена как требование документа, но ее нужно уточнять при реализации: `ES256` обычно относится к ECDSA with SHA-256, а не к самостоятельной хэш-функции.

## Валидация fboot на стороне VCont

После получения `fboot` и сертификата/подписи VCStudio контроллер должен:

1. Рассчитать хэш от `fboot` тем же алгоритмом, который использовала VCStudio.
2. С помощью открытого ключа извлечь значение хэша из ЭЦП/сертификата VCStudio.
3. Сравнить рассчитанный и извлеченный хэши.

Если значения совпадают, контроллер применяет `fboot`. Если значения отличаются, VCStudio должно получить сообщение `e_NOT_READY`.

Операционные требования:

- все действия, связанные с загрузкой нового прикладного ПО в контроллер, должны логироваться с высоким/максимальным приоритетом;
- при расхождении хэшей должно генерироваться событие информационной безопасности с критичным приоритетом;
- рассчитанное значение хэша должно храниться на контроллере;
- запись и любые изменения сохраненного хэша разрешены только `root`-пользователям.

## Авторизация

Когда `UseAuth` включен, система исполнения проверяет перед выполнением команды, разрешена ли команда согласно текущей роли. Если роль отсутствует, выполнение команды запрещается.

VCStudio инициализирует роль при открытии сессии, отправляя `AUTH`-запрос. Точная схема передачи JWT/token в XML должна проверяться по текущей реализации клиента и runtime; не используй неподтвержденные XML-атрибуты или элементы для токена.

```xml
<Request ID="1" Action="AUTH"></Request>
```

После декодирования токена система исполнения контроллера инициализирует роль. Если токен некорректен, обрабатывается исключительная ситуация и дальнейшее выполнение команд невозможно.

Токен также содержит идентификатор пользователя для сессии. После выполнения команд сессия закрывается, а система исполнения контроллера деинициализирует роль.

## Шаблоны команд IDE

Команды IDE являются XML-запросами. Некоторые запросы имеют префикс имени таска/ресурса, например `TASK1;`.

### Создание функциональных блоков

Функциональные блоки создаются без привязки к исполняющему ресурсу/таску. Первоначальный порядок выполнения внутри лупа соответствует порядку команд создания.

Практическое правило для `vcont.fboot`: порядок `CREATE`-команд для `FB` является частью семантики программы. Runtime использует этот порядок как исходную очередность запуска/исполнения блоков внутри лупа до явного изменения через `ASSIGN Before`. Поэтому при генерации, форматировании или сравнении bootfile нельзя сортировать ФБ по имени, типу или зависимостям без осознанного изменения поведения. Если блок `B` должен видеть результат блока `A` в том же цикле, размещай `A` раньше `B` или добавляй явную команду изменения порядка.

```xml
;<Request ID="3" Action="CREATE"><FB Name="APPLICATION1.LOOP1.FB_RANDOM" Type="FB_RANDOM" /></Request>
;<Request ID="4" Action="CREATE"><FB Name="APPLICATION1.LOOP1.REAL2REAL" Type="REAL2REAL" /></Request>
;<Request ID="5" Action="CREATE"><FB Name="APPLICATION1.LOOP1.REAL2REAL_1" Type="REAL2REAL" /></Request>
;<Request ID="6" Action="CREATE"><FB Name="APPLICATION1.LOOP1.F_ADD" Type="F_ADD" /></Request>
```

### Запись литерала в пин

```xml
;<Request ID="7" Action="WRITE"><Connection Source="1233" Destination="APPLICATION1.LOOP1.FB_RANDOM.SEED" /></Request>
```

### Создание связей

```xml
;<Request ID="8" Action="CREATE"><Connection Source="APPLICATION1.LOOP1.REAL2REAL.OUT" Destination="APPLICATION1.LOOP1.F_ADD.IN1" /></Request>
;<Request ID="9" Action="CREATE"><Connection Source="APPLICATION1.LOOP1.FB_RANDOM.VAL" Destination="APPLICATION1.LOOP1.REAL2REAL_1.IN" /></Request>
;<Request ID="10" Action="CREATE"><Connection Source="APPLICATION1.LOOP1.FB_RANDOM.VAL" Destination="APPLICATION1.LOOP1.REAL2REAL.IN" /></Request>
;<Request ID="11" Action="CREATE"><Connection Source="APPLICATION1.LOOP1.REAL2REAL_1.OUT" Destination="APPLICATION1.LOOP1.F_ADD.IN2" /></Request>
```

### Изменение порядка выполнения внутри лупа

Изменения порядка запрашиваются без привязки к исполняющему таску и влияют только на ФБ внутри указанного лупа. Это штатный способ зафиксировать очередность, если порядок создания ФБ в bootfile не совпадает с нужной очередностью исполнения.

```xml
;<Request ID="16" Action="ASSIGN"><FB Name="APPLICATION1.LOOP1.REAL2REAL_1" Before="APPLICATION1.LOOP1.REAL2REAL" /></Request>
```

Пример перемещает `REAL2REAL_1` перед `REAL2REAL`.

### Создание исполняющего ресурса/таска

```xml
;<Request ID="2" Action="CREATE"><FB Name="TASK1" Type="TASK_RES" Options="Period=1000"/></Request>
```

Опции таска:

- `Period`: период таска в миллисекундах, целочисленное значение.
- `CPU`: битовая маска ядер CPU для привязки исполняющего потока таска. Ядра нумеруются с 1. Примеры: `CPU=1` означает первое ядро, `CPU=2` - второе ядро, `CPU=3` - первое и второе ядра, `CPU=4` - третье ядро.

Если `CPU` отсутствует, поток таска не является realtime-потоком, а планирование и назначение CPU выполняются по правилам ОС.

Общее правило для `Options`: параметры передаются одной строкой вида `name1=value1 name2=value2`. Если параметр имеет подходящее значение по умолчанию, его можно не указывать. Для runtime-устройств Modbus, EtherNet/IP, KNX и PROFIBUS см. `runtime-options.md`.

### Назначение лупа на таск

Пустой таск ничего не выполняет, даже если существует луп с упорядоченными ФБ. Чтобы таск начал выполнение, на него нужно назначить луп.

```xml
TASK1;<Request ID="17" Action="ASSIGN"><Subcontainer Name="APPLICATION1.LOOP1" /></Request>
```

На исполняющие ресурсы назначаются только лупы. Функциональные блоки напрямую не назначаются, потому что порядок их выполнения внутри таска был бы неизвестен.

На таск можно назначить несколько лупов.

### Перенос лупа на другой таск

```xml
TASK2;<Request ID="18" Action="ASSIGN"><Subcontainer Name="APPLICATION1.LOOP1" /></Request>
```

Когда `APPLICATION1.LOOP1` назначается на `TASK2`, среда исполнения ищет этот луп в других исполняющих ресурсах и удаляет его из предыдущего таска, например из `TASK1`.

## Каталог IDE-команд

Ниже компактный каталог команд, которые нужно учитывать при генерации `vcont.fboot` или при работе VCStudio/VCont по TCP. Префикс до `;` указывает целевой ресурс/таск, если команда выполняется в контексте ресурса.

### Таски и ресурсы

Создать таск:

```xml
;<Request ID="1" Action="CREATE"><FB Name="T" Type="TASK_RES" Options="Period=100 CPU=2" /></Request>
```

Запустить таск:

```xml
T;<Request ID="1" Action="START"></Request>
```

Остановить таск:

```xml
T;<Request ID="1" Action="STOP"></Request>
```

Практический вариант для снятия стабильного состояния пользовательской программы: остановить исполняющий таск, прочитать нужные пины через IDE `READ`, затем снова запустить таск. Для типового `mainTask`:

```xml
mainTask;<Request ID="17" Action="STOP" />
<Request ID="18" Action="READ"><Connection Source="APPLICATION1.LOOP1.CNT_A.OUT" Destination="*"/></Request>
mainTask;<Request ID="19" Action="START" />
```

Инициализировать ресурс:

```xml
<Request ID="1" Action="INITIALIZE"></Request>
```

Сбросить ресурс:

```xml
<Request ID="1" Action="REMOVERES"></Request>
```

Перезагрузить ресурс:

```xml
<Request ID="107" Action="REBOOT"></Request>
```

Получить текущий Hot Standby статус runtime:

```xml
<Request ID="1" Action="HSBSTATUS"></Request>
<Response ID="1"><STATUS="STATE"/></Response>
```

`STATE` принимает значения:

- `MAIN`: текущий VCont является активным HSB-узлом.
- `RESERVE`: текущий VCont является резервным HSB-узлом.
- `STANDALONE`: HSB включен, но узел работает как одиночный активный контроллер.
- `NONE`: HSB-опция выключена.

Для диагностики HSB это прямой runtime-запрос и более точный источник текущей роли, чем парсинг строк `Global mode changed...` из логов. В тестах опрашивай `HSBSTATUS` на каждом VCont-инстансе отдельно; команда возвращает локальный статус конкретного runtime, а не состояние всего кластера.

### Функциональные блоки

Создать ФБ:

```xml
T;<Request ID="1" Action="CREATE"><FB Name="A.L.B" Type="FBTYPE" /></Request>
```

Запустить ФБ:

```xml
T;<Request ID="1" Action="START"><FB Name="A.L.B" Type="FBTYPE"/></Request>
```

Остановить ФБ:

```xml
T;<Request ID="1" Action="STOP"><FB Name="A.L.B" Type=""/></Request>
```

Удалить ФБ:

```xml
T;<Request ID="1" Action="DELETE"><FB Name="A.L.B" Type="FBTYPE"/></Request>
```

Запросить перечень задач/ФБ:

```xml
;<Request ID="1" Action="QUERY"><FB Name="*" Type="*"/></Request>
```

### Связи, параметры и порядок выполнения

Создать связь:

```xml
;<Request ID="1" Action="CREATE"><Connection Source="A1.L1.B1.P1" Destination="A2.L2.B2.P2" /></Request>
```

Удалить связь:

```xml
;<Request ID="1" Action="DELETE"><Connection Source="A1.L1.B1.P1" Destination="A2.L2.B2.P2" /></Request>
```

Прочитать значение параметра:

```xml
T;<Request ID="1" Action="READ"><Connection Source="A.L.B.P" Destination=""/></Request>
```

Практическое наблюдение по VCont `1.1.0.21308`: при отправке IDE-команды по TCP порядок атрибутов `Request` важен для парсера. Рабочий вариант:

```xml
<Request ID="2" Action="READ"><Connection Source="APP001.LOOP010.CNT_A.OUT" Destination="*"/></Request>
```

Вариант с `Action` перед `ID`, например `<Request Action="READ" ID="2">...`, возвращал `UNSUPPORTED_CMD`. Такой порядок может появляться при генерации XML через `xmltodict.unparse`, поэтому для отладки IDE-команд лучше формировать XML явно или проверять итоговую строку перед отправкой.

TCP framing команды:

```text
0x50 0x00 <len-prefix> <prefix> 0x50 0x00 <len-xml> <xml>
```

Для чтения без префикса первый блок имеет длину `0`: `P\x00\x00`.

Практическое наблюдение по локальным автотестам и VCont `1.1.0.21308`: `vcont-common-tools.common.tools.to_message` формирует длину как один байт:

```python
bytes([80, 0, len(part_before_xml)]) + part_before_xml + bytes([80, 0, len(part_xml)]) + part_xml
```

Поэтому для ручной отладки коротких IDE-команд используй такой же framing. Если нужно читать много параметров, безопаснее отправлять несколько коротких `READ`, а не один длинный XML, который может выйти за однобайтовую длину.

Ответ `READ` кладет прочитанное значение в `Destination`:

```xml
<Response ID="2">  <Connection Source="APP001.LOOP010.CNT_A.OUT" Destination="16" /></Response>
```

При парсинге ответа сначала извлекай полный `<Response>...</Response>`. Не обрезай строку на первом `/>`, потому что `<Connection ... />` внутри ответа самозакрывающийся.

Записать значение параметра:

```xml
T;<Request ID="1" Action="WRITE"><Connection Source="VALUE" Destination="A.L.B.P"/></Request>
```

Изменить порядок выполнения ФБ внутри лупа:

```xml
;<Request ID="1" Action="ASSIGN"><FB Name="A1.L1.B1" Before="A1.L1.B2"/></Request>
```

Изменить порядок выполнения лупов:

```xml
;<Request ID="1" Action="ASSIGN"><FB Name="A1.L1" Before="A2.L2" /></Request>
```

### Watch/list просмотра

Добавить параметр в лист просмотра:

```xml
T;<Request ID="1" Action="CREATE"><Watch Source="A.L.B.P" Destination=""/></Request>
```

Запросить параметры в листе просмотра:

```xml
;<Request ID="1" Action="READ"><Watches/></Request>
```

Удалить параметр из листа просмотра:

```xml
T;<Request ID="1" Action="DELETE"><Watch Source="A.L.B.P" Destination=""/></Request>
```

### Лупы, aliases и Modbus server

Назначить луп таску:

```xml
T;<Request ID="1" Action="ASSIGN"><Subcontainer Name="A.L" /></Request>
```

Создать alias:

```xml
T;<Request ID="1" Action="CREATE"><Alias Source="A.L.B.P" Destination="ALIAS_NAME"/></Request>
```

Создать Modbus server:

```xml
<Request ID="1" Action="CREATE"><FB Name="MBS" Type="MBSERVER" Options="..."/></Request>
```

Запустить Modbus server:

```xml
MBS;<Request ID="1" Action="START"/>
```

### Сохранение и загрузка boot

Сохранить базу загрузки:

```xml
<Request ID="107" Action="DBSAVE"></Request>
```

Авторизовать сессию или выполнение команды:

```xml
<Request ID="1" Action="AUTH"></Request>
```

Загрузить файл перед выполнением boot:

```xml
<Request ID="1" Action="LOADFILE"></Request>
```

Выполнить boot-файл:

```xml
<Request ID="1" Action="EXECBOOT"></Request>
```

`LOADFILE` выполняется перед `EXECBOOT`.
