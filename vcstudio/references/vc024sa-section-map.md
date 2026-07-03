# VC024SA.B Section Map

Use this map before opening `vc024sa-complete.md`. The complete reference is embedded in this skill, extracted from `/home/ant/Загрузки/Руководство_правки_июнь.pdf`, so the skill is self-contained and does not depend on the source PDF/DOCX.

Important caveat: the PDF table of contents still shows the older numbering for `6.7+` in places. The body text is the source of truth for this map: `6.7` is ST, `6.8` is VCont startup, `6.9` is offline operations, `6.10` is online resource operations, and `6.11` is monitoring.

## Top-Level Sections

- `1. История изменения документа` (`vc024sa-complete.md`, around `L0125`): revision A 20.10.2024 first revision; revision B 25.03.2025 new hierarchy description.
- `2. Введение` (`L0132`): VCSystem, VCont runtime, VCStudio, target audience and architecture concepts.
- `3. Инсталляция программы` (`L0165`): hardware/software requirements, distribution acquisition, Linux/Windows install paths.
- `4. Запуск программы VCStudio` (`L0242`): Linux `vcstudio`, Windows `vcstudio.exe`.
- `5. Проект в VCStudio` (`L0266`): project/workspace, authorization, create/open project, archives, UI areas, toolbar, navigation objects, settings.
- `6. Разработка проекта` (`L0719`): devices, resources, applications, control loops, tasks, FBs, connections, order, event loops, search, ST, VCont launch, load/online operations, monitoring.
- `7. Обслуживание` (`L2901`): project restore from backup/history.
- `8. Коммуникационные возможности` (`L2976`): Modbus RTU/TCP, Modbus TCP Server memory map, publication into Runtime memory, MODBUS FBs, OPC UA blocks, protocol support list.

## Detailed Body Navigation

Search `vc024sa-complete.md` by these exact body headings or line labels when a question needs full detail:

- `L0166` `3.1. Требования к программному и аппаратному обеспечению для VCStudio`
- `L0180` `3.2. Требования к программному и аппаратному обеспечению для VCont в режиме эмулятора`
- `L0192` `3.3. Требования к программному и аппаратному обеспечению для VCont в операционном режиме`
- `L0210` `3.4. Способы получения дистрибутивов программ`
- `L0214` `3.5. Инсталляция программ на ОС Linux`
- `L0222` `3.6. Инсталляция программ на ОС Windows`
- `L0278` `5.2. Авторизация`
- `L0344` `5.5. Архивные файлы проекта`
- `L0349` `5.5.1. Системные сообщения о работе VCStudio`
- `L0353` `5.5.2. Резервные копии проекта`
- `L0359` `5.6. Области интерфейса программы VCStudio`
- `L0416` `5.6.2. Панель инструментов`
- `L0504` `5.6.3. Объекты в окне навигации`
- `L0541` `5.7. Настройка интерфейса VCStudio`
- `L0720` `6.1. Создание Устройства`
- `L0761` `6.2. Создание Ресурса`
- `L0799` `6.3. Создание Приложения`
- `L0831` `6.4. Создание Контура управления`
- `L0869` `6.5. Создание Задач`
- `L0917` `6.6. Создание алгоритмов в контуре управления`
- `L0919` `6.6.1. Назначение периодической или событийной задачи`
- `L0945` `6.6.2. Добавление функциональных блоков`
- `L0988` `6.6.3. Внешний вид функционального блока`
- `L1003` `6.6.4. Свойства портов ввода/вывода функционального блока`
- `L1036` `6.6.5. Задание начальных значений параметров портов функциональных блоков`
- `L1095` `6.6.6. Изменение типа данных ANY портов функциональных блоков`
- `L1155` `6.6.7. Изменение количества входов/выходов ФБ`
- `L1241` `6.6.8. Замена типа блока на другой в существующем контуре`
- `L1255` `6.6.9. Команда «Обновить тип блока»`
- `L1276` `6.6.10. Создание соединений`
- `L1473` `6.6.11. Порядок выполнения функциональных блоков`
- `L1502` `6.6.12. Контур управления событийной задачи. Особенности создания алгоритмов`
- `L1575` `6.6.13. Поиск функциональных блоков`
- `L1613` `6.7. Создание алгоритмов с помощью языка ST`
- `L1628` `6.7.1. Общие сведения о языке ST`
- `L1723` `6.7.2. Создание функционального блока на языке ST`
- `L1789` `6.7.3. Управляющие операторы`
- `L1807` `6.7.3.1. CASE`
- `L1846` `6.7.3.2. IF IFLSE` (typo preserved from document)
- `L1893` `6.7.3.3. FOR`
- `L1939` `6.7.3.4. WHILE`
- `L1998` `6.7.3.5. REPEAT`
- `L2046` `6.7.4. Массивы`
- `L2126` `6.7.5. Пользовательские типы данных`
- `L2129` `6.7.5.1. Перечисление ENUM`
- `L2199` `6.7.5.2. Структура STRUCT`
- `L2201` `6.8. Запуск среды исполнения (vcont)`
- `L2217` `6.9. Офлайн операции (без подключения к ресурсу)`
- `L2237` `6.9.1. Загрузка алгоритмов проекта в контроллер`
- `L2293` `6.9.5. Онлайн загрузить КУ`
- `L2350` `6.9.6. Онлайн удалить КУ`
- `L2381` `6.10. Онлайн операции`
- `L2394` `6.10.1. Инициализация переменных`
- `L2430` `6.10.2. Сохранение переменных`
- `L2461` `6.10.3. Создание файла загрузки`
- `L2515` `6.10.4. Перезагрузка ресурса`
- `L2552` `6.10.5. Сброс ресурса`
- `L2588` `6.10.6. Создание и загрузка файла загрузки`
- `L2631` `6.11. Режим мониторинга`
- `L2633` `6.11.1. Включение мониторинга`
- `L2657` `6.11.2. Добавление параметров в мониторинг`
- `L2700` `6.11.3. Изменение входных параметров в он-лайн режиме`
- `L2722` `6.11.4. Форсирование переменных`
- `L2763` `6.11.5. Принудительная генерация событий`
- `L2903` `7.1. Восстановление проекта из резервной копии`
- `L2987` `8.1. Modbus`
- `L3010` `8.1.1. Modbus Serial`
- `L3082` `8.1.2.1. Modbus TCP Client`
- `L3154` `8.1.2.2. Modbus TCP Server`
- `L3221` `8.1.2.3. Modbus TCP Server. Публикация значений ФБ во внутреннюю память Runtime`
- `L3286` `8.1.3. Функциональные блоки MODBUS`
- `L3300` `8.1.3.1. MBWRITE_PACK`
- `L3400` `8.1.3.2. MBREAD_PACK`
- `L3499` `8.1.3.3. MBSERIALDIAG`
- `L3578` `8.1.3.4. MBDEVICERTU`
- `L3646` `8.1.3.5. MBDEVICETCP`
- `L3706` `8.1.4. Настройка количества портов входов/выходов для MBREAD_PACK и MBWRITE_PACK`
- `L3721` `8.1 OPC UA` (numbering conflict preserved from document)
- `L3799` `8.1.1 Блок CLIENT`
- `L3864` `8.1.2 Блок SUBSCRIBE`
- `L3913` `8.1.3 Блок PUBLISH`

## Answering Rule

For high-confidence answers, first use the thematic reference. For rare UI labels, exact table rows, figure captions, typo-sensitive text, or anything the thematic reference does not cover, open `vc024sa-complete.md` and quote/summarize from the embedded extracted text. Do not require the external PDF/DOCX to answer.
