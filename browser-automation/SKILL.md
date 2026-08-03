---
name: browser-automation
description: "Разово выполнять браузерные сценарии через Playwright: UI, формы, screenshots, DOM/network evidence; not long-lived UI test code."
---

# Browser Automation

Используй этот skill, когда задача требует реального взаимодействия с браузером: открыть страницу, пройти пользовательский сценарий, проверить визуальный результат, собрать screenshots/traces или локализовать UI-проблему через DOM, console и network evidence.

## Workflow

1. Определи цель браузерного прогона: smoke, repro, visual check, data extraction или диагностика.
2. Найди доступный URL:
   - если dev server уже запущен, используй его;
   - если приложение нужно запустить, используй стандартную команду проекта;
   - если пользователь дал внешний сайт, проверь, что задача не требует авторизации или действий без разрешения.
3. Выбери самый короткий Playwright-сценарий, который дает evidence:
   - `page.goto` с явным `waitUntil`;
   - role/text/test-id selectors вместо хрупких CSS-путей;
   - ожидания по состоянию UI, network response или URL.
4. Сохрани артефакты, когда они помогают доказать результат:
   - screenshot для визуальной проверки;
   - console errors;
   - failed requests;
   - trace/video только для сложного flaky/repro.
5. После прогона объясни результат через наблюдаемые факты, а не через предположение.

## Что покрывает этот skill

- Проверку локальных webapp-изменений через браузер.
- Автоматизацию повторяемых UI-сценариев: login, forms, checkout, onboarding, dashboard flows.
- Диагностику визуальных, DOM, console и network проблем.
- Сбор скриншотов и компактных evidence-логов для bug reports.

## Какие references открывать

Открывай references только если сценарий сложный, нестабилен или нужен Playwright-specific pattern.

- Практики Playwright-сценариев, селекторов и диагностики:
  [references/playwright-patterns.md](references/playwright-patterns.md)
- Verification checklist для browser evidence:
  [references/playwright-verification.md](references/playwright-verification.md)

## Базовые правила

- Не делай браузерную автоматизацию, если достаточно статического чтения кода или обычного unit/API теста.
- Не используй реальные destructive actions на внешних сайтах без явного разрешения.
- Не логируй секреты, cookies, tokens и личные данные.
- Предпочитай детерминированные ожидания вместо `waitForTimeout`.
- Для frontend-реализации дополнительно используй `frontend-engineer`.
- Для добавления долгоживущих автотестов дополнительно используй `autotest-engineer`.

## Формат ответа

Когда выполняешь браузерную проверку, возвращай:

1. Какой URL и сценарий проверены.
2. Какие действия выполнил браузер.
3. Evidence: screenshots, console/network ошибки, assertions.
4. Итог: pass/fail и конкретная причина.
5. Что нужно исправить или проверить дальше.
