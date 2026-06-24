# Structured Text In VCStudio

## Модель

VCStudio умеет создавать функциональные блоки и контуры на Structured Text. В основе - трансляция ST в исполняемый Lua-код. Это позволяет использовать Lua-библиотеки, кросс-платформенность, Lua debug/profiling tooling.

Для проверки совместимости ST translator со Studio важен полный путь `ST -> Lua -> VCont -> IDE READ`. Standalone translation полезна как диагностика, но не доказывает, что результат загрузится из Studio или будет читаем через monitoring/READ.

ST syntax близок к Pascal. По IEC 61131-3 ключевые конструкции принято писать заглавными буквами. Пробелы и табуляция не влияют на синтаксис.

Присваивание:

```pascal
variable := value;
```

Многострочный комментарий:

```pascal
(* comment *)
```

## Операторы и типы

Arithmetic: `+`, `-`, `*`, `/`, `mod`.

Logic: `OR`, `AND`, `XOR`, `NOT`.

Comparison: `=`, `<>`, `>`, `>=`, `<`, `<=`. Comparison result is always `BOOL`.

Типы:

- integers: `SINT`, `USINT`, `INT`, `UINT`, `DINT`, `UDINT`, `LINT`, `ULINT`;
- real: `REAL`, `LREAL`;
- bit strings: `BYTE`, `WORD`, `DWORD`, `LWORD`;
- `BOOL`, `STRING`;
- time/date: `TIME`, `TOD`, `DATE`, `DT`.

Доступ к битам возможен напрямую:

```pascal
a.3 := 1;
```

По умолчанию переменные инициализируются нулем, если явно не задано другое значение:

```pascal
str1: STRING := 'Hello world';
```

## Создание ST Function Block

Путь в Studio:

1. ПКМ по `UserLibrary`.
2. `Создать ФБ`.
3. Задать имя будущего ФБ и тип `Структурированный текст`.
4. В редакторе блока открыть вкладку `Алгоритм`.
5. Описать входы/выходы и algorithm.
6. На вкладке `Интерфейс` проверить имя, количество и тип портов.
7. Сохранить проект; новый ФБ будет доступен в `UserLibrary`.

Минимальный каркас:

```pascal
VAR_INPUT
    IN: BOOL;
END_VAR

VAR_OUTPUT
    OUT: BOOL;
END_VAR

OUT := NOT IN;
```

В документе в примере используются `VAR_END`, но стандартный IEC-вариант - `END_VAR`; при реализации сверяй с текущим ST translator.

## Control Flow

`CASE`:

```pascal
CASE STATE_NUM OF
    1:
        MESS := 'ONE';
    2..5:
        MESS := 'TWO-FIVE';
    6,7,8:
        MESS := 'SIX-EIGHT';
    ELSE
        MESS := 'UNREAL_STATE';
END_CASE;
```

`IF`:

```pascal
IF IN_VAL = 7 THEN
    MESS := 'SEVEN';
ELSIF IN_VAL > 10 AND 15 >= IN_VAL THEN
    MESS := '10-15 RANGE';
ELSE
    MESS := 'INVALID';
END_IF;
```

`FOR`:

```pascal
FOR I := 1 TO N / 2 BY 1 DO
    COUNT := COUNT + 2;
END_FOR;
```

If `BY` is omitted, step is `1`. For reverse iteration use negative step. `EXIT` can terminate loops early.

`WHILE`:

```pascal
WHILE (STR_LEN >= i) AND (POS = 0) DO
    IF IN_STRING[i] = FIND_SYMBOL THEN
        POS := i;
    END_IF;
    i := i + 1;
END_WHILE;
```

Use `WHILE` carefully in control algorithms: while executing the loop, controller logic may not observe changed FB inputs and can miss emergency conditions. Typical safe use: initialization or bounded string search.

`REPEAT`:

```pascal
REPEAT
    IF IN_STRING[i] = FIND_SYMBOL THEN
        POS := i;
    END_IF;
    i := i + 1;
UNTIL i > STR_LEN OR POS > 0
END_REPEAT;
```

`REPEAT` executes at least once. It has the same control-risk caveat as `WHILE`.

## Arrays

Arrays require fixed bounds:

```pascal
VAR
    values : ARRAY [1..10] OF INT;
END_VAR
```

Initialization examples:

```pascal
VAR
    arr : ARRAY [-2..2] OF INT := [1, 2, 3, 4];
    matrix1 : ARRAY [1..2, 1..3] OF INT := [2([3(25)])];
    matrix2 : ARRAY [1..2, 1..3] OF INT := [[11, 12, 13], [21, 22, 23]];
END_VAR
```

Uninitialized elements receive default values. Dynamic/unbounded arrays are not supported because PLC execution needs predictable memory and timing. Constant variables may define bounds.

Arrays can contain FB instances, for example timers with initialized inputs.

## ENUM And State Machines

`ENUM` defines named constants:

```pascal
TYPE E_STATE :
(
    IDLE := 0,
    START := 100,
    STOP := 200
);
END_TYPE
```

Common use: state machines via `CASE`. Prefer explicit numeric values when state compatibility matters across versions or generated artifacts.
