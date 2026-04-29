# Протокольные заметки

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
