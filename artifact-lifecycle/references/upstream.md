# Research and local adaptation

Проверено 2026-10-21. Локальный helper написан с нуля; upstream code/installer не запускались и не копировались.

- [tyroneross/build-loop: repo-maintenance](https://github.com/tyroneross/build-loop/blob/671125595f510b614e8ed68e46671e46e30bfe4e/skills/repo-maintenance/SKILL.md): полезны inventory, ownership, active-process checks и retention. Stale ignored candidate не доказывает воспроизводимость. Локально сужено до owned scratch вне проектов; branch/source reconciliation не импортируется.
- [openai/openai-agents-python: runtime-behavior-probe](https://github.com/openai/openai-agents-python/blob/3e0e89374f629c974929054e56e823a43c91a013/.agents/skills/runtime-behavior-probe/SKILL.md): полезно сохранять краткий run summary и evidence до удаления one-off probe files. Специфические approval gates и OpenAI API workflow не импортируются.
- [Workflow Janitor](https://github.com/PrantoSMSS/workflow-janitor): найден в веб-индексе, но GitHub API при проверке вернул 404. Не установлен из недоступного upstream. В индексированной версии слишком широки targets (tool history/state), а quarantine без удаления сама накапливает мусор.

Это адаптация идей lifecycle, а не установка полного чужого workflow. Встроенной очистки всего диска нет.
