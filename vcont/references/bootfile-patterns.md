# VCont Bootfile Patterns

`vcont.fboot` - текстовый сценарий XML-команд IDE рядом с бинарником VCont. Используй эти patterns как skeleton; конкретные типы ФБ, пины и alias-регистры сверяй с текущей typelibrary и задачей.

## Guardrails

- Имя файла для runtime-startup path: `vcont.fboot`.
- Порядок `CREATE FB` внутри лупа семантически важен и задает исходную очередность исполнения.
- Если блок `B` должен видеть результат `A` в том же цикле, создай `A` раньше `B` или используй `ASSIGN Before`.
- Пустой task ничего не исполняет: луп нужно назначить на task, затем запустить task.
- HSB не синхронизирует проект: одинаковую или совместимую программу нужно загрузить во все VCont-инстансы.

## Minimal Task And Loop

```xml
;<Request ID="1" Action="CREATE"><FB Name="mainTask" Type="TASK_RES" Options="Period=100" /></Request>
;<Request ID="2" Action="CREATE"><FB Name="APPLICATION1.LOOP1.SOURCE" Type="SOURCE_TYPE" /></Request>
;<Request ID="3" Action="CREATE"><FB Name="APPLICATION1.LOOP1.PROCESS" Type="PROCESS_TYPE" /></Request>
;<Request ID="4" Action="CREATE"><Connection Source="APPLICATION1.LOOP1.SOURCE.OUT" Destination="APPLICATION1.LOOP1.PROCESS.IN" /></Request>
mainTask;<Request ID="5" Action="ASSIGN"><Subcontainer Name="APPLICATION1.LOOP1" /></Request>
mainTask;<Request ID="6" Action="START"></Request>
```

## Explicit Execution Order

Если порядок создания не совпадает с нужным порядком исполнения:

```xml
;<Request ID="10" Action="ASSIGN"><FB Name="APPLICATION1.LOOP1.PROCESS" Before="APPLICATION1.LOOP1.SINK" /></Request>
```

## Stable Read Pattern

Для тестов, где нужен стабильный snapshot пользовательской программы, останови task, прочитай пины через IDE `READ`, затем запусти task обратно.

```xml
mainTask;<Request ID="20" Action="STOP" />
mainTask;<Request ID="21" Action="START" />
```

## HSB Pattern

- Клади `vcont.fboot` рядом с бинарником каждого узла до запуска.
- Для одинаковой программы копируй один bootfile во все `.work/vcont-runtime/vcontN/.../vcont.fboot`.
- Для node-specific поведения используй fixture mapping по сервисам, например `{"vcont1": "main.vcont.fboot", "vcont2": "reserve.vcont.fboot"}`.
- Failover oracle проверяй по синхронизируемым DI/DO или внешнему эффекту, а не по внутреннему event-task контексту.

## Modbus Counter Pattern

- Для external Modbus failover используй синхронизируемые counters/values, которые пишутся во внешние holding registers.
- В локальном `vcont-hsb` stand известные registers для failover assertions: `2048..2050`.
- Oracle: после takeover нет zero reset, значения продолжают шаг `+1`.

## Trial Caveat

- Trial Lite (`tria-lite`) не грузит `vcont.fboot`.
- Demo / Trial Full (`tria-full`) может грузить `vcont.fboot`, но имеет demo limits.
