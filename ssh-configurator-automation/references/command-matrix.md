# Матрица Экранов И Команд

Ниже сведена операционная модель приложения: `menu -> tab -> route -> UI action -> backend command -> риск`.

Источник:

- backend spec: [backend-commands.json](backend-commands.json)
- router: `/usr/lib/ssh-configurator/resources/app/renderer/src/router/index.js`
- главное меню: `/usr/lib/ssh-configurator/resources/app/renderer/src/components/TheMenu.vue`
- layout tabs: `views/*/Layout.vue`
- экраны: `views/**/*.vue`
- живые подтверждения: [safe-actions.md](safe-actions.md) и [console-evidence.md](console-evidence.md)

При расхождении между UI wiring и backend-спекой:

- сначала доверять `backend-commands.json` как контракту команд
- затем проверять, как именно команда проброшена из UI
- финально подтверждать всё runtime-evidence через console log

## Главное меню

### Для `Runtime-VM` и `Runtime-server`

- `Системные настройки` -> `/system-settings/datetime`
- `Сетевые настройки` -> `/network-settings/settings`
- `Управление ВК` -> `/manage/services`
- `Ключи доступа` -> `/keys`
- `Диагностика` -> `/diagnostics`
- `Мониторинг` -> `/monitor`

### Для `Virt-Server`

- `Системные команды` -> `/system-settings/datetime`
- `Сетевые команды` -> `/network-settings/settings`
- `Управление снэпшотами` -> `/snapshots`
- `Резервное копирование` -> `/vmbackup`
- `Управление ВМ` -> `/manage/vm/management`
- `Ключи доступа` -> `/keys`
- `Диагностика` -> `/diagnostics`
- `Мониторинг` -> `/monitor`

## Вкладки По Разделам

### `/system-settings/*`

- `Дата и время`
- `Изоляция ядер`
- `NTP сервер`
- `Системные команды`

### `/network-settings/*`

- `Сетевые настройки`
- `Файлы`

### `/manage/*`

- `Управление службами`
- `Резервное копирование`
- `Обновление`

### `/manage/vm/*`

- `Управление ВМ`
- `Параметры описания ВМ`
- `Список всех XML`
- `Список всех образов`
- `Сгруппированные файлы`
- `PCI Devices`

## Матрица Команд

Формат риска:

- `safe-read`: чтение, список, проверка, безопасно для повседневного исследования
- `mutating`: меняет состояние, но не удаляет объект целиком
- `destructive`: удаление, выключение, сброс, восстановление, необратимые или потенциально опасные операции

### `/system-settings/datetime`

- Действие: `Запросить` рядом с полями даты и времени
  - Команда: `date_time`
  - Аргументы: нет
  - Риск: `safe-read`
  - Подтверждение: да, время читается с хоста
- Действие: `Установить` рядом с полями даты и времени
  - Команда: `set_date_time`
  - Аргументы: `["YYYY-MM-DD HH:MM:SS"]`
  - Риск: `mutating`
- Действие: `Запросить` рядом с полем часового пояса
  - Команда: `timezone`
  - Аргументы: нет
  - Риск: `safe-read`
  - Подтверждение: да, возвращает `Europe/Moscow`
- Действие: `Установить` рядом с полем часового пояса
  - Команда: `set_timezone`
  - Аргументы: `["<timezone>"]`
  - Риск: `mutating`

### `/system-settings/kernel-isolation`

- Действие: `Запросить`
  - Команда: `get_cpu_qty`
  - Аргументы: нет
  - Риск: `safe-read`
  - Подтверждение: да, вернул `Logical CPUs: 2`, `Physical cores: 2`
- Действие: `Обновить загрузчик хоста RT`
  - Команда: `update_grub_rt_host_cmdline`
  - Аргументы: `["<firstCore>", "<lastCore>"]`
  - Риск: `mutating`
  - Комментарий: затрагивает загрузочную конфигурацию RT-host

### `/system-settings/ntp-server`

- Действие: `Установить`
  - Команда: `change_ntp_server`
  - Аргументы: `["<ipv4>"]`
  - Риск: `mutating`

### `/system-settings/system-commands`

- Действие: `Перезагрузить хост`
  - Команда: `reboot_host`
  - Аргументы: нет
  - Риск: `destructive`
- Действие: `Выключить хост`
  - Команда: `shutdown_host`
  - Аргументы: нет
  - Риск: `destructive`
- Действие: `Установить` для поля `Переименовать хост`
  - Команда: `change_and_apply_hostname`
  - Аргументы: `["<hostName>"]`
  - Риск: `mutating`
- Действие: `Запросить` для поля `Тип хоста`
  - Команда: `check_host_type`
  - Аргументы: нет
  - Риск: `safe-read`
  - Подтверждение: да, возвращает `Runtime-VM`
- Действие: `Первичная инициализация ВМ`
  - Условие: только при `hostType === 'Virt-Server'`
  - Команда: `configure_hugepages`
  - Аргументы: `["<gigabytes>"]`
  - Риск: `destructive`
  - Комментарий: в UI прямо помечено как необратимое действие

### `/network-settings/settings`

- Действие: icon `reload` в аккордеоне `Сетевые настройки`
  - Команда: `get_interface_details`
  - Аргументы: нет
  - Риск: `safe-read`
- Действие: icon `delete` в таблице интерфейсов
  - Команда: `delete_interface`
  - Аргументы: `["<interfaceName>"]`
  - Риск: `destructive`
- Действие: открытие селекта `Имя`
  - Команда: `list_interfaces`
  - Аргументы: нет
  - Риск: `safe-read`
  - Комментарий: используется для заполнения `interfaceOptions`
- Действие: `Изменить` при включённом DHCP
  - Команда: `configure_dhcp`
  - Аргументы: `["<interfaceName>"]`
  - Риск: `mutating`
- Действие: `Изменить` при статической конфигурации
  - Команда: `set_ip_static`
  - Аргументы: `["<interfaceName>", "<ip/cidr>", "<gateway>", "<dns>"]`
  - Риск: `mutating`
- Действие: открытие списка интерфейсов в `Создание Bond`
  - Команда: `list_interfaces`
  - Аргументы: нет
  - Риск: `safe-read`
- Действие: `Создать` в `Создание Bond`
  - Команда: `configure_bond`
  - Аргументы: `["<bondName>", "<iface1 iface2 ...>", "<ip/cidr>", "<mode>", "<gateway>", "<dns>"]`
  - Риск: `mutating`
- Действие: открытие списка портов в `Создание сетевого моста`
  - Условие: только при `hostType === 'Virt-Server'`
  - Команда: `list_interfaces`
  - Аргументы: нет
  - Риск: `safe-read`
- Действие: `Создать` в `Создание сетевого моста`
  - Условие: только при `hostType === 'Virt-Server'`
  - Команда: `configure_bridge`
  - Аргументы: `["<bridgeName>", "<port>", "<ip/cidr>", "<gateway>", "<dns>"]`
  - Риск: `mutating`
- Действие: `Применить cетевые настройки`
  - Команда: `apply_network_settings`
  - Аргументы: нет
  - Риск: `destructive`
- Действие: `Восстановить настройки по умолчанию`
  - Команда: `reset_network_settings`
  - Аргументы: нет
  - Риск: `destructive`
  - Комментарий: UI предупреждает, что настройки будут сброшены до DHCP

### `/network-settings/files`

- Действие: icon `reload`
  - Команда: `list_files_by_directory`
  - Аргументы: `["network"]`
  - Риск: `safe-read`
  - Подтверждение: экран открывается, строки на текущем хосте не появились
- Действие: `Переименовать`
  - Команда: `rename_file`
  - Аргументы: `["<source>", "<target>"]`
  - Риск: `mutating`
- Действие: icon `delete`
  - Команда: `delete_file`
  - Аргументы: `["<source>"]`
  - Риск: `destructive`

### `/manage/services`

- Действие: `Запуск VCont без службы`
  - Команда: `start_once`
  - Аргументы: `["vcontd"]`
  - Риск: `mutating`
- Действие: `Остановить VCont`
  - Команда: `kill_service`
  - Аргументы: `["vcontd"]`
  - Риск: `destructive`
- Действие: `Создать`
  - Команда: `create_service`
  - Аргументы: `["<selectedServiceName>"]`
  - Риск: `mutating`
- Действие: `Запустить`
  - Команда: `start_service`
  - Аргументы: `["<selectedServiceName>"]`
  - Риск: `mutating`
- Действие: `Остановить`
  - Команда: `stop_service`
  - Аргументы: `["<selectedServiceName>"]`
  - Риск: `mutating`
- Действие: `Перезапустить`
  - Команда: `restart_service`
  - Аргументы: `["<selectedServiceName>"]`
  - Риск: `mutating`
- Доступные service rows в UI:
  - `vcontd`
  - `opcuad`
  - `vcont-monitor`

### `/manage/backups`

- Действие: `Обновить Vcont`
  - Команда: `update_firmware`
  - Аргументы: `["<directory>", "<username>", "<ip>"]`
  - Риск: `mutating`
- Действие: `Создать копию Vcont`
  - Команда: `make_runtime_backup`
  - Аргументы: `["<username>", "<ip>", "<directory>"]`
  - Риск: `mutating`
- Действие: `Восстановить Vcont`
  - Команда: `restore_runtime_backup`
  - Аргументы: `["<directory>", "<username>", "<ip>"]`
  - Риск: `destructive`

### `/manage/updates`

- Действие: `Обновить`
  - Команда: `update_configurator`
  - Аргументы: `["<directory>", "<username>", "<ip>"]`
  - Риск: `mutating`

### `/keys`

- Действие: `Сгенерировать ключ`
  - Команда: `generate_key`
  - Аргументы: нет
  - Риск: `mutating`
- Действие: `Удалить ключи в known_hosts`
  - Команда: `refresh_known_hosts`
  - Аргументы: `["<ip>"]`
  - Риск: `mutating`
- Действие: `Вывести список ключей`
  - Команда: `list_user_keys`
  - Аргументы: нет
  - Риск: `safe-read`
  - Подтверждение: да, в консоли вернулся ключ `vcont_initial`
- Действие: `Удалить ключ`
  - Команда: `delete_user_key`
  - Аргументы: `["<selectedKeyName>"]`
  - Риск: `destructive`
- Действие: `Добавить`
  - Команда: `add_user_key`
  - Аргументы: `["<newUserKey>"]`
  - Риск: `mutating`

### `/diagnostics`

- Действие: `Выполнить`
  - Команда: `check_status`
  - Аргументы: `["<serviceName>"]`
  - Риск: `safe-read`
  - Подтверждение: да, для `systemd-journald` пришёл журнал
- Значения `serviceOptions` в коде:
  - `systemd-networkd`
  - `systemd-timesyncd`
  - `systemd-journald`
  - `rsyslog`
  - `vcontd`
  - `avahi-daemon`
  - `vcont-monitor`
  - `ssh`

### `/monitor`

- Действие: `Выполнить` в блоке `Обновить сертификаты`
  - Команда: `update_certs`
  - Аргументы: `["<directory>", "<user>", "<ip>"]`
  - Риск: `mutating`
- Действие: `Выполнить` в блоке `Установить агент мониторинга`
  - Команда: `setup_monitoring_agent`
  - Аргументы: `["<directory>", "<user>", "<ip>"]`
  - Риск: `mutating`

### `/snapshots`

- Действие: title `Вывести список`
  - Команда: `list_vms`
  - Аргументы: нет
  - Риск: `safe-read`
  - Подтверждение: на текущем `Runtime-VM` команда отсутствует
- Действие: title `Обновить`
  - Команда: `update_snap_list`
  - Аргументы: `["<selectedVmName>"]`
  - Риск: `safe-read`
- Действие: title `Создать`
  - Команда: `make_vm_snapshot`
  - Аргументы: `["<selectedVmName>"]`
  - Риск: `mutating`
- Действие: title `Объединить все снэпшоты`
  - Команда: `merge_all_snapshots`
  - Аргументы: `["<selectedVmName>"]`
  - Риск: `destructive`
- Действие: title `Удалить все снэпшоты`
  - Команда: `delete_all_snapshots`
  - Аргументы: `["<selectedVmName>"]`
  - Риск: `destructive`
- Действие: title `Восстановить`
  - Команда: `restore_snapshot`
  - Аргументы: `["<selectedVmName>", "<selectedSnapshotName>"]`
  - Риск: `destructive`
- Действие: title `Удалить`
  - Команда: `delete_snapshot`
  - Аргументы: `["<selectedVmName>", "<selectedSnapshotName>"]`
  - Риск: `destructive`

### `/vmbackup`

- Действие: `Создать копию VM`
  - Команда: `make_vm_backup`
  - Аргументы: `["<vmName>", "<directory>", "<user>", "<ip>"]`
  - Риск: `mutating`
- Действие: `Восстановить VM`
  - Команда: `restore_vm_backup`
  - Аргументы: `["<vmName>", "<directory>", "<user>", "<ip>"]`
  - Риск: `destructive`

### `/manage/vm/management`

- Действие: title `Вывести список`
  - Команда: `list_vms`
  - Аргументы: нет
  - Риск: `safe-read`
  - Подтверждение: на текущем `Runtime-VM` команда отсутствует
- Действие: title `Запуск ВМ`
  - Команда: `start_vm`
  - Аргументы: `["<selectedVmName>"]`
  - Риск: `mutating`
- Действие: title `На паузу`
  - Команда: `pause_vm`
  - Аргументы: `["<selectedVmName>"]`
  - Риск: `mutating`
- Действие: title `Возобновить`
  - Команда: `resume_vm`
  - Аргументы: `["<selectedVmName>"]`
  - Риск: `mutating`
- Действие: title `Перезагрузить`
  - Команда: `reboot_vm_virsh`
  - Аргументы: `["<selectedVmName>"]`
  - Риск: `destructive`
- Действие: title `Выключить`
  - Команда: `shutdown_vm_virsh`
  - Аргументы: `["<selectedVmName>"]`
  - Риск: `destructive`
- Действие: title `Удалить из списка`
  - Команда: `undefine_vm`
  - Аргументы: `["<selectedVmName>"]`
  - Риск: `destructive`
- Действие: title `Удалить ВМ, дисковые образы, снашоты и конфигурационные файлы`
  - Команда: `delete_vm_full`
  - Аргументы: `["<selectedVmName>"]`
  - Риск: `destructive`
- Действие: title `Консольный доступ к ВМ`
  - Команда: `openTerminalSession('console', ["<selectedVmName>"])`
  - Риск: `mutating`
  - Комментарий: идёт не через `runSSHCommand`, а через terminal dialog
- Действие: title `Редактировать XML конфигурацию ВМ`
  - Команда: `openTerminalSession('edit_xml_online', ["<selectedVmName>"])`
  - Риск: `destructive`
  - Комментарий: интерактивная терминальная сессия

### `/manage/vm/description`

- Действие: открыть селект `XML файл`
  - Команда: `list_vms_schemas`
  - Аргументы: нет
  - Риск: `safe-read`
- Действие: открыть селект `Network value`
  - Команда: `list_interfaces`
  - Аргументы: нет
  - Риск: `safe-read`
- Действие: открыть селект `PCI`
  - Команда: `list_ethernet_pci_to_interface_mapping`
  - Аргументы: нет
  - Риск: `safe-read`
- Действие: `Изменить` для `RAM`
  - Команда: `run_vm_config`
  - Аргументы: `["ram", "<xmlFile>", "<ramValue>"]`
  - Риск: `mutating`
- Действие: `Изменить` для `CPU`
  - Команда: `run_vm_config`
  - Аргументы: `["cpu", "<xmlFile>", "<cpuValue>"]`
  - Риск: `mutating`
- Действие: `Изменить` для `Network`
  - Команда: `run_vm_config`
  - Аргументы: `["network", "<xmlFile>", "<networkType>", "<networkValue>"]`
  - Риск: `mutating`
- Действие: `Изменить` для `PCI`
  - Команда: `run_vm_config`
  - Аргументы: `["pci", "<pciId>"]`
  - Риск: `mutating`
  - Комментарий: здесь аргументы отличаются от остальных путей, `xmlFile` не передаётся
- Действие: `Изменить` для `Source`
  - Команда: `run_vm_config`
  - Аргументы: `["source", "<xmlFile>", "<sourceValue>"]`
  - Риск: `mutating`
- Действие: `Изменить` для `Rename`
  - Команда: `run_vm_config`
  - Аргументы: `["rename", "<xmlFile>", "<renameValue>"]`
  - Риск: `mutating`
- Действие: `Зарегистрировать ВМ`
  - Команда: `define_vm`
  - Аргументы: `["<xmlFile>"]`
  - Риск: `mutating`

### `/manage/vm/xmls`

- Действие: `Вывести список`
  - Команда: `list_files_by_directory`
  - Аргументы: `["xml"]`
  - Риск: `safe-read`
  - Подтверждение: на текущем хосте директория отсутствует
- Действие: `Удалить`
  - Команда: `delete_file`
  - Аргументы: `["<selectedFileName>"]`
  - Риск: `destructive`
- Действие: `Переименовать`
  - Команда: `rename_file`
  - Аргументы: `["<selectedFileName>", "<renameTarget>"]`
  - Риск: `mutating`
- Действие: `Зарегистрировать ВМ`
  - Команда: `define_vm`
  - Аргументы: `["<selectedFileName>"]`
  - Риск: `mutating`

### `/manage/vm/images`

- Действие: `Вывести список`
  - Команда: `list_files_by_directory`
  - Аргументы: `["images"]`
  - Риск: `safe-read`
  - Подтверждение: на текущем хосте директория отсутствует
- Действие: `Удалить`
  - Команда: `delete_file`
  - Аргументы: `["<selectedFileName>"]`
  - Риск: `destructive`
- Действие: `Переименовать`
  - Команда: `rename_file`
  - Аргументы: `["<selectedFileName>", "<renameTarget>"]`
  - Риск: `mutating`

### `/manage/vm/grouped-files`

- Действие: `Вывести список`
  - Команда: `group_files_by_type_and_vm`
  - Аргументы: нет
  - Риск: `safe-read`
  - Подтверждение: на текущем `Runtime-VM` команда отсутствует

### `/manage/vm/pci-devices`

- Действие: `Вывести список`
  - Команда: `list_pci_devices_by_iommu_group`
  - Аргументы: нет
  - Риск: `safe-read`
  - Подтверждение: на текущем хосте не читаются IOMMU groups
- Действие: `Проверить`
  - Команда: `check_iommu_grouping`
  - Аргументы: `["<pciDevice>"]`
  - Риск: `safe-read`

## Что Уже Подтверждено На Текущем Хосте

- `connect` работает, host type определяется как `Runtime-VM`
- `date_time`, `timezone`, `get_cpu_qty`, `check_status`, `list_user_keys` отрабатывают успешно
- `list_vms`, `group_files_by_type_and_vm` на текущем хосте отсутствуют как backend-команды
- `list_files_by_directory xml|images` упирается в отсутствие libvirt-директорий
- `list_pci_devices_by_iommu_group` упирается в отсутствие доступных IOMMU groups

## Практическое Правило Для Автоматизации

- По умолчанию автоматизировать только `safe-read`
- `mutating` выполнять осознанно и, по возможности, на тестовом контуре
- `destructive` не запускать без отдельного явного разрешения пользователя
