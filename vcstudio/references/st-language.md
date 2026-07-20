# Structured Text In VCStudio

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

Считай следующие конструкции неподдержанными в текущем Studio-bundled ST->Lua path, пока новая версия бинарника не доказана end-to-end. Валидность по IEC 61131-3, распознанный lexer/parser token, exit code `0` или созданный Lua-файл сами по себе не доказывают корректную семантику в Studio и VCont.

### Прагмы `{...}`

- Не используй `{attribute ...}` и другие vendor pragmas в коде, передаваемом транслятору.
- Не трактуй текст в фигурных скобках как обычный комментарий: по ST это контейнер прагмы, а её семантика зависит от реализации.
- Удали pragma из effective translator input или перенеси metadata во внешний Studio/project configuration. Для обычных пояснений используй `(* ... *)` или `//`, проверяя их отдельно от pragma behavior.
- Не удаляй неизвестную или семантически значимую pragma молча: сначала выясни её назначение и воспроизведи эффект поддерживаемой конфигурацией либо останови перенос как behavior-changing.

### UTF-8 / non-ASCII в идентификаторах

- Имена переменных, полей, типов и других ST symbols задавай только ASCII-идентификаторами: латинские буквы `A-Z`/`a-z`, цифры и `_`, например `counter` вместо `счётчик`.
- Кириллица и другие UTF-8/non-ASCII символы в идентификаторах не поддерживаются текущим translator path.
- Текущий lexer может выдать серию `Illegal character`, затем syntax/parse error без пригодного Lua artifact.
- При автоматическом переименовании сохраняй явную таблицу `original -> effective`, чтобы диагностика и связь с исходным проектом не потерялись.
- Не обобщай это ограничение на комментарии и string literals: UTF-8 data является отдельной capability и требует отдельного теста.

### Пользовательские функции

- Объявления POU вида `FUNCTION ... END_FUNCTION` и вызовы пользовательских функций не поддерживаются текущим Studio-bundled translator path.
- Не распространяй это ограничение на поддерживаемые встроенные функции вроде `LEN`, `FIND` и преобразований `*_TO_*`, а также на экземпляры стандартных функциональных блоков: это отдельные конструкции.
- Перенеси пользовательскую функцию в `FUNCTION_BLOCK` с явными `VAR_INPUT`/`VAR_OUTPUT` и вызывай логику через экземпляр ФБ.

### Пользовательские структуры данных

- Не используй объявления `TYPE ... STRUCT ... END_STRUCT ... END_TYPE` и переменные пользовательских структур как поддерживаемую end-to-end возможность.
- Распознавание `STRUCT` parser-ом или создание Lua-файла не доказывает корректные initialization, member access, `interfaceSpec` и VCont runtime mapping; Studio editor grammar также не принимает эту конструкцию.
- Разверни структуру в отдельные скалярные переменные или поддерживаемые одномерные массивы и передавай данные через явные порты.

### `RETAIN` и `PERSISTENT`

- Квалификаторы переменных `RETAIN` и `PERSISTENT` не поддерживаются текущим Studio-bundled ST->Lua path.
- Не считай обычную внутреннюю переменную эквивалентом retained/persistent storage и не обещай сохранение значения после перезапуска, cold start или повторной загрузки.
- Если состояние должно переживать перезапуск, используй отдельно подтверждённый механизм хранения Studio/VCont и проверяй lifecycle на реальном runtime.

### Тип `CHAR`

- Тип данных `CHAR` не поддерживается текущим Studio-bundled ST->Lua path.
- Для текстового значения используй подтверждённый для конкретного сценария `STRING`; если требуется ровно один символ, обеспечь это ограничение явно в логике и отдельно проверь encoding/runtime behavior.

### Прямая адресация `AT %...`

- Не полагайся на declarations вида `Input AT %IX0.0`, `Flag AT %QX0.1` или `Word AT %MW10` внутри translated ST.
- Даже если Studio interface parser извлёк `AT` metadata или translator принял declaration, это не доказывает реальную привязку к process image VCont.
- Передавай данные через явные `VAR_INPUT`/`VAR_OUTPUT` порты и настраивай физическую, Modbus или иную runtime-привязку вне ST algorithm через Studio/VCont configuration.

### `VAR_GLOBAL`

- Не считай `VAR_GLOBAL` поддерживаемой общей памятью controller scope между POU, типами ФБ или экземплярами.
- Узкий standalone пример может распознаться и понизиться до обычной Lua `local`; такой green test доказывает только локальное вычисление, но не shared lifetime, visibility или synchronization semantics.
- Помести состояние в один owning FB и передавай его через явные порты/соединения. Если нужна product-specific shared storage, моделируй и проверяй её отдельно на runtime contract.

### `VAR_EXTERNAL`

- Внешнее связывание имени с controller-global storage не поддержано; parser обычно завершается syntax/parse error и не создаёт пригодный Lua artifact.
- Не эмулируй `VAR_EXTERNAL` неявным Lua global: это меняет lifetime, isolation и поведение нескольких экземпляров.
- Замени external dependency явным входом/выходом и Studio connection от owning FB.

### Вложенные и многомерные массивы

- Не используй `ARRAY[1..2] OF ARRAY[1..3] OF INT` как поддерживаемый тип. Также не считай `ARRAY[1..2, 1..3] OF INT` безопасной заменой только потому, что standalone translation завершилась.
- Текущий end-to-end path не гарантирует корректные `interfaceSpec`, initialization, indexing и VCont runtime mapping для nested/multidimensional shapes.
- Не приписывай direct nested syntax конкретный parser diagnostic без минимального repro: это compatibility guardrail, а смежные multidimensional формы могут пройти translation и сломаться только в runtime.
- Разверни данные в одномерный `ARRAY[1..N] OF T` и вычисляй индекс явно, либо используй несколько отдельных одномерных массивов. Проверяй чтение/запись через фактический load и Watch/`READ` oracle.

### Handling rule

1. Перед переводом найди эти конструкции в effective ST input; сохрани отдельно original и rewritten payload для диагностики.
2. Если usable Lua не создан, классифицируй результат как translator limitation, а не VCont runtime failure.
3. Если Lua создан, но load/initialization/`READ` неверны, классифицируй конструкцию как end-to-end unsupported; не повышай status по одному translation pass.
4. После замены translator binary перепроверь минимальный repro, Studio wrapper/load path и VCont oracle. Только после этого меняй этот compatibility contract.

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
- time aliases are normalized for deploy type names: `TOD` -> `TIME_OF_DAY`, `LTOD` -> `LTIME_OF_DAY`, `DT` -> `DATE_AND_TIME`, `LDT` -> `LDATE_AND_TIME`.

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
- one-dimensional arrays, array literals, and repeated initializer groups; nested and multidimensional arrays are not end-to-end supported;
- `REFERENCE TO` for non-primitive/non-enum/non-subrange types;
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
- counters: `CTU`, `CTD`, `CTUD` plus typed variants such as `CTU_INT`, `CTD_UDINT`, `CTUD_LINT`.

Supported built-in function families are source-derived from `StructuredTextSupportedFunctions.java` and `operator_mapper.py`; high-value integration candidates include arithmetic/comparison (`ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `EQ`, `NE`, `GT`, `GE`, `LT`, `LE`), strings (`CONCAT`, `LEN`, `FIND`, `LEFT`, `RIGHT`, `MID`, `INSERT`, `DELETE`, `REPLACE`), selection (`SEL`, `MUX`, `LIMIT`, `MAX`, `MIN`), bit/endian (`SHL`, `SHR`, `ROL`, `ROR`, `TO_BIG_ENDIAN`, `FROM_BIG_ENDIAN`), time split/conversion (`DAY_OF_WEEK`, `SPLIT_DATE`, `SPLIT_TOD`, `SPLIT_DT`), and `*_TO_*` conversions.

## Integration-Test Guardrails

- Studio-like ST tests should use editor-safe fragment syntax unless testing a known Studio/compiler mismatch.
- Consult `Known ST->Lua Translator Limitations` before generating or normalizing ST; do not silently preserve an unsupported construct.
- Keep translator-only tests separate from Studio-integration tests.
- Do not infer Studio acceptance from `data/st-lua/linux.dist/main.bin` alone.
- Do not infer runtime behavior from generated Lua shape alone; load into VCont and observe through Studio-like Watch protocol or an explicitly marked deterministic runtime oracle.
- When a real Studio log disagrees with this file, prefer the log and inspect the corresponding source path before updating the skill.
