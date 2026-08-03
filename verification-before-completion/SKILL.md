---
name: verification-before-completion
description: "Use before evidence-backed success claims after implementation, fix, tests, build/lint, commit, push, PR, or completed verification; skip pure analysis/status."
---

# Verification Before Completion

Используй этот skill перед evidence-backed claim о состоянии работы: "готово", "починил", "тесты проходят", "build успешен", "можно мержить", "задача завершена". Для чистого анализа или статуса без readiness claim этот skill не нужен. Принцип: сначала свежая достаточная проверка, потом claim.

Этот gate закрывает типовой anti-rationalization pattern: нельзя заменять проверку формулировками "изменение маленькое", "должно работать", "я уже видел похожее" или "subagent проверил".

## Gate

Перед success claim выполни:

1. Определи, какая минимальная свежая команда или проверка реально доказывает claim.
2. Запусти ее. Полный прогон нужен для release/shared/high-risk claim или когда narrow check не доказывает заявленное.
3. Прочитай output и exit code.
4. Сопоставь output с claim.
5. Для bug fix проверь prove-it condition: исходный симптом воспроизведен и исчез, либо regression test покрывает именно его.
6. Если output не доказывает claim, сообщи фактический статус и gap.
7. Только после этого формулируй claim с evidence.

## Что считать evidence

- Tests pass: команда тестов завершилась exit 0, output показывает отсутствие failures.
- Build succeeds: build command завершилась exit 0.
- Linter clean: lint command завершилась exit 0 или явно показала 0 errors.
- Bug fixed: исходный симптом воспроизведен и больше не проявляется, либо regression test проверяет именно этот симптом.
- Requirements met: checklist требований сверена с diff, тестами или ручной проверкой.
- Subagent completed: основной агент проверил diff/evidence, а не только поверил отчету subagent.
- External API behavior correct: версия и official source проверены, если claim зависит от внешней библиотеки или сервиса.

## Red Flags

Остановись и проверь, если собираешься написать:

- "должно работать";
- "скорее всего";
- "выглядит готовым";
- "я уверен";
- "тесты должны пройти";
- "subagent сказал, что готово";
- "проверять не обязательно";
- любой аналог success claim без свежего evidence.

## Частичные проверки

Частичная проверка допустима только как частичная:

- "Запустил unit-тесты для X, они прошли; полный suite не запускал."
- "Build не проверял, потому что нет зависимости Y."
- "Проверил lint, но это не доказывает runtime behavior."

Не расширяй claim дальше фактической проверки.

## Skill Changes

Перед claim о готовности изменений в `/home/ant/codex-skills` проверь:

1. `git diff --check`
2. `python3 scripts/audit_skills.py --root /home/ant/codex-skills --strict --require-smoke-coverage` для repo-wide/common-rule changes.
3. `python3 .system/skill-creator/scripts/quick_validate.py <skill-dir>` для узких single-skill edits, если repo-wide audit не запускался.
4. Наличие всех reference-файлов, на которые ссылаются измененные `SKILL.md`.

Если менялись trigger/description, отдельно проверь, что description остается коротким, конкретным и не конфликтует с более высоким уровнем инструкций.

## Когда проверка невозможна

Если проверку нельзя выполнить:

1. Объясни конкретный blocker.
2. Укажи, какая команда должна быть запущена.
3. Не заявляй, что результат проходит.
4. Дай остаточный риск.

## Формат ответа

Перед финальным ответом по завершенной работе включай только то, что нужно для понимания evidence:

1. Команду или метод проверки.
2. Результат: pass/fail/not run.
3. Короткое ограничение, если проверка была частичной.
