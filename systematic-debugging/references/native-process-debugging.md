# Зависания и падения процессов Linux/Python

Статус: `experimental`. Адаптировано из The Art of Debugging Stas Bekman (CC-BY-SA-4.0); источник и полный текст лицензии в [references/native-upstream.md](native-upstream.md). Это инструментальная ветка существующего RCA workflow.

## Выбери свидетельство по симптому

| Симптом | Следующая диагностика |
|---|---|
| Процесс жив, занят или ждет IO | Показания CPU/state и ограниченный `strace` по точному PID либо запуск disposable reproducer под трассировкой |
| Segfault в native коде/SWT/JNI | Существующий core и соответствующий binary/debug symbols; `gdb` backtrace всех потоков |
| Python завис | Stack dump через доступный `py-spy`/настроенный `faulthandler`; native frames при необходимости |
| JVM/Java deadlock | JVM thread dump соответствующим JDK-инструментом; C backtrace не заменяет Java stacks |
| Неверная shared library | Путь binary, `ldd`, symbol/version mismatch, фактический import path |
| Изменения Python не действуют | `sys.executable`, `package.__file__`, cwd/config; сначала докажи, что запущена нужная копия |

Работай с точным процессом и его дочерними PID, не выбирай «первый python» в общей системе. Пассивный stack/syscall evidence предшествует правке кода или изменению timing. Отсутствие одной ошибки в коротком окне не исключает ее вообще.

Для запуска одноразового reproducer:

```bash
strace -f -o /tmp/repro.strace -- /path/to/reproducer
gdb --batch -ex run -ex 'thread apply all bt full' --args /path/to/reproducer
```

Для уже существующего core:

```bash
gdb --batch -ex 'thread apply all bt full' /path/to/binary /path/to/core
```

Сохрани exit code, signal, точную команду/версию, PID, временное окно, binary/build ID и релевантный фрагмент evidence. Успешный exit самого gdb означает получение диагностики, а не исправность программы. Если `strace` ограничен `timeout`, exit 124 означает конец окна; проверь, что нужный trace реально записан.

Attach через gdb/gcore может приостановить процесс; частота tracing влияет на timing. Используй сначала disposable reproducer или уже собранный core. Не меняй системные `ptrace_scope`, core pattern, сервисы и VPN ради доступа. Не используй `kill -ABRT` как эквивалент non-destructive snapshot. При отказе ptrace сообщи границу доступа и выбери разрешенный запуск reproducer под debugger.

Проверяй права и секреты в trace/core перед передачей: process args, environment и read/write могут содержать credentials. Не включай `set -x` вокруг auth-команд. Контрольные crash/hang пилоты выполняй на собственных временных процессах; не на рабочем VCont/Studio.
