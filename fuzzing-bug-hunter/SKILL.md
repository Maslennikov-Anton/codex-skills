---
name: fuzzing-bug-hunter
description: "Искать новые defect families через matrix/grammar fuzzing: failure surface и минимальные repro; not ordinary regression, manual exploratory or known-bug root cause."
---

# Fuzzing Bug Hunter

Используй этот skill, когда цель - расширить карту отказов системы и найти новые defect families, а не просто покрыть известный сценарий тестом.

## Gate

Подходит, если нужно:

- исследовать матрицу `construct x context x operand-shape`;
- понять supported/unsupported границы;
- отделить новые defect families от вариаций уже известного бага;
- превратить находки в минимальные repro и declarative cases.

Не подходит для обычного regression test (`autotest-engineer`), root cause уже найденной поверхности (`systematic-debugging`), review fuzz artifacts (`code-review-professional`) или ручной exploratory-проверки (`manual-tester`).

## Workflow

1. Определи поверхность: grammar, parser, codegen, runtime, input hygiene или diagnostics.
2. Проверь существующий inventory: `tests/cases`, generators, matrix artifacts, текущие красные случаи.
3. Сформулируй минимальную, но полезную матрицу и гипотезу о границе.
4. Запусти исследование с правдивым signal:
   - отдели harness/setup noise от дефекта;
   - сними representative raw diagnostic;
   - классифицируй parser/codegen/runtime/environment/diagnostics failure.
5. После нового сигнала минимизируй repro, оформи case с собственным oracle, при необходимости обнови временную сводку failing cases и прогони baseline.
6. Если новых defects нет, зафиксируй проверенную поверхность, confirmed supported границы и следующий рациональный фронт.

## Rules

- Цель fuzzing-а - знание о failure surface, а не покрытие ради покрытия.
- Не превращай matrix в случайные комбинации без гипотезы.
- Один новый defect family ценнее многих дубликатов без новой границы.
- Не озеленяй результаты удалением плохих входов или ослаблением oracle; `xfail` не используем.
- Если reproducer начал проходить, актуализируй кейс/гипотезу: переведи в supported regression или удали устаревший artifact.
- Проверенная поверхность без новых багов - полезный результат, фиксируй его явно.

## Typical Axes

- selector/context matrix для control flow.
- built-in argument matrix.
- placement/context matrix для standard blocks.
- input hygiene matrix.
- diagnostics normalization matrix.
- sequence-level combinations unsupported forms.

## Формат результата

Верни: исследованную поверхность, матрицу/гипотезу, найденные defect families, confirmed supported зоны, обновленные artifacts и следующий фронт исследования.

## Related Skills

- `autotest-engineer` -> stable regression tests по найденным дефектам.
- `systematic-debugging` -> доказательство root cause.
- `code-review-professional` -> review fuzz/repro artifacts.
- `team-engineering-style` -> закрепление устойчивого процесса fuzzing.
