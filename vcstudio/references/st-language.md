# Structured Text In VCStudio

## Навигация

- Создание Studio-compatible ST: `Editor Grammar Vs Translator Grammar`, `Studio ST Paths`, `Interface Extraction`.
- Проверка возможности языка: `Known ST->Lua Translator Limitations`, затем `Translator-Supported Syntax For Candidate Tests`.
- Диагностика deploy/codegen: `Translator Run Profile`, `Lua InterfaceSpec`, `Source-Observed Codegen Rules`.
- Проектирование тестов: `Integration-Test Guardrails`; результат считается поддержанным только после editor/wrapper/translation/load/runtime проверки применимых слоёв.

## Source Baseline

Source-derived facts here come from local `/home/ant/IdeaProjects/vcstudio` branch `VCONT-2056`:

- Studio ST editor grammar: `plugins/org.eclipse.fordiac.ide.model.structuredtext/.../StructuredText.xtext`;
- ST loop synchronization: `TextLoopEditor.java`, `StFBSynchronizer.java`, `StVariableParser.java`;
- deploy wrapper and translator invocation: `StDeployHelper.java`;
- bundled translator: `data/st-lua/linux.dist/src`.

For integration tests, emulate the Studio path, not just the bundled translator. The relevant intersection is:

1. what the Studio editor can parse/save;
2. what `StVariableParser` extracts into the Studio interface;
3. what `StDeployHelper` wraps and sends;
4. what the bundled translator compiles to Lua;
5. what VCont accepts and exposes through Watch/READ.

## Editor Grammar Vs Translator Grammar

The Studio editor grammar is narrower than the bundled `st-lua` translator grammar.

Studio editor grammar accepts an algorithm shaped as:

```iecst
FUNCTION_BLOCK optional_name
VAR | VAR_INPUT | VAR_OUTPUT
    name : type := optional_initial;
END_VAR
statements
END_FUNCTION_BLOCK
```

The outer `FUNCTION_BLOCK ... END_FUNCTION_BLOCK` is optional in the editor grammar, but the normal Studio authoring path stores the algorithm text from the UI and deploy code wraps it again as `FUNCTION_BLOCK ST ... END_FUNCTION_BLOCK`.

Important Studio-editor constraints:

- `TYPE ... END_TYPE`, `STRUCT`, `VAR_TEMP`, and `VAR_GLOBAL` are not in `StructuredText.xtext` top-level algorithm grammar; the bundled translator may compile them, but they are not safe Studio-editor constructs.
- `VAR_INPUT`, `VAR_OUTPUT`, and `VAR` are the Studio-safe sections for authoring.
- The editor grammar uses `END_VAR`; `VAR_END` is a documentation typo and is not source-supported.
- Statements are semicolon-separated by `Stmt_List`; use explicit semicolons in integration cases.
- `CASE` labels in editor grammar are constants or variables. Numeric ranges like `2..5` are supported by the bundled translator, but not by `StructuredText.xtext` `Case_Label`.

Translator-only constructs can still be useful for translator black-box tests, but mark them separately from Studio-integration cases.

## Studio ST Paths

| Path | Source path | Wrapper/input | Events in generated Lua interface | Runtime creation |
|---|---|---|---|---|
| ST loop text editor | `TextLoopEditor` saves `LoopLanguage.setST`, then `StFBSynchronizer.syncFromSt` | raw loop ST fragment, deployed through `createStRequest(taskHeader, stCode, "ST")` | deploy helper hardcodes `REQ` / `CNT` | one synthetic FB `APP.LOOP.ST` of type `ST`, Lua embedded in the `CREATE FB` request |
| ST loop model interface | `StFBSynchronizer.syncFbInterface` | same raw ST fragment parsed for visible ports | model FB interface uses `REQ` / `CNF` | this is model synchronization, not the final Lua `interfaceSpec` for ST loop deploy |
| UserLibrary/user ST FB | `SimpleFBType` with `STAlgorithm` inside an `FBNetworkElement` | `getStText` wraps algorithm text as `FUNCTION_BLOCK ST ... END_FUNCTION_BLOCK` | first actual event input/output from block interface; typical user ST FB is `REQ` / `CNF`; fallback is `NULL` | first `CREATE FBType Name="<type>" >...lua...</Request>`, then `CREATE FB Name="APP.LOOP.<name>" Type="<type>" ...` |
| Standalone translator/harness | caller-provided source | usually full `FUNCTION_BLOCK NAME ... END_FUNCTION_BLOCK` | no Studio Java `interfaceSpec` unless harness recreates it | not proof of Studio compatibility |

The most common emulation mistake is mixing ST loop `REQ`/`CNT` with user ST FB `REQ`/`CNF`.

## Interface Extraction

`StVariableParser` is a Java regex/line parser used by Studio wrapper code. It is not the Python translator parser.

Rules to emulate:

- only `VAR_INPUT` and `VAR_OUTPUT` become Studio data interface ports;
- local `VAR` stays internal translator state and appears in generated `internalVarsInformation`;
- declarations are read line by line between `VAR_INPUT|VAR_OUTPUT` and `END_VAR`;
- `//` comments are stripped; block comments are not part of this parser's stripping logic;
- a trailing semicolon is stripped;
- text after initializer marker `:=` is removed for interface type extraction;
- ` AT ` links are stripped from the declaration and preserved separately by the parser;
- `ARRAY[lower..upper] OF T` becomes one data port with element type `T` and size `max(0, upper - lower + 1)`;
- lower bound is not preserved in `DIDataTypeNames` / `DODataTypeNames`;
- multiline declarations are risky because the parser is line-based.

Interface indexes:

- data inputs start at `33554432` (`1 << 25`);
- data outputs start at `67108864` (`1 << 26`);
- internal persisted values start at `268435456` (`1 << 28`);
- declaration order defines offsets.

`StDeployHelper.inlinePortIndexes` replaces generated Lua tokens `DI_<name>` and `DO_<name>` with those numeric indexes before sending Lua to VCont.

## Translator Run Profile

Studio runs the bundled translator as an external binary:

- Linux path: `st-lua/linux.dist/main.bin`;
- Windows path expected by Java: `st-lua/windows.dist/main.exe`;
- working directory: a generated directory under `st-lua/compile` for preview/compile or `st-lua/deploy` for deploy;
- input file: `source_code.st`;
- output file: `script.lua`;
- the binary is launched without command-line arguments.

Studio treats translation as failed when:

- the translator binary path does not exist;
- the binary cannot be made executable;
- process exit code is nonzero;
- any translator log line contains `ERROR`;
- `script.lua` is missing, not a regular file, or empty;
- the final generated request is larger than the protocol frame limit.

Current translator limits are source-defined as 250 `VAR_INPUT`, 250 `VAR_OUTPUT`, 2000 internal `VAR`, and 200 total service variables.

## Known ST->Lua Translator Limitations

Этот раздел — compatibility contract для текущего пути `VCStudio -> ST editor/wrapper -> bundled ST->Lua -> VCont`.
Ограничения сгруппированы по слою возникновения. Валидность по IEC 61131-3, распознанный token, exit code `0` или
созданный Lua-файл сами по себе не доказывают end-to-end поддержку.

Различай три вида записей: **не поддержано** — конструкцию нельзя использовать; **частичная семантика** — допустим
только явно описанный subset; **смежная граница** — ST может быть корректен, но runtime protocol или typelibrary не
предоставляет ожидаемую возможность.

### Карта раздела

| Группа | Ограничения и важные границы |
|---|---|
| 1. Исходный текст | прагмы, non-ASCII identifiers, `_` в числовых литералах, Unicode в `STRING`/`WSTRING`/`WCHAR` |
| 2. Типы и выражения | `TIME_TO_DINT`, long time types, mixed numeric conversion, `CASE` |
| 3. Структура программы | SFC, `PROGRAM`, пользовательские `FUNCTION`, несколько top-level `FUNCTION_BLOCK` в одном input, `EXTENDS`, `CLASS`, `INTERFACE`/`IMPLEMENTS`, `ACTION`, `METHOD`, `PROPERTY`, `NAMESPACE`, `CONFIGURATION` |
| 4. Библиотека ФБ | отсутствующий vendor-FB `SEMA` |
| 5. Объявления и данные | общий `:=`, `VAR_IN_OUT`, references/pointers, `TYPE`/`STRUCT`/`UNION`, `RETAIN`/`PERSISTENT`, `CHAR`, `AT %...`, `VAR_GLOBAL`/`VAR_EXTERNAL`, массивы |
| 6. Runtime management | indexed `READ`/`WRITE` элементов массива |

### Общие правила для кода и тестов

1. Найди конструкцию в effective ST input и определи фактическую границу отказа: editor, wrapper/translation, VCont
   load/runtime или typelibrary.
2. Удали тест, если его единственная цель — известное неподдерживаемое поведение. В смешанном тесте убери только
   неподдерживаемую часть и сохрани самостоятельный oracle на оставшуюся цель.
3. Не заменяй expected value исходным/default value: неуспешный setup тогда даст ложноположительный результат.
4. После замены Studio/translator/runtime перепроверь минимальный repro по всем применимым слоям и только затем меняй
   этот contract.

### 1. Исходный текст и литералы

#### Прагмы `{...}`

- Не используй `{attribute ...}` и другие vendor pragmas в коде, передаваемом транслятору.
- Не трактуй текст в фигурных скобках как обычный комментарий: по ST это контейнер прагмы, а её семантика зависит от реализации.
- Удали pragma из effective translator input или перенеси metadata во внешний Studio/project configuration. Для обычных пояснений используй `(* ... *)` или `//`, проверяя их отдельно от pragma behavior.
- Не удаляй неизвестную или семантически значимую pragma молча: сначала выясни её назначение и воспроизведи эффект поддерживаемой конфигурацией либо останови перенос как behavior-changing.

#### UTF-8 / non-ASCII в идентификаторах

- Имена переменных, полей, типов и других ST symbols задавай только ASCII-идентификаторами: латинские буквы `A-Z`/`a-z`, цифры и `_`, например `counter` вместо `счётчик`.
- Кириллица и другие UTF-8/non-ASCII символы в идентификаторах не поддерживаются текущим translator path.
- Текущий lexer может выдать серию `Illegal character`, затем syntax/parse error без пригодного Lua artifact.
- При автоматическом переименовании сохраняй явную таблицу `original -> effective`, чтобы диагностика и связь с исходным проектом не потерялись.
- UTF-8 комментарии являются отдельной capability и проходят текущий translator path; это не доказывает поддержку non-ASCII в идентификаторах или текстовых типах.

#### Подчёркивания в числовых литералах

- Не используй `_` как разделитель групп цифр внутри числовых литералов: запись вида `1_000_000` не поддерживается текущим Studio-bundled ST->Lua path.
- Перед трансляцией удаляй только разделители внутри числа: `1_000_000` -> `1000000`. Это ограничение не относится к `_` в ASCII-идентификаторах, например `motor_speed`.
- Не сохраняй проверки числовых литералов с `_` как expected-positive `supported_runtime`: они закрепляют неподдерживаемый синтаксис как обязательную возможность продукта.

#### Кириллица в `STRING`, `WSTRING` и `WCHAR`

- Для текста на русском языке используй `WSTRING` и типизированные литералы вида `WSTRING#'Привет'`. Обычный `STRING` считай ASCII-only в продуктовом compatibility contract: кириллица в `STRING` не поддерживается, даже если её UTF-8 байты фактически проходят translation/load и узкий `FIND(...) > 0` возвращает `TRUE`.
- Не сохраняй тест с кириллицей в `STRING` как expected-positive `supported_runtime` и не меняй ожидаемую длину с `6` на `12`: это закрепило бы неподдерживаемое byte-oriented поведение как пользовательскую возможность.
- На проверенных артефактах кириллический `WSTRING` проходит оба VCont load path как входной, выходной и внутренний `VAR`: прямые `READ`/`WRITE`, equality и проверка наличия подстроки через `FIND(...) > 0` работают. Это подтверждает хранение и transport текста, но не Unicode-aware семантику строковых функций.
- Текущий codegen понижает операции над `STRING` и `WSTRING` к обычной Lua byte string. Для `WSTRING#'Привет'` подтверждено: `LEN(...) = 12`, `FIND(..., WSTRING#'вет') = 7`, `LEFT(..., 1) <> WSTRING#'П'`, а `LEFT(..., 2) = WSTRING#'П'`. Поэтому длины, позиции и границы `LEFT`/`RIGHT`/`MID` и смежных функций не трактуй как номера Unicode characters; не режь кириллицу ими без отдельного подтверждённого Unicode helper/normalization layer.
- Не обобщай поддержку `WSTRING` на `WCHAR`. Изолированный внутренний `WCHAR := "П"` переводится в Lua, но VCont отклоняет создание экземпляра с `UNSUPPORTED_TYPE` в Studio path и не создаёт экземпляр через fboot; `WCHAR` остается end-to-end unsupported.

### 2. Типы, выражения и операторы управления

#### Граница `TIME_TO_DINT`: ST и FBD

- Считай `TIME_TO_DINT(...)` поддерживаемой встроенной функцией ST, а не пользовательской функцией или обязательным FBD-блоком. Не удаляй ST regression case только потому, что в VCStudio typelibrary отсутствует `TIME_TO_DINT.fbt`.
- Используй наносекунды в oracle для текущего ST->Lua->VCont path: `TIME_TO_DINT(T#50ms) = 50_000_000`. Транслятор хранит `TIME` как nanosecond-like integer и применяет 32-bit signed conversion; отдельно проверяй переполнение `DINT` для длительных интервалов.
- Не трактуй runtime mode `studio` в ST integration matrix как FBD-проверку: это загрузка сгенерированного ST FB через Studio-like online command stream. Наличие функции в ST и наличие одноимённого `.fbt` в FBD-библиотеке являются разными capability.

#### Длинные типы времени `LTIME`, `LTOD` и `LDT`

- Типы `LTIME`, `LTOD` (`LTIME_OF_DAY`) и `LDT` (`LDATE_AND_TIME`) не поддерживаются текущим Studio-bundled ST->Lua->VCont path.
- Не используй их в interface/internal declarations, typed literals или встроенных преобразованиях и split-функциях, которым требуется один из этих типов на входе или выходе. Распознанный token, успешная standalone translation или нормализация имени типа в Studio wrapper не доказывают end-to-end поддержку.
- Для длительности используй `TIME`, для времени суток — `TOD`/`TIME_OF_DAY`, для даты и времени — `DT`/`DATE_AND_TIME`, только если их диапазона и точности достаточно для сценария. После замены отдельно проверь граничные значения и единицы runtime oracle.
- Не держи cases на `LTIME`, `LTOD`/`LTIME_OF_DAY` или `LDT`/`LDATE_AND_TIME` как expected-positive `supported_runtime`.

#### Неявное преобразование смешанных числовых типов

- Не рассчитывай на автоматическое повышение типа в арифметических выражениях: текущий валидатор ST-редактора VCStudio требует совместимых типов операндов. Например, `Numerator : INT; OUT : REAL; OUT := Numerator / 4.0;` не является допустимым REAL-делением и должно диагностироваться как `Operator type mismatch`.
- Тип переменной назначения не меняет тип уже вычисляемого выражения. Если требуется REAL-арифметика, явно преобразуй целочисленный операнд до операции, например `OUT := INT_TO_REAL(Numerator) / 4.0;`, и отдельно подтверди поддержку самой операции end-to-end.
- Не считай результат `2` доказательством округления `2.25`: при обходе editor-validation текущий транслятор определяет выражение по левому `INT`-операнду и может сгенерировать Lua floor division `//`, поэтому дробное значение вообще не вычисляется.
- Не держи implicit-promotion probes как expected-positive `supported_runtime`. Режим `studio` в integration harness проверяет Studio-like command load, но не запускает валидатор ST-редактора и сам по себе не доказывает editor acceptance.

#### Допустимый селектор `CASE`

- В Studio-authored коде используй для `CASE` встроенный целочисленный селектор и совместимые целочисленные метки. Числовые диапазоны относятся только к translator-only coverage: bundled translator их понимает, но текущая Studio editor grammar — нет. Не используй `BOOL`, `STRING` или `WSTRING`.
- Транслятор может синтаксически разобрать недопустимый селектор, но завершает codegen сообщением `Wrong CASE selector type: 'BOOL'` или `Wrong CASE selector type: 'STRING'` и не создаёт пригодный `script.lua`. Parse и exit code процесса `0` не доказывают поддержку.
- Булево ветвление выражай через `IF ... THEN ... ELSE`; строковое — через `IF` / `ELSIF` с явными сравнениями. Если нужен именно `CASE`, заранее отобрази варианты на целочисленные коды.
- IEC допускает перечислимую семантику в соответствующих профилях, но текущий Studio path не поддерживает пользовательский `TYPE`/`ENUM`; для совместимости также отображай enum-state на встроенный integer.
- Не держи `CASE` по `BOOL`, `STRING` или `WSTRING` как expected-positive `supported_runtime` и не классифицируй корректный отказ как дефект продукта.

### 3. Структура программы и модель исполнения

#### SFC-синтаксис в ST payload

- SFC — отдельный графический язык и модель исполнения. Текущий Studio ST path не поддерживает конструкции SFC (`INITIAL_STEP`, `STEP ... END_STEP`, `TRANSITION ... END_TRANSITION` и привязки действий с qualifiers `N` / `S` / `R` / `L`) внутри ST payload; добавление такой поддержки не планируется.
- IEC 61131-3 допускает использование элементов SFC в ST и ST-код в телах действий, но нормативная допустимость не означает поддержку этой формы редактором, Studio wrapper или bundled ST->Lua translator. Не встраивай SFC внутрь `FUNCTION_BLOCK ... END_FUNCTION_BLOCK`.
- Текущий translator process может завершиться с exit code `0`, но пишет `Syntax error ... unexpected '<step name>'` и `Parse error`, не создавая `script.lua`; считай это неуспешной трансляцией, а не VCont runtime defect.
- Не держи SFC surface cases как expected-positive `supported_runtime`, product gap или future coverage в ST->Lua suite: они неактуальны для текущего и планируемого Studio ST path. Если проекту нужен SFC, рассматривай его как отдельный графический authoring/deploy path с собственным Studio model oracle; это не доказывает поддержку SFC-синтаксиса внутри ST.

#### Классы `CLASS`

- Классы в текущей VCStudio не поддерживаются. Не используй объявления `CLASS ... END_CLASS`, экземпляры пользовательских классов и обращения к их полям или операциям в Studio-compatible ST.
- Класс объединяет состояние и операции в пользовательский тип, но распознавание отдельных tokens транслятором или создание Lua-файла не доказывает, что Studio умеет создать, сохранить, связать и загрузить такую модель.
- Для совместимого кода перенеси состояние и логику в один owning `FUNCTION_BLOCK` с явными `VAR_INPUT` / `VAR_OUTPUT` и внутренними `VAR`. Это ограничение не запрещает подтвержденные стандартные функциональные блоки и обращения к их интерфейсу.
- Не заменяй класс пользовательской `FUNCTION`, `INTERFACE`, `METHOD`, `PROPERTY`, `ACTION` или наследованием `EXTENDS`, поскольку эти конструкции также не поддерживаются текущим Studio path. Не держи `CLASS` cases как expected-positive `supported_runtime`.

#### Интерфейсы `INTERFACE` и `IMPLEMENTS`

- Интерфейсы в текущей VCStudio не поддерживаются. Не используй объявления `INTERFACE ... END_INTERFACE`, ключевое слово `IMPLEMENTS`, переменные интерфейсного типа и полиморфные вызовы через такой тип в Studio-compatible ST.
- По назначению интерфейс определяет набор методов без реализации и позволяет разным типам предоставить единый контракт. Например, управляющий код может одинаково запускать и останавливать асинхронный или синхронный двигатель, не зная особенностей их внутренней реализации.
- Для совместимого кода задай нормализованный контракт одного owning `FUNCTION_BLOCK`: общие команды и уставки передавай через `VAR_INPUT`, общие состояния и ошибки возвращай через `VAR_OUTPUT`, а тип реализации задавай целочисленным selector и явно выбирай ветвь через `IF` / `CASE`. Специфику каждого типа двигателя оставь внутри соответствующей ветви.
- Если реализации уже существуют как отдельно подтвержденные библиотечные ФБ, унифицируй их порты и соединения на уровне модели Studio только после проверки полного пути Studio -> ST/Lua -> VCont. Композиция нескольких отдельно транслируемых пользовательских FB типов поддерживается, но не воспроизводит полиморфизм `INTERFACE`; `CLASS`, `METHOD`, `INTERFACE`/`IMPLEMENTS` и `EXTENDS` остаются неподдерживаемыми. Не держи `INTERFACE` / `IMPLEMENTS` cases как expected-positive `supported_runtime`.

#### Действия `ACTION`

- Текущая VCStudio не поддерживает действия `ACTION`: не используй именованные секции `ACTION <name> ... END_ACTION` и их вызовы в Studio-compatible ST.
- По назначению действие выносит повторяющийся фрагмент логики POU под отдельным именем, сокращает дублирование и улучшает читаемость. Не смешивай эту конструкцию с SFC action qualifiers `N` / `S` / `R` / `L`: они относятся к отдельной SFC-модели исполнения, но также не поддерживаются в ST payload текущего Studio path.
- Для совместимого кода оставь один `FUNCTION_BLOCK` и перестрой управление так, чтобы общий фрагмент выполнялся в одном месте: вычисли условия и промежуточные значения заранее, затем используй общий `IF` / `CASE` участок. Не заменяй `ACTION` пользовательской `FUNCTION`, поскольку она также не поддерживается текущим Studio-bundled translator path.
- Если общую логику необходимо переиспользовать между несколькими POU, вынеси её в отдельно созданный библиотечный `FUNCTION_BLOCK` только после проверки его интерфейса и полного multi-type пути VCStudio -> ST/Lua -> VCont. Не держи `ACTION` cases как expected-positive `supported_runtime`.

#### Методы `METHOD`

- Методы в текущей VCStudio не реализованы. Не используй объявления `METHOD ... END_METHOD`, модификаторы и локальные секции метода, внутренние вызовы `MethodName(...)` или вызовы вида `Instance.MethodName(...)` в Studio-compatible ST.
- Метод обычно инкапсулирует именованную операцию POU и может работать с состоянием экземпляра, параметрами и возвращаемым значением. Распознанный translator token или созданный Lua-файл не доказывает, что Studio умеет создать, сохранить, связать и загрузить такой метод.
- Для совместимого кода перенеси вычисление в основной алгоритм owning `FUNCTION_BLOCK`: вычисли условия и промежуточные значения заранее и выполни общий участок один раз через `IF` / `CASE`. Не заменяй метод пользовательской `FUNCTION` или `ACTION`, поскольку обе конструкции также не поддерживаются текущим Studio path.
- Для переиспользования между POU используй отдельно созданный библиотечный `FUNCTION_BLOCK` только после проверки его интерфейса и полного multi-type пути VCStudio -> ST/Lua -> VCont. Не держи `METHOD` cases как expected-positive `supported_runtime`.

#### Свойства `PROPERTY`

- Свойства в текущей VCStudio не поддерживаются. Не используй объявления `PROPERTY ... END_PROPERTY`, секции `GET ... END_GET` / `SET ... END_SET` и обращения к свойству в Studio-compatible ST.
- По назначению `PROPERTY` предоставляет контролируемый доступ к переменной: setter может валидировать новое значение, отклонять недопустимую запись и выполнять логирование, а getter — возвращать текущее состояние без прямого доступа к внутреннему storage.
- Для совместимой контролируемой записи используй явный контракт одного owning `FUNCTION_BLOCK`: передавай новое значение через `VAR_INPUT` вместе с `WRITE_REQ`, проверяй диапазон и другие инварианты в основном алгоритме, обновляй внутренний `VAR` только при успехе и возвращай текущее значение, `WRITE_OK` и код ошибки через `VAR_OUTPUT`.
- Для логирования выдавай отдельный статус, счетчик или импульс события и подключай его к подтвержденному механизму журналирования Studio/VCont вне ST property. Не заменяй `PROPERTY` пользовательской `FUNCTION`, `METHOD` или `ACTION`, поскольку эти конструкции также не поддерживаются текущим Studio path. Не держи `PROPERTY` cases как expected-positive `supported_runtime`.

#### Композиция зависимых пользовательских ST FB и `EXTENDS`

- Разделяй две разные возможности. Один effective translator input поддерживает ровно один top-level `FUNCTION_BLOCK`; несколько объявлений в одном `source_code.st` остаются неподдерживаемыми. При этом Studio-проект может содержать несколько пользовательских ST FB типов и объявлять экземпляр одного типа внутри другого, например `C : CHILD33;` внутри `MAIN`.
- Не склеивай зависимый и корневой типы в один translator payload. Текущий binary может вернуть process exit code `0`, но пишет `unexpected 'FUNCTION_BLOCK'`, оставляет `script.lua` пустым и должен считаться завершившимся с ошибкой.
- Собери граф зависимостей по объявлениям экземпляров пользовательских FB типов. Транслируй каждый тип отдельным полным input `FUNCTION_BLOCK <TYPE> ... END_FUNCTION_BLOCK`; для Studio deploy сохраняй порядок от листьев к корню. Циклическую зависимость не пытайся упорядочить молча: останови deploy и покажи цикл.
- В Lua родительского типа ожидай persisted handle вида `local C = VCont.GetOrCreateFB("CHILD33", "C", fb)`, затем присваивания входов, вызов `C()` и чтение выходов. Имя типа и имя экземпляра должны соответствовать исходному объявлению; отсутствие этого кода — повод проверить распознавание типа и codegen до загрузки.
- Создай в VCont все требуемые `FBType` до назначения и `START` задачи. Канонический и безопасный порядок — зависимости, затем корневой тип, затем корневой runtime-экземпляр, `ASSIGN` и `START`. Обратный порядок `CREATE FBType` может работать, если все типы уже существуют к первому исполнению, но не закрепляй его как Studio contract.
- Не создавай отдельный top-level runtime-экземпляр каждого зависимого типа без цели теста: вложенные экземпляры создаются лениво через `VCont.GetOrCreateFB(..., fb)` и принадлежат родительскому экземпляру. Несколько вложенных экземпляров с разными именами должны иметь изолированное состояние.
- Проверяй композицию runtime-oracle, а не только переводом или ответами на `CREATE`: прочитай выход корневого экземпляра после исполнения. Для stateful цепочки выполни несколько циклов и проверь последовательность состояний; для глубокой цепочки проверь минимум три уровня `LEAF -> MIDDLE -> TOP`.
- Отсутствующий зависимый тип может не сорвать `CREATE` родительского `FBType`, но во время исполнения VCont пишет `Lua Lib create FB, type <TYPE> not found`, вложенный handle становится `nil`, а выход родителя может остаться начальным. Такой случай классифицируй как неполную загрузку dependency closure, а не как успешную композицию.
- В integration harness представляй каждый тип отдельным `translation_unit`, передавай Lua всех завершённых units в генераторы `fboot` и Studio-like command stream, а runtime-экземпляр и oracle привязывай к корневому типу.
- Эта поддержка относится только к композиции отдельных обычных `FUNCTION_BLOCK`. Она не добавляет поддержку наследования `FUNCTION_BLOCK Child EXTENDS Parent`, `ABSTRACT`, `INTERFACE`/`IMPLEMENTS`, `METHOD`, пользовательских `FUNCTION` или POU `PROGRAM`; проверяй такие конструкции независимо.
- Фактический Studio deploy log от 2026-08-05 подтвердил discovery `CHILD33, MAIN`, отдельную компиляцию обоих типов и child-first загрузку. На артефактах translator `7ee990a3` и VCont `2.1.0.27850` runtime-проверки подтвердили двух- и трёхуровневую композицию в `fboot` и Studio-like режимах, а также изоляцию stateful вложенных экземпляров.

#### Пространства имён `NAMESPACE`

- Пространства имён в текущей VCStudio не поддерживаются. Не используй блоки `NAMESPACE ... END_NAMESPACE` и ссылки на пользовательские типы, функции или функциональные блоки с квалификацией пространства имён в Studio-compatible ST.
- По назначению пространство имён группирует и изолирует символы, предотвращая конфликты одинаковых имён в больших проектах. Распознавание отдельных tokens транслятором или успешная работа одноимённого символа без namespace не доказывает поддержку этой модели.
- Для совместимого кода используй плоские уникальные ASCII-имена со стабильным префиксом подсистемы или библиотеки, например `DriveAsync_State` и `DriveSync_State`. Группировку модулей сохраняй в структуре проекта или библиотеки Studio, но не передавай `NAMESPACE` в ST payload.
- Учитывай остальные ограничения Studio path: пользовательские `TYPE` и `FUNCTION`, несколько типов `FUNCTION_BLOCK` в одном payload, `CLASS`, `INTERFACE` и наследование `EXTENDS` также не поддерживаются. Не пытайся воспроизвести namespace через эти конструкции и не держи `NAMESPACE` cases как expected-positive `supported_runtime`.

#### POU `PROGRAM`

- Объявления POU вида `PROGRAM <name> ... END_PROGRAM` не поддерживаются текущим Studio ST path. Studio editor grammar принимает текст алгоритма с необязательной обёрткой одного `FUNCTION_BLOCK`, а deploy path создаёт из него Lua FBType; модели top-level `PROGRAM` в этом payload нет.
- Текущий bundled translator может завершиться с exit code `0`, но на корректной IEC-форме `PROGRAM LUA_PROGRAM` пишет `Syntax error at line 1: unexpected 'LUA_PROGRAM'` и `Parse error`, не создавая `script.lua`. Считай это отказом трансляции до Studio load и VCont runtime.
- Не моделируй `PROGRAM` как обычный Lua FBType, не создавай его как экземпляр ФБ и не считай `READ` его `VAR_OUTPUT` корректным oracle. Привязка `PROGRAM ... WITH ...` внутри неподдерживаемого top-level `CONFIGURATION` не добавляет отсутствующую поддержку PROGRAM POU.
- Для Studio-compatible реализации перенеси алгоритм и данные в один owning `FUNCTION_BLOCK`, а его выполнение организуй через Control Loop и назначение задачи в модели Studio. Не держи cases, проверяющие объявление или task binding POU `PROGRAM`, как expected-positive `supported_runtime`; в смешанном кейсе удали raw `PROGRAM` surface и сохрани только самостоятельную поддерживаемую цель.

#### Top-level `CONFIGURATION`

- Ключевое слово `CONFIGURATION` и блоки `CONFIGURATION ... END_CONFIGURATION` не поддерживаются текущим Studio ST path. Не передавай в ST payload связанные объявления `RESOURCE ... END_RESOURCE`, `TASK`, привязки `PROGRAM ... WITH ...` и секции `VAR_CONFIG`, находящиеся внутри такой конфигурации.
- Не смешивай raw IEC configuration syntax с моделью проекта VCStudio. Studio позволяет настраивать Resource, Application, Control Loop, задачи и соединения через GUI и данные проекта, после чего формирует команды и fboot для VCont вне ST-алгоритма; это не доказывает, что editor, wrapper или bundled translator принимают `CONFIGURATION` в ST payload.
- Наличие корректного `FUNCTION_BLOCK` перед top-level `CONFIGURATION` не делает комбинированный payload поддерживаемым и не даёт основания проверять результат только по Lua, созданному для первого блока. Oracle должен подтверждать принятие всего исходного payload, Studio load и требуемую runtime-семантику.
- Для Studio-compatible реализации оставь в ST payload один owning `FUNCTION_BLOCK`, а периоды и приоритеты задач, назначение Control Loop, ресурсы и привязки задай в модели проекта Studio. Не держи cases, проверяющие `CONFIGURATION` или его дочерние объявления, как expected-positive `supported_runtime`; в смешанном кейсе удали configuration surface и сохрани только независимую поддерживаемую цель.

#### Пользовательские функции

- Объявления POU вида `FUNCTION ... END_FUNCTION` и вызовы пользовательских функций не поддерживаются текущим Studio-bundled translator path.
- Не распространяй это ограничение на поддерживаемые встроенные функции вроде `LEN`, `FIND` и преобразований `*_TO_*`, а также на экземпляры стандартных функциональных блоков: это отдельные конструкции.
- Для самого надежного обхода перенеси вычисление внутрь одного `FUNCTION_BLOCK` с явными `VAR_INPUT`/`VAR_OUTPUT` или используй подтвержденный стандартный ФБ.

### 4. Библиотека функциональных блоков

#### Функциональный блок `SEMA`

- В текущей typelibrary VCStudio отсутствует тип `SEMA` (`SEMA.fbt`); Studio не предоставляет готовый семафор для синхронизации доступа нескольких программных блоков к общему ресурсу.
- По назначению `SEMA` — примитив синхронизации для разделения общего ресурса между несколькими программными блоками, ПЛК-программами, задачами или ПАВ.
- Не используй объявление `Guard : SEMA;` в Studio-compatible ST и не считай успешную standalone-трансляцию доказательством поддержки. Транслятор может сгенерировать `VCont.GetOrCreateFB("SEMA", ...)`, но это не добавляет отсутствующий тип в библиотеку Studio и не подтверждает интерфейс или runtime-семантику `CLAIM` / `RELEASE` / `BUSY`.
- Для сценария, где два драйвера управляют одним двигателем, помести владение двигателем в один arbitration `FUNCTION_BLOCK`: передавай отдельные запросы драйверов через входы, явно храни текущего владельца, выдавай взаимоисключающие разрешения и определяй приоритет, освобождение и безопасное состояние. Не подменяй семафор двумя независимыми флагами или `VAR_GLOBAL`.
- Если требуется именно контракт `SEMA`, сначала добавь и проверь согласованный тип ФБ в typelibrary VCStudio и VCont, затем подтверди его интерфейс и поведение по полному пути Studio -> ST/Lua -> VCont -> Watch. До такой проверки считай `SEMA` неподдерживаемым vendor extension, а не стандартной возможностью IEC 61131-3.

### 5. Объявления, storage и структуры данных

#### Множественные объявления с инициализацией

- Не используй один инициализатор для нескольких имён в общем declaration: `A, B, C : INT := 2;` не поддерживается текущим Studio-bundled ST->Lua path.
- Объявление нескольких переменных без инициализации допустимо: `A, B, C : INT;`.
- Если каждой переменной нужно начальное значение, объявляй и инициализируй их отдельно:

```iecst
A : INT := 2;
B : INT := 2;
C : INT := 2;
```

- Применяй это правило одинаково к `VAR_INPUT`, `VAR_OUTPUT` и внутренним `VAR`; не держи multiple-name declaration с общим `:=` как expected-positive `supported_runtime` case.

#### `VAR_IN_OUT`

- Считай секцию `VAR_IN_OUT` неподдерживаемой в текущем Studio-bundled ST->Lua path независимо от типа переменной; это относится и к скалярам, и к `ARRAY`.
- Не держи `VAR_IN_OUT` cases как expected-positive `supported_runtime`: успешный editor parse сам по себе не доказывает translation/load/runtime semantics.
- Замени двунаправленный параметр парой явных портов `VAR_INPUT` и `VAR_OUTPUT`: передай исходное значение через вход, вычисли обновлённое значение внутри одного `FUNCTION_BLOCK` и верни его через выход. Обратную связь между экземплярами настраивай соединением Studio/VCont вне ST payload.

#### Ссылки и указатели

- Не используй `REFERENCE TO`, `POINTER TO`, `ADR(...)`, присваивание ссылки `REF=` и разыменование через `^` в текущем Studio-bundled ST->Lua path.
- Для `REFERENCE TO` primitive-типа текущий бинарник явно завершает translation с `Unsupported REFERENCE TO for primitive types`; не держи такую форму как expected-positive runtime case.
- Считай `POINTER TO`, получение адреса через `ADR(...)` и чтение или запись через `P^` неподдержанными независимо от того, распознаны ли отдельные tokens parser-ом.
- Замени alias/pointer-семантику явными scalar или одномерными `ARRAY` переменными и передавай значения через `VAR_INPUT`/`VAR_OUTPUT`. Если нужно изменить состояние другого экземпляра, используй явное соединение и отдельный выход, а не скрытую адресную связь.

#### Пользовательские `TYPE`, `STRUCT` и `UNION`

- Не используй top-level объявления `TYPE ... END_TYPE` как поддерживаемую конструкцию в Studio-authored ST: текущая `StructuredText.xtext` не включает их в grammar алгоритма.
- Не повышай capability по успешному standalone parse или translation. Scalar aliases, `ENUM`, subrange, array aliases и `STRUCT` могут распознаться, но текущий codegen теряет корректный internal/interface mapping — например, оставляет обращения `fb[IN_<name>]` при `numIntVars = 0` — либо VCont отклоняет пользовательский тип порта с `UNSUPPORTED_TYPE`.
- Учитывай, что `UNION` и часть сложных форм могут завершиться parse/translation error; конкретный diagnostic зависит от формы объявления.
- Распознавание `STRUCT` parser-ом или создание Lua-файла не доказывает корректные initialization, member access, `interfaceSpec` и VCont runtime mapping; Studio editor grammar также не принимает эту конструкцию.
- Для editor-safe end-to-end кода используй встроенные типы напрямую, явные скалярные порты и одномерные `ARRAY[1..N]` без alias. Разверни структуру в плоскую схему; `ENUM`/subrange моделируй встроенным integer, именованными константами и явными range checks.
- Скалярная проекция и одномерный `ARRAY[1..N]` подтверждены в обоих VCont load path, но это не доказывает сохранение layout исходной структуры.
- Не держи `TYPE ... END_TYPE`, aliases, `ENUM`, subrange, `STRUCT` или `UNION` как expected-positive `supported_runtime`: parser-only evidence относится только к inventory грамматики.

#### `RETAIN` и `PERSISTENT`

- Квалификаторы переменных `RETAIN` и `PERSISTENT` не поддерживаются текущим Studio-bundled ST->Lua path.
- Не считай обычную внутреннюю переменную эквивалентом retained/persistent storage и не обещай сохранение значения после перезапуска, cold start или повторной загрузки.
- Если состояние должно переживать перезапуск, используй отдельно подтверждённый механизм хранения Studio/VCont и проверяй lifecycle на реальном runtime.
- Обычный внутренний `VAR` подтвержден только как состояние между циклами одного запущенного FB. Warm-start persistence относится к VCont DB lifecycle (`DBSAVE`, `LoadDBAtStartup`, `SaveOutputs`/параметры сохранения) и не доказывает семантику ST qualifiers.

#### Тип `CHAR`

- Тип данных `CHAR` не поддерживается текущим Studio-bundled ST->Lua path.
- Для текстового значения используй подтверждённый для конкретного сценария `STRING`; если требуется ровно один символ, обеспечь это ограничение явно в логике и отдельно проверь encoding/runtime behavior.
- Считай неподдерживаемыми все встроенные преобразования, которые принимают или возвращают `CHAR`: семейства `CHAR_TO_*` и `*_TO_CHAR`, включая `CHAR_TO_INT(...)`, `INT_TO_CHAR(...)`, `CHAR_TO_STRING(...)` и составные цепочки преобразований. Успешная standalone translation отдельного вызова не доказывает end-to-end поддержку.
- Для одиночного ASCII-символа используй `STRING := 'A'` и явно проверяй `LEN(...) = 1`; это не предоставляет числовой код символа и не является заменой `CHAR_TO_INT(...)`.

#### Прямая адресация `AT %...`

- Не полагайся на declarations вида `Input AT %IX0.0`, `Flag AT %QX0.1` или `Word AT %MW10` внутри translated ST.
- Даже если Studio interface parser извлёк `AT` metadata или translator принял declaration, это не доказывает реальную привязку к process image VCont.
- Передавай данные через явные `VAR_INPUT`/`VAR_OUTPUT` порты и настраивай физическую, Modbus или иную runtime-привязку вне ST algorithm через Studio/VCont configuration.

#### `VAR_GLOBAL` и `VAR_EXTERNAL`

- Не считай `VAR_GLOBAL` поддерживаемой общей памятью controller scope между POU, типами ФБ или экземплярами.
- Узкий standalone пример может распознаться и понизиться до обычной Lua `local`; такой green test доказывает только локальное вычисление, но не shared lifetime, visibility или synchronization semantics.
- Внешнее связывание имени с controller-global storage не поддержано; parser обычно завершается syntax/parse error и не создаёт пригодный Lua artifact.
- Не эмулируй `VAR_EXTERNAL` неявным Lua global: это меняет lifetime, isolation и поведение нескольких экземпляров.
- Помести состояние в один owning FB и передавай его через явные входы, выходы и Studio connections. Если нужна product-specific shared storage, моделируй и проверяй её отдельно на runtime contract.

#### Массивы

- Используй только массивы с нижней границей `1`: `ARRAY[1..N] OF T`. Начальная индексация с `0`, отрицательного или любого другого значения не поддерживается текущим Studio-bundled ST->Lua path.
- Считай формы `ARRAY[0..N]`, `ARRAY[2..N]` и `ARRAY[-N..N]` end-to-end unsupported, даже если parser принимает declaration: Studio interface extraction сохраняет размер массива, но не его нижнюю границу, а Lua/VCont mapping использует индексацию от `1`.
- При переносе `ARRAY[L..U]` в поддерживаемую форму объявляй `ARRAY[1..U-L+1]` и согласованно преобразуй каждое обращение `A[I]` в `A[I-L+1]`, включая циклы, инициализацию и runtime oracle. Не заменяй только границы declaration: это изменит семантику индексов.
- Не используй `ARRAY[1..2] OF ARRAY[1..3] OF INT` как поддерживаемый тип. Также не считай `ARRAY[1..2, 1..3] OF INT` безопасной заменой только потому, что standalone translation завершилась.
- Текущий end-to-end path не гарантирует корректные `interfaceSpec`, initialization, indexing и VCont runtime mapping для nested/multidimensional shapes.
- Не приписывай direct nested syntax конкретный parser diagnostic без минимального repro: это compatibility guardrail, а смежные multidimensional формы могут пройти translation и сломаться только в runtime.
- Разверни данные в одномерный `ARRAY[1..N] OF T` и вычисляй индекс явно, либо используй несколько отдельных одномерных массивов. Проверяй чтение/запись через фактический load и Watch/`READ` oracle.
- Не держи lower-bound, nested или multidimensional array cases как expected-positive `supported_runtime`.

### 6. Runtime management endpoints

#### Indexed runtime `READ` / `WRITE` массива

- Не путай индексирование внутри ST с адресом VCont management protocol. Выражения `A[1]` и `A[2]` поддерживаются в алгоритме ST, но runtime endpoint существует только для целого interface-порта `A`; адреса `...A[2]`, `...A.2` и `...A(2)` возвращают `NO_SUCH_OBJECT` в `fboot` и Studio-like load path. Это относится как к прямому `WRITE`, так и к прямому `READ` элемента.
- Для runtime-записи передавай bracket literal в целый порт: `WRITE A <- [1,12]`, `WRITE A <- [FALSE,TRUE]`. После успешной записи проверяй нужный элемент через scalar projection в ST или читай весь порт `A`; не создавай expected-positive cases с indexed management endpoint.
- Для `ARRAY OF TIME` избегай нулевого элемента в форме `T#0ms` внутри runtime array literal: `[T#10ms,T#0ms]` на проверенном VCont отвечает `BAD_PARAMS`, хотя успевает частично изменить массив. Используй числовой `0`, например `[T#10ms,0]`, и учитывай текущую nanosecond-like семантику: `TIME_TO_DINT(T#10ms) = 10_000_000`.
- Если цель теста — именно indexed runtime `READ` / `WRITE`, удали такой кейс как неактуальный для текущего management contract. Смешанный кейс можно сохранить только после удаления indexed endpoint и с самостоятельным oracle на поддерживаемую whole-array запись или ST member access; не заменяй ожидаемый результат исходным initial value, иначе неуспешный `WRITE` даст ложноположительный тест.

### Диагностический checklist

1. Сохрани original, effective и rewritten payload, чтобы не потерять источник несовместимости.
2. Если usable Lua не создан, классифицируй результат как translator limitation, а не VCont runtime failure.
3. Если Lua создан, но load/initialization завершились ошибкой, укажи точную wrapper/load/runtime boundary.
4. Если load успешен, но `READ`/Watch расходится с oracle, проверяй codegen и runtime semantics; не повышай status по
   одному translation pass.

## Lua InterfaceSpec

Studio Java builds `interfaceSpec` around translator output.

Event/data rules:

- `numEIs = 1`, `EINames = {"<event>"}`;
- `numEOs = 1`, `EONames = {"<event>"}`;
- `EIWith` is zero-based input data positions followed by `255`;
- `EOWith` is zero-based output data positions followed by `255`;
- `EIWithIndexes = {0}` and `EOWithIndexes = {0}`;
- `DINames`, `DONames`, `DIDataTypeNames`, `DODataTypeNames` come from parsed interface vars;
- scalar type is serialized as `"TYPE"`;
- array type is serialized as `"ARRAY", <size>, "ELEMENT_TYPE"`;
- time aliases are normalized for deploy type names: `TOD` -> `TIME_OF_DAY`, `LTOD` -> `LTIME_OF_DAY`, `DT` -> `DATE_AND_TIME`, `LDT` -> `LDATE_AND_TIME`. Это только wrapper serialization rule: оно не отменяет известное ограничение на `LTIME`, `LTOD`/`LTIME_OF_DAY` и `LDT`/`LDATE_AND_TIME`.

After translator output, Studio appends:

```lua
return {execute = execute, setInitialValues = setInitialValues, interfaceSpec = interfaceSpec, internalVarsInformation = internalVarsInformation}
```

With auth disabled, the Lua request body is XML-escaped for `&`, `<`, `>`, `"`, and `'`. With auth enabled, Studio calls `JWTHelper.encryptLua(...)` instead of XML-escaping the Lua body.

## Translator-Supported Syntax For Candidate Tests

The bundled translator parser recognizes more syntax than the Studio editor, but parser recognition is not the same as supported semantics:

- `TYPE` with enum, struct, type alias, and named subrange;
- `VAR_INPUT`, `VAR_OUTPUT`, `VAR`, `VAR_TEMP`; limited `VAR_GLOBAL` forms may parse, but shared global semantics is unsupported, and `VAR_EXTERNAL` is unsupported;
- `IF` / `ELSIF` / `ELSE`;
- `CASE`, including comma labels and numeric ranges;
- `FOR`, `WHILE`, `REPEAT`, `EXIT`, `CONTINUE`, `RETURN`;
- one-dimensional `ARRAY[1..N]`, array literals, and repeated initializer groups; lower bounds other than `1`, nested arrays, and multidimensional arrays are not end-to-end supported;
- tokens ссылок и указателей могут распознаваться parser-ом, но `REFERENCE TO`, `POINTER TO`, `ADR(...)`, `REF=` и `^` не входят в поддерживаемый end-to-end subset;
- member access, array indexing, named FB-call arguments, and `=>` output assignments.

Use this set for translator coverage, but use the editor-safe subset for Studio-integration coverage unless a real Studio log proves the construct passes through the UI path.

## Source-Observed Codegen Rules

Observed from real Studio logs and the local translator binary:

- `STRING` interface ports are ordinary data ports; string initializer becomes a Lua string literal.
- `LEN(x)` maps to `string.len(x)`.
- `FIND(a, b)` maps to `Builtins.find({a, b})`.
- `REAL_TO_INT(x)` maps through `TypeConversion.truncate_real(...)` and `TypeConversion.trim_by_type(..., 16, true)`.
- `INT_TO_REAL(x)` maps to `TypeConversion.to_real(x)`.
- `TIME` literals are nanosecond-like integer values in the generated Lua; `T#500ms` becomes `500000000`.
- Internal `VAR` scalars are stored through `fb[268435456 + offset]` and described by `internalVarsInformation`.
- Interface array input initializers are emitted element-by-element, for example `fb[DI_VALUES][1] = 1`.
- Interface array output without explicit initializer may not be initialized in `setInitialValues`, but execute code can still write elements like `fb[DO_VALUES][1]`.
- `CASE` is lowered to Lua `if` / `elseif` / `else`; comma labels become `or` expressions.
- Standard FB declarations such as `TMR : TON;` are emitted as local persisted FB handles inside `execute`, for example `local TMR = VCont.GetOrCreateFB("TON", "TMR", fb)` in the current bundled binary, then field assignments, call, and member reads.

Standard FB names recognized by the translator lexer include:

- timers/latches/triggers: `TON`, `TOF`, `TP`, `SR`, `RS`, `R_TRIG`, `F_TRIG`;
- counters: `CTU`, `CTD`, `CTUD` plus typed variants recognized by the lexer.

Для фактического имени counter FB сверяй typelibrary, а не только lexer. В текущей VCStudio-библиотеке базовый `CTD` уже является `INT`-вариантом; не используй несуществующий alias `CTD_INT`. Суффиксный вариант допустим только при наличии точного `.fbt`, например `CTD_DINT`; распознанное lexer-ом имя без соответствующего runtime FB может перевестись в `VCont.GetOrCreateFB("<name>", ...)`, но сорвать исполнение всего Lua FB.

Supported built-in function families are source-derived from `StructuredTextSupportedFunctions.java` and `operator_mapper.py`; high-value integration candidates include arithmetic/comparison (`ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `EQ`, `NE`, `GT`, `GE`, `LT`, `LE`), strings (`CONCAT`, `LEN`, `FIND`, `LEFT`, `RIGHT`, `MID`, `INSERT`, `DELETE`, `REPLACE`), selection (`SEL`, `MUX`, `LIMIT`, `MAX`, `MIN`), bit/endian (`SHL`, `SHR`, `ROL`, `ROR`, `TO_BIG_ENDIAN`, `FROM_BIG_ENDIAN`), time split/conversion (`DAY_OF_WEEK`, `SPLIT_DATE`, `SPLIT_TOD`, `SPLIT_DT`), and confirmed `*_TO_*` conversions, excluding `CHAR_TO_*`, `*_TO_CHAR`, and other families covered by the known limitations above.

## Integration-Test Guardrails

- Studio-like ST tests should use editor-safe fragment syntax unless testing a known Studio/compiler mismatch.
- Consult `Known ST->Lua Translator Limitations` before generating or normalizing ST; do not silently preserve an unsupported construct.
- Keep translator-only tests separate from Studio-integration tests.
- Do not infer Studio acceptance from `data/st-lua/linux.dist/main.bin` alone.
- Do not infer runtime behavior from generated Lua shape alone; load into VCont and observe through Studio-like Watch protocol or an explicitly marked deterministic runtime oracle.
- When a real Studio log disagrees with this file, prefer the log and inspect the corresponding source path before updating the skill.
