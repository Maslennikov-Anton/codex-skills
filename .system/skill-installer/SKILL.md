---
name: skill-installer
description: Устанавливать skills Codex в `$CODEX_HOME/skills` из curated-списка или по пути из GitHub-репозитория. Использовать, когда пользователь просит показать доступные skills, установить skill из curated-набора или установить skill из другого репозитория, включая приватный.
metadata:
  short-description: Установка curated skills из openai/skills и других репозиториев
---

# Установщик skills

Помогает устанавливать skills. По умолчанию они берутся из `https://github.com/openai/skills/tree/main/skills/.curated`, но пользователь также может указать другие источники. Экспериментальные skills находятся в `https://github.com/openai/skills/tree/main/skills/.experimental` и устанавливаются аналогично.

Используй helper scripts в зависимости от задачи:
- Показывай список skills, когда пользователь спрашивает, что доступно, или вызывает этот skill без уточнения действия. По умолчанию выводится `.curated`, но можно передать `--path skills/.experimental`, если спрашивают про экспериментальные skills.
- Устанавливай skill из curated-набора, если пользователь указал имя skill.
- Устанавливай skill из другого репозитория, если пользователь передал GitHub repo/path, включая приватные репозитории.

Устанавливай skills через helper scripts.

## Коммуникация

При выводе списка skills отвечай примерно так, с учетом контекста запроса. Если пользователь спрашивает про экспериментальные skills, показывай список из `.experimental` и явно помечай источник:
"""
Skills из {repo}:
1. skill-1
2. skill-2 (уже установлен)
3. ...
Какие из них установить?
"""

После установки skill сообщай пользователю: "Перезапустите Codex, чтобы он подхватил новые skills."

## Скрипты

Все эти скрипты используют сеть, поэтому при запуске в песочнице запрашивай escalation.

- `scripts/list-skills.py` (печатает список skills с пометками об установке)
- `scripts/list-skills.py --format json`
- Пример для экспериментального списка: `scripts/list-skills.py --path skills/.experimental`
- `scripts/install-skill-from-github.py --repo <owner>/<repo> --path <path/to/skill> [<path/to/skill> ...]`
- `scripts/install-skill-from-github.py --url https://github.com/<owner>/<repo>/tree/<ref>/<path>`
- Пример для экспериментального skill: `scripts/install-skill-from-github.py --repo openai/skills --path skills/.experimental/<skill-name>`

## Поведение и опции

- По умолчанию используется прямое скачивание для публичных GitHub-репозиториев.
- Если скачивание падает из-за auth/permission ошибок, используется fallback на `git sparse checkout`.
- Установка прерывается, если целевая директория skill уже существует.
- Skills устанавливаются в `$CODEX_HOME/skills/<skill-name>` (по умолчанию `~/.codex/skills`).
- Несколько значений `--path` позволяют установить несколько skills за один запуск; имя каждого берется из basename пути, если явно не задан `--name`.
- Поддерживаются опции: `--ref <ref>` (по умолчанию `main`), `--dest <path>`, `--method auto|download|git`.

## Примечания

- Curated-список запрашивается из `https://github.com/openai/skills/tree/main/skills/.curated` через GitHub API. Если источник недоступен, объясни ошибку и заверши работу.
- Приватные GitHub-репозитории можно читать через существующие git credentials или через `GITHUB_TOKEN`/`GH_TOKEN` для режима download.
- Git fallback сначала пробует HTTPS, затем SSH.
- Skills из `https://github.com/openai/skills/tree/main/skills/.system` уже предустановлены, поэтому обычно не нужно помогать пользователям устанавливать их. Если пользователь спрашивает, просто объясни это. Если он настаивает, можно скачать и перезаписать.
- Информация о том, установлен ли skill, берется из `$CODEX_HOME/skills`.
