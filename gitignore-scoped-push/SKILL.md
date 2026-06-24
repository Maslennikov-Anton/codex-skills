---
name: gitignore-scoped-push
description: "Use when user asks to commit/push/sync a repo according to .gitignore: stage explicit tracked allowlist, exclude ignored artifacts, verify remote SHA."
---

# Gitignore-Scoped Push

Используй этот skill, когда пользователь просит `запушить согласно гитигнору`, `push according to .gitignore`, `синкани изменения` с commit/push смыслом, или когда repo publish происходит рядом с generated/test artifacts.

## Workflow

1. Подтверди repo и target:
   - `git rev-parse --show-toplevel`
   - `git branch --show-current`
   - `git remote -v`
2. Сними полный статус:
   - `git status --short --ignored`
   - отдельно прочитай `.gitignore`, если ignored artifacts видны впервые или выглядят нестандартно.
3. Определи commit scope:
   - stage только явный allowlist проектных путей: docs, src, tests, config, scripts, fixtures, package metadata;
   - не используй `git add -A` без pathspec в шумном repo;
   - не используй `git add -f` для ignored outputs, если пользователь явно не попросил включить артефакт.
4. Проверь staged scope:
   - `git diff --cached --name-status`
   - `git diff --cached --check`
   - фильтр имен staged files против `.venv`, `.work`, `allure-results`, `junit*.xml`, `__pycache__`, caches, reports, temporary exit-code files.
5. Запусти самый короткий релевантный gate перед commit:
   - lint/contract/unit smoke из project docs;
   - если runtime tests ожидаемо красные и CI собирает JUnit/Allure, зафиксируй это как ограничение, но не переписывай scope ради зеленого статуса.
6. Commit:
   - message описывает результат, не процесс;
   - после commit проверь, что tracked worktree чистый или остались только осознанные unstaged changes.
7. Push:
   - `git push <remote> <branch>`;
   - проверь `git ls-remote <remote> refs/heads/<branch>` или эквивалент, что remote SHA совпадает с `HEAD`.

## Guardrails

- Ignored artifacts остаются локально. Не удаляй `.venv`, `.work`, JUnit, Allure, caches или generated reports, если пользователь не просил cleanup отдельно.
- Если staging падает из-за `.git/index.lock` или sandbox read-only, повтори тот же явный allowlist с нужной эскалацией; не расширяй scope.
- Если push завис или дал transient SSH/network timeout, сначала retry того же commit/scope. Не меняй commit и не включай новые файлы из-за сетевого сбоя.
- Если repo уже содержит чужие staged/unstaged изменения, не откатывай их. Либо включи их только если они входят в текущий пользовательский scope, либо остановись и явно назови конфликт.
- Для GitLab remote используй обычный `git`/`glab`; не маршрутизируй через GitHub skills.

## Report

В финальном ответе укажи:

- commit SHA и message;
- remote/branch и результат push;
- какие verification команды прошли;
- что осталось локально ignored или unstaged;
- если pipeline monitoring не просили, прямо скажи, что pipeline не отслеживался.
