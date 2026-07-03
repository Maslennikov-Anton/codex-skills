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

The bundled translator parser supports more syntax than the Studio editor:

- `TYPE` with enum, struct, type alias, and named subrange;
- `VAR_INPUT`, `VAR_OUTPUT`, `VAR`, `VAR_TEMP`, `VAR_GLOBAL`;
- `IF` / `ELSIF` / `ELSE`;
- `CASE`, including comma labels and numeric ranges;
- `FOR`, `WHILE`, `REPEAT`, `EXIT`, `CONTINUE`, `RETURN`;
- arrays, array literals, repeated initializer groups, and multidimensional arrays;
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
- Keep translator-only tests separate from Studio-integration tests.
- Do not infer Studio acceptance from `data/st-lua/linux.dist/main.bin` alone.
- Do not infer runtime behavior from generated Lua shape alone; load into VCont and observe through Studio-like Watch protocol or an explicitly marked deterministic runtime oracle.
- When a real Studio log disagrees with this file, prefer the log and inspect the corresponding source path before updating the skill.
