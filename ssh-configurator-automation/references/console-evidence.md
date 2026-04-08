# Консольные Доказательства

Ниже собрана связка `UI action -> SSH command -> observed response` по данным из встроенной консоли приложения.

Источник: `TheConsole.vue` рендерит `consoleState.items`, а `runSSHCommand()` всегда пишет в этот store итоговую команду, ответ и error state.

## Подтверждённые успешные команды

### Подключение

- UI: подключение через диалог `Настройки SSH`
- Консоль:
  - `connect`
  - `check_host_type`
  - `check_host_type`
- Наблюдение:
  - второй `check_host_type` вернул `Runtime-VM`

### Дата и время

- UI: `/system-settings/datetime` -> `Запросить`
- Команда: `date_time`
- Ответ:
  - `2026-04-08 15:43:11`

### Часовой пояс

- UI: `/system-settings/datetime` -> `Запросить` для timezone
- Команда: `timezone`
- Ответ:
  - `Europe/Moscow`

### Изоляция ядер

- UI: `/system-settings/kernel-isolation` -> `Запросить`
- Команда: `get_cpu_qty`
- Ответ:
  - `Logical CPUs: 2`
  - `Physical cores: 2`

### Диагностика

- UI: `/diagnostics` -> `Выполнить`
- Команда: `check_status systemd-journald`
- Ответ:
  - журнал `systemd-journald`
  - начало ответа:
    - `Last 50 log messages`

### Ключи

- UI: `/keys` -> `Вывести список ключей`
- Команда: `list_user_keys`
- Ответ:
  - `Listing all SSH keys in /home/service/.ssh/authorized_keys:`
  - `ssh-ed25519 ... vcont_initial`

## Подтверждённые ошибки и ограничения на текущем Runtime-VM

### Управление ВМ

- UI: `/manage/vm/management` -> `Вывести список`
- Команда: `list_vms`
- Ответ:
  - `Command not found: list_vms`

Вывод:
- экран существует в UI
- но backend-команда на текущем хосте не поддерживается

### Список XML

- UI: `/manage/vm/xmls` -> `Вывести список`
- Команда: `list_files_by_directory xml`
- Ответ:
  - `Directory '/var/lib/libvirt/xml_store' does not exist or is not a directory.`

Вывод:
- логика экрана есть
- но на текущем хосте соответствующая директория отсутствует

### Список образов

- UI: `/manage/vm/images` -> `Вывести список`
- Команда: `list_files_by_directory images`
- Ответ:
  - `Directory '/var/lib/libvirt/images' does not exist or is not a directory.`

### Сгруппированные файлы

- UI: `/manage/vm/grouped-files` -> `Вывести список`
- Команда: `group_files_by_type_and_vm`
- Ответ:
  - `Command not found: group_files_by_type_and_vm`

### PCI devices

- UI: `/manage/vm/pci-devices` -> `Вывести список`
- Команда: `list_pci_devices_by_iommu_group`
- Ответ:
  - `Failed to read IOMMU groups directory`

## Соединение и потери соединения

В консоли уже наблюдались реальные ошибки соединения:

- `connection_lost`
  - `Shell channel ended`
  - `Connection closed`

Это полезно для будущих сценариев автоматической диагностики связи.

## Практический смысл

- Если UI-таблица пуста, сначала проверять консоль:
  - это действительно пустой результат
  - или backend-команда завершилась ошибкой
- Для VM-разделов на текущем `Runtime-VM` уже доказано, что часть команд либо отсутствует, либо опирается на директории libvirt, которых здесь нет.
- Для безопасного исследования дальше полезно после каждого действия автоматически читать последние console entries, а не полагаться только на DOM.
