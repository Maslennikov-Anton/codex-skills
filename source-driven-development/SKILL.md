---
name: source-driven-development
description: "Опирайтесь на официальные источники при работе с framework/library/API: версии, документация, breaking changes, устаревшие паттерны и citations."
---

# Source-Driven Development

Используй этот skill, когда реализация зависит от внешнего API, библиотеки, фреймворка, протокола, CLI, облачного сервиса или продукта, где память модели может быть устаревшей.

## Workflow

1. Определи stack и версии:
   - lockfile, package metadata, pyproject, build files, Docker image, CLI version;
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

## Формат ответа

Когда source evidence важно для решения, возвращай:

1. Версия или статус версии.
2. Официальный источник.
3. Какой documented pattern выбран.
4. Что осталось непроверенным, если источник недоступен.
