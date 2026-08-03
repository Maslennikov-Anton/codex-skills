# Тест-кейсы VCont

## Docker Compose и профилированные VCont-сервисы

Актуальная Docker-среда VCont - Ubuntu 24.04. Это общее правило для smoke, HSB, trial/licensed и других runtime-проверок. Образы на Ubuntu 22.04 не являются рабочим baseline: актуальные VCont-бинарники могут требовать `GLIBC_2.38`, `GLIBC_2.36` и `GLIBCXX_3.4.32`. Используй 22.04 только если задача явно проверяет совместимость со старой ОС.

Если `docker-compose.yml` использует YAML anchor для `vcont1` и профилированные сервисы `vcont3`/`vcont4`, не полагайся на автоматически сгенерированные image names вида `project-service`. Профилированный сервис может остаться на старом локальном image, если раньше он был собран другим Dockerfile/entrypoint и текущий прогон не пересобрал именно этот service image.

Практическое правило для тестовой инфры HSB: задавай общий `image` для всех VCont-сервисов и поднимай стенд через `docker compose up -d --build`. Иначе возможен симптом, при котором `vcont1`/`vcont2` запускаются нормально, а `vcont3` или `vcont4` рестартится со старым entrypoint, например с запуском `./vcont -c ...` и без актуального `LD_LIBRARY_PATH=/opt/vcont:/opt/vcont/lib`.

## HSB failover с IDE-мониторингом пользовательской программы

Назначение: часто повторяемый ручной/скриптовый тест для двух VCont в HSB. Цель - проверить не только запуск контейнеров и смену ролей, а то, что пользовательская программа продолжает выполняться на активном узле после failover без потери runtime-состояния.

### Контекст проекта

Базовая рабочая директория:

```text
/home/ant/IdeaProjects/vcont-hsb
```

Ожидаемая пара сервисов Docker Compose:

```text
vcont1 -> IDE port 61499
vcont2 -> IDE port 61500
```

Bootfile для проверки комплексной программы параллельных счетчиков (текущий период таска в файле — 50 мс):

```text
/home/ant/IdeaProjects/vcont-hsb/tests/resources/fboot/complex_counters.vcont.fboot
```

Он должен быть положен как `vcont.fboot` рядом с бинарником каждого VCont:

```text
.work/vcont-runtime/vcont1/vcont-lin.x86_64-arch/vcont.fboot
.work/vcont-runtime/vcont2/vcont-lin.x86_64-arch/vcont.fboot
```

В актуальной локальной инфре исходная поставка VCont хранится как Debian-пакет:

```text
vcont1/vcont.lin.x86_64.deb
```

Runtime-директории под каждый узел готовятся из этого `.deb` перед запуском тестов. Не используй старые `.tgz`/`.tar.gz` архивы или распакованные копии в `vcont1/` как baseline, если они вдруг остались локально.

Контрольные пины программы:

```text
APP001.LOOP010.CNT_A.OUT
APP001.LOOP010.CNT_B.OUT
APP001.LOOP010.CNT_C.OUT
APP001.LOOP010.LAST_A.OUT
APP001.LOOP010.LAST_B.OUT
APP001.LOOP010.LAST_C.OUT
```

### Что считать oracle

Для определения текущей HSB-роли сначала используй IDE-команду `HSBSTATUS` на каждом VCont-инстансе. Логи нужны для истории смены ролей и диагностики HSB-синхронизации, но основным oracle пользовательской программы остаются значения пинов, прочитанные через IDE-команды `READ` с активного узла. Для текущего проекта/поставки `vcont-hsb` экспериментально включен `DataToLog: "serialize,deserialize"`; если строки `SERIALIZE/DESERIALIZE` есть в логе, обязательно прикладывай их к артефактам. В других проектах эта настройка может не работать, поэтому тестовая логика не должна считать отсутствие `SERIALIZE/DESERIALIZE` универсальной ошибкой VCont.

Предпочтительный запрос роли:

```xml
<Request ID="1" Action="HSBSTATUS"></Request>
<Response ID="1"><STATUS="MAIN|RESERVE|STANDALONE|NONE"/></Response>
```

Если прямой запрос недоступен, роль можно восстановить по текущим строкам в `vcont.log`:

```text
Global mode changed to MAIN
Global mode changed to RESERVE
Global mode changed to STANDALONE
The mode has been changed to: MAIN|RESERVE|STANDALONE
The current copy becomes MAIN.
The current copy becomes RESERVE.
```

Если один контейнер остановлен, второй работающий узел считается активным. Если оба работают, активным считать `MAIN`; `STANDALONE` считать активным только если нет единственного `MAIN`. `RESERVE` нельзя читать как активный поток расчета.

### Корректная IDE-команда `READ`

Для VCont `1.1.0.21308` порядок атрибутов важен: `ID` должен идти перед `Action`.

```xml
<Request ID="101" Action="READ"><Connection Source="APP001.LOOP010.CNT_A.OUT" Destination="*"/></Request>
```

Практический TCP framing, совместимый с `vcont-common-tools.common.tools.to_message`:

```python
payload = xml.encode("utf-8")
message = bytes([80, 0, 0]) + bytes([80, 0, len(payload)]) + payload
```

Для этого сценария читай каждый пин отдельной короткой командой. Не объединяй все пины в один длинный XML, если длина может выйти за однобайтовый `len(payload)`.

Ответ `READ` возвращает значение в атрибуте `Destination`, а не в `Value`:

```xml
<Response ID="101">
  <Connection Source="APP001.LOOP010.CNT_A.OUT" Destination="16" />
</Response>
```

Парсер ответа должен сначала извлекать полный `<Response>...</Response>`, а уже потом парсить XML. Нельзя останавливать regex на первом `/>`, потому что внутри полного ответа самозакрывающийся `<Connection ... />`.

### Процедура 3-минутного прогона

1. Убедиться, что оба runtime используют один и тот же `complex_counters.vcont.fboot`.
2. Перезапустить оба сервиса:

```bash
docker compose restart vcont1 vcont2
```

3. Дождаться, пока активный узел отвечает на IDE `READ` хотя бы по `CNT_A.OUT`, `CNT_B.OUT`, `CNT_C.OUT`.
4. Запустить мониторинг на 180 секунд.
5. Каждые 0.5-1 секунду читать с активного узла контрольные пины через IDE `READ`.
6. Каждые 15 секунд выполнять переключение:
   - если оба контейнера работают, остановить текущий активный (`MAIN` или единственный активный `STANDALONE`);
   - если один контейнер остановлен, вернуть остановленный через `docker compose start <service>`;
   - сразу после операции заново определить активный узел через `HSBSTATUS` на каждом доступном VCont-инстансе; состояние контейнеров и роли в логах использовать только как fallback/diagnostics.
7. Сохранять JSON-артефакт в `/tmp`, включая:
   - timestamp/relative time;
   - docker state каждого узла;
   - распознанную HSB-роль каждого узла;
   - выбранный активный узел и причину выбора;
   - значения `CNT_A/CNT_B/CNT_C/LAST_A/LAST_B/LAST_C`;
   - события `stop-active` и `start-stopped` с последними значениями перед переключением.
8. После теста поднять оба сервиса:

```bash
docker compose start vcont1 vcont2
```

### Критерии результата

Позитивные признаки:

- после остановки активного узла второй узел становится `STANDALONE` и отвечает на IDE `READ`;
- после возврата пары режимы стабилизируются как `MAIN/RESERVE`;
- нет пропусков чтения активного потока по `CNT_A.OUT`, `CNT_B.OUT`, `CNT_C.OUT`;
- счетчики на новом активном узле продолжают ожидаемую последовательность без отката/сброса относительно последнего состояния прежнего MAIN.

Негативные признаки:

- новый активный узел возвращает нули или состояние, явно не близкое к последнему состоянию прежнего MAIN;
- `CNT_C` или старшие счетчики откатываются при failover;
- тестовый клиент случайно читает `RESERVE` как активный узел;
- IDE-клиент получает пустые ответы из-за неверного framing, слишком длинного XML или неправильного парсинга `Response`.

### Исторический прогон старого 5-минутного варианта 2026-04-30

Этот прогон оставлен только как исторический диагностический baseline сценария с `complex_counters.vcont.fboot` и длительностью 300 секунд. Для текущей проверки используй актуальный файл из репозитория и действующие pytest-сценарии; не переноси результат старого артефакта на текущую сборку.

Артефакт:

```text
/tmp/vcont_hsb_failover_monitor_final_20260430_152519.json
```

Параметры:

```text
duration=300s
sample=0.5s
switch=15s
events=19
stop-active=10
start-stopped=9
active samples=531
missing active counter reads=0
```

Результат этого прогона: смена HSB-ролей работала, активный узел после остановки MAIN продолжал выполнять программу и отвечать на IDE `READ`, но состояние счетчиков между MAIN и RESERVE расходилось. Поэтому требование "без потерь на резервном" не было подтверждено.

Примеры расхождения, формат `CNT_A/CNT_B/CNT_C`:

```text
45.4s:  stop vcont1, before 15/5/2 -> vcont2 after 16/1/0
76.0s:  stop vcont2, before 13/7/2 -> vcont1 after 16/3/0
168.0s: stop vcont1, before 11/5/0 -> vcont2 after 13/1/2
290.4s: stop vcont1, before 3/5/2  -> vcont2 after 6/1/0
```

Вывод: для будущих прогонов сначала проверяй корректность IDE-клиента и выбора активного узла, затем оценивай именно непрерывность пользовательских счетчиков на failover. Если после failover значения расходятся похожим образом, это evidence рассинхронизации runtime-данных ФБ, а не проблема запуска контейнеров.

## HSB failover с Modbus RTU-over-TCP

RTU без serial-device можно проверять как RTU-over-TCP: TCP-соединение несет raw Modbus RTU ADU с CRC16, без MBAP. Для HSB нужны два разных сценария, потому что они покрывают разные роли VCont.

### Вариант 1: VCont как RTU client

Назначение: прямой аналог теста с `MBCLIENTTCP`.

Схема:

```text
VCont active:
  CTU_A/B/C.CV -> MBWRITE_PACK_1.WD01
  MBWRITE_PACK_1 -> MBCLIENTRTUOVERTCP
  MBCLIENTRTUOVERTCP -> external RTU-over-TCP server registers 2048..2050

pytest:
  external checker reads external RTU server registers 2048..2050
```

Failover oracle:

1. дождаться, что внешний server получил ненулевые одинаковые значения;
2. дождаться следующего шага счетчика до остановки MAIN;
3. остановить MAIN;
4. дождаться нового active;
5. проверить, что значения во внешнем server продолжаются, а не сбрасываются: `after_stop > during_stop` по каждому регистру;
6. для счетчиков с периодом 1000 мс можно дополнительно проверять ожидаемый шаг `+1`, если чтение сделано на контролируемой границе.

### Вариант 2: VCont как RTU server

Назначение: проверить встроенный `MBSERVER Mode=rtu`, который читает внешний RTU-клиент.

Схема:

```text
VCont active:
  CTU_A/B/C.CV -> CNT_A/B/C.IN
  CNT_A/B/C.OUT -> Alias -> MBSRV1.MW2048..2050
  MBSRV1 = MBSERVER Mode=rtu

pytest:
  external RTU client reads active VCont MBSERVER registers 2048..2050
```

Failover oracle:

1. читать текущий `MAIN` как RTU server через host-порт его `1502`;
2. дождаться `before_stop` - ненулевых одинаковых значений;
3. остановить MAIN;
4. дождаться, что бывший `RESERVE` стал active;
5. переключить внешний RTU-клиент на порт нового active;
6. проверить, что `after_stop > before_stop` по каждому регистру. Проверка только "не ноль" или "все регистры равны" недостаточна, потому что пропустит reset/откат.

Практическая ловушка: для публикации счетчика во встроенный `MBSERVER` не делай alias напрямую с `CTU.CV`. На локальном стенде счетчики росли, но регистры оставались нулевыми. Рабочий паттерн: `CTU.CV -> INT.IN`, затем `INT.OUT -> MBSRV1.MW...`.
