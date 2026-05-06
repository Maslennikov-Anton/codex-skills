# Prompt Contracts

## Worker Prompt

```text
Ты не один в codebase: другие агенты и основной агент могут менять соседние зоны.

Ownership:
- Ты отвечаешь только за: ...
- Не изменяй: ...
- Не откатывай чужие изменения.

Task:
- ...

Context:
- ...

Implementation constraints:
- Следуй существующим patterns.
- Держи scope узким.
- Не добавляй unrelated refactors.

Verification:
- Запусти: ...
- Если проверка невозможна, объясни почему.

Final response:
- Summary.
- Changed paths.
- Commands run and results.
- Risks or follow-up.
```

## Explorer Prompt

```text
Ответь на узкий вопрос по codebase. Не меняй файлы.

Question:
- ...

Scope:
- Искать в: ...
- Игнорировать: ...

Return:
- Direct answer.
- File references with line numbers.
- Relevant constraints or risks.
```

## Review Prompt

```text
Проведи review результата subagent.

Review mode:
- Spec compliance OR code quality.

Expected scope:
- ...

Diff or files:
- ...

Return findings first:
- Severity.
- File/line.
- Why this matters.
- Required fix.

If no findings:
- Say clearly.
- Mention residual risk or unverified area.
```

## Ownership Rules

- Один файл не должен быть write-owned двумя worker'ами одновременно.
- Shared config, lockfiles, migrations и public contracts требуют отдельной coordination task.
- Если worker обнаружил необходимость выйти за ownership, он должен остановиться и сообщить, а не расширять scope самостоятельно.
