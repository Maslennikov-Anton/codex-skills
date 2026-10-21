# Источники review methods

Локальные references — измененные адаптации, 2026-10-21:

- `test-gap-audit.md`: [GitHub Awesome Copilot](https://github.com/github/awesome-copilot/blob/613efc8c21d9b3ce642dff361d17006cd9967e28/skills/test-gap-audit/SKILL.md), commit `613efc8c21d9b3ce642dff361d17006cd9967e28`, MIT. Полный copyright/license: `../licenses/awesome-copilot-MIT.txt`. Сокращены report boilerplate и repo-wide traversal; сохранены public behavior, actual assertions и границы подтвержденного gap.
- `silent-failures.md`: [Anthropic PR Review Toolkit, Silent Failure Hunter](https://github.com/anthropics/claude-plugins-official/blob/d1adba47161a271799de7b548225d929310046bd/plugins/pr-review-toolkit/agents/silent-failure-hunter.md), commit `d1adba47161a271799de7b548225d929310046bd`, Apache-2.0. Лицензия конкретного plugin: `../licenses/pr-review-toolkit-Apache-2.0.txt`. Убраны чужие logging/error ID conventions, безусловный critical для broad catch, обязательные UI alerts и запуск отдельного агента. Сохранены проверка lost error signal, retry exhaustion и ложного успеха.

Это экспериментальные расширения существующего review, не два новых обязательных workflow. Severity и разрешения задаются текущей задачей и основным SKILL.md.
