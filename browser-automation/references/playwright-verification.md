# Playwright Verification Checklist

Используй, когда browser run должен доказать состояние webapp, а не просто открыть страницу.

## Evidence

- Screenshot после ключевого состояния UI.
- Console errors/warnings, если они относятся к проверяемому сценарию.
- Failed network requests: URL, method, status/error.
- Visible assertions: текст, role, URL, enabled/disabled state, count.
- Для responsive UI проверь минимум desktop и mobile viewport, если задача затрагивает layout.

## Minimal Harness

- Подписывайся на `page.on("console")` и `page.on("requestfailed")` до `goto`.
- Используй role/text/test-id selectors вместо хрупких CSS путей.
- Жди состояние через locator assertions или network/url condition, не через fixed timeout.
- Сохраняй screenshot с именем, отражающим сценарий и viewport.

## Reporting

В ответе укажи:

- URL и viewport.
- Проверенные действия.
- Assertions или observed state.
- Console/network problems.
- Screenshot path, если он сохранен.
