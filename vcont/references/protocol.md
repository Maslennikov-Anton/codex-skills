# Протокольные заметки

## Модель взаимодействия VCont и VCStudio

Инициатором связи выступает VCStudio. Команды отправляются в VCont TCP-пакетами на адрес/порт, заданный параметром `IpPort` в `vcontcfg.json`.

Ответы VCont бывают двух типов:

- простой ответ, который показывает успешность выполнения команды;
- сложный ответ, который содержит запрошенную информацию, например результат чтения или список объектов.

Перечень команд основан на IEC 61499-1-2012 и расширен продуктовой версией VCont.

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

VCStudio инициализирует роль при открытии сессии, отправляя `AUTH`-запрос:

```xml
;<Request ID="1" Action="AUTH">
<token="JWT_TOKEN_VALUE"></Request>
```

После декодирования токена система исполнения контроллера инициализирует роль. Если токен некорректен, обрабатывается исключительная ситуация и дальнейшее выполнение команд невозможно.

Токен также содержит идентификатор пользователя для сессии. После выполнения команд сессия закрывается, а система исполнения контроллера деинициализирует роль.

## Шаблоны команд IDE

Команды IDE являются XML-запросами. Некоторые запросы имеют префикс имени таска/ресурса, например `TASK1;`.

### Создание функциональных блоков

Функциональные блоки создаются без привязки к исполняющему ресурсу/таску. Первоначальный порядок выполнения внутри лупа соответствует порядку команд создания.

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

Изменения порядка запрашиваются без привязки к исполняющему таску и влияют только на ФБ внутри указанного лупа.

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
