---
name: source-driven-development
description: "Use when a decision depends on exact current version, official docs, deprecations, external API behavior, security defaults, or citations; skip local-only code."
---

# Source-Driven Development

Используй этот skill, когда решение зависит от точной текущей версии внешнего API, библиотеки, фреймворка, протокола, CLI, облачного сервиса или продукта. Если поведение полностью определяется локальным кодом/lockfile и version-specific claim не нужен, не запускай полный source-doc pass.

## Workflow

1. Определи stack и версии:
   - lockfile, package metadata, pyproject, build files, Docker image, CLI version;
   - для Python/JS/Playwright/GitHub/OpenAI/Allure сначала проверь локально установленную версию, lockfile или официальный CLI output;
   - если версия не видна локально, явно зафиксируй unknown и не делай version-specific claim.
2. Найди authoritative source:
   - official docs, release notes, migration guide, API reference, standards document;
   - для OpenAI-продуктов используй `openai-docs`;
   - для кода проекта сначала используй локальный repo, затем внешние источники.
3. Сверь решение с текущей версией:
   - supported API;
   - deprecations/breaking changes;
   - required config/env;
   - documented error handling и security notes.
4. Реализуй минимально по documented pattern, без “примерно помню”.
5. В финальном ответе или design note укажи, какие источники определили решение, если это важно для последующего сопровождения.

## Red Flags

- “В React/FastAPI/Playwright обычно так” без проверки версии.
- Код использует API, которого нет в lockfile/current docs.
- Решение берется из старого blog post вместо официального migration guide.
- Breaking change предполагается на память.
- Security/config default выбран без документации.
- Python/JS/Playwright/GitHub/OpenAI/Allure API меняется или диагностируется без проверки текущей версии или official docs.

## Формат ответа

Когда source evidence важно для решения, возвращай:

1. Версия или статус версии.
2. Официальный источник.
3. Какой documented pattern выбран.
4. Что осталось непроверенным, если источник недоступен.
