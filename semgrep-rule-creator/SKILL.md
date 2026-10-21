---
name: semgrep-rule-creator
description: "Создавать и проверять Semgrep rules для известного bug pattern: positive/negative fixtures, AST/taint и precision; not general bug discovery or unreviewed CI enablement."
---

# Правила Semgrep для известной ошибки

Статус: `experimental`. Превращай подтвержденную причину в воспроизводимый статический guard. Совпадение правила — кандидат, пока контракт и контекст не подтверждены.

## Workflow

1. Получи известный failing пример, root cause, поддержанный контракт и безопасный контрпример. Если причины еще нет, сначала debugging или discovery; для поиска вариантов — `variant-analysis`.
2. Проверь установленную версию `semgrep --version`, язык и нужные возможности по official docs. Используй локальный CLI; если его нет, изолированный venv подходит для разрешенного пилота. Не меняй зависимости проекта автоматически.
3. Создай минимальный rule и paired fixture: `ruleid: ID` перед опасной строкой, `ok: ID` перед похожей безопасной строкой. Добавь переименование переменных, безопасный guard, другой контракт и существенные синтаксические варианты. Держи исключения узкими и объясненными.
4. Используй AST patterns для структуры; taint — когда риск зависит от source → sink и sanitizers. Не заменяй доказательство data flow совпадением текста. Детали и команды: [references/rule-testing.md](references/rule-testing.md).
5. Запусти unit tests rule и read-only scan ограниченного scope. Проверь parsing errors, skipped files и реальные finding locations, а не один exit code. Если rule пропускает известный вариант или ловит safe control, уточни его и повтори проверку.
6. Верни правило, fixture, команды/версию, подтвержденные находки и известные ограничения. Запуск в CI, autofix и массовая правка — только в пределах задачи; не включай guard до проверки precision.

Проверка rules может работать с `--metrics=off` и локальным `--config`; не нужны облачный аккаунт или отправка исходников. Не отключай действующие repo policies ради запуска.

Источники и лицензия: [references/upstream.md](references/upstream.md).
