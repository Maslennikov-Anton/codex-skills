# Feedback Triage

## Таблица разбора

```markdown
| Item | Source | Severity | Decision | Reason | Status |
| --- | --- | --- | --- | --- | --- |
| ... | user/reviewer/tool | critical/important/minor | fix/clarify/push-back/defer | ... | open/done |
```

## Decision Rules

- `fix`: feedback технически корректен, scope понятен, изменение не ломает contracts.
- `clarify`: требование неоднозначно или несколько interpretations ведут к разным changes.
- `push-back`: suggestion ломает behavior, конфликтует с constraints, нарушает YAGNI или основан на неверной предпосылке.
- `defer`: item minor, не входит в текущий scope, но полезен как follow-up.

## Pushback Template

```markdown
Проверил этот пункт. В текущем codebase <факт>.

Предложенное изменение <последствие>.
Поэтому я бы не менял это в текущем scope. Альтернатива: <вариант>.
```

## Fix Response Template

```markdown
Исправлено: <что изменено>.
Проверка: `<command>` -> <result>.
```

## Clarification Template

```markdown
Пункты <A, B> понятны. По пункту <C> нужны уточнения: <конкретный вопрос>.
Не начинаю partial implementation, потому что варианты меняют <contract/files/behavior>.
```
