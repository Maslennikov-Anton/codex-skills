---
name: skill-installer
description: Устанавливать Codex skills в `$CODEX_HOME/skills` из curated-списка или по пути в GitHub-репозитории. Использовать, когда пользователь просит показать доступные skill-ы, установить skill из curated-списка или поставить skill из другого репозитория, включая private repo.
metadata:
  short-description: Установка curated skill-ов из openai/skills и других репозиториев
---

# Установка Skill-ов

Помогает устанавливать skill-ы. По умолчанию речь идет о https://github.com/openai/skills/tree/main/skills/.curated, но пользователь может указать и другие источники. Экспериментальные skill-ы лежат в https://github.com/openai/skills/tree/main/skills/.experimental и ставятся аналогично.

Используй helper scripts в зависимости от задачи:
- Показывай список skill-ов, когда пользователь спрашивает, что доступно, или вызывает этот skill без конкретного действия. По умолчанию показывай `.curated`, а для экспериментальных skill-ов используй `--path skills/.experimental`.
- Устанавливай из curated-списка, когда пользователь дал имя skill-а.
- Устанавливай из другого репозитория, когда пользователь передал путь или repo в GitHub, включая private repo.

Устанавливай skill-ы через helper scripts.

## Коммуникация

Когда показываешь список skill-ов, форматируй ответ примерно так. Если пользователь спрашивает про экспериментальные skill-ы, показывай `.experimental` вместо `.curated` и явно помечай источник:
"""
Skills из {repo}:
1. skill-1
2. skill-2 (уже установлен)
3. ...
Какие из них установить?
"""

После установки skill-а сообщай пользователю: "Перезапусти Codex, чтобы он подхватил новые skill-ы."

## Скрипты

Все эти скрипты используют сеть, поэтому при запуске в sandbox запрашивай escalation.

- `scripts/list-skills.py` (prints skills list with installed annotations)
- `scripts/list-skills.py --format json`
- Example (experimental list): `scripts/list-skills.py --path skills/.experimental`
- `scripts/install-skill-from-github.py --repo <owner>/<repo> --path <path/to/skill> [<path/to/skill> ...]`
- `scripts/install-skill-from-github.py --url https://github.com/<owner>/<repo>/tree/<ref>/<path>`
- Example (experimental skill): `scripts/install-skill-from-github.py --repo openai/skills --path skills/.experimental/<skill-name>`

## Поведение и опции

- Для публичных GitHub repo по умолчанию использует прямую загрузку.
- Если загрузка падает из-за auth/permission errors, переключается на git sparse checkout.
- Прерывается, если целевая директория skill-а уже существует.
- Устанавливает в `$CODEX_HOME/skills/<skill-name>`; по умолчанию это `~/.codex/skills`.
- Несколько значений `--path` позволяют установить несколько skill-ов за один запуск; имя берется из basename пути, если не передан `--name`.
- Опции: `--ref <ref>` (по умолчанию `main`), `--dest <path>`, `--method auto|download|git`.

## Заметки

- Curated-список подтягивается через GitHub API из `https://github.com/openai/skills/tree/main/skills/.curated`. Если он недоступен, объясни ошибку и остановись.
- Для private GitHub repo можно использовать существующие git credentials или опциональные `GITHUB_TOKEN`/`GH_TOKEN`.
- Git fallback сначала пробует HTTPS, затем SSH.
- Skill-ы из https://github.com/openai/skills/tree/main/skills/.system уже предустановлены, поэтому обычно не нужно помогать пользователю ставить их отдельно. Если пользователь настаивает, можно скачать и перезаписать.
- Пометки об уже установленных skill-ах берутся из `$CODEX_HOME/skills`.
