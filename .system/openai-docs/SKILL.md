---
name: "openai-docs"
description: "Использовать, когда пользователь спрашивает, как работать с продуктами или API OpenAI, и нужна актуальная официальная документация с цитатами, помощь в выборе текущей модели под задачу или явное guidance по обновлению до GPT-5.4 и адаптации prompt-ов; по возможности использовать OpenAI docs MCP tools, reference-файлы считать только вспомогательным контекстом, а fallback-поиск ограничивать официальными доменами OpenAI."
---


# Документация OpenAI

Давай авторитетные и актуальные рекомендации по официальной документации OpenAI. Если в окружении доступны OpenAI docs MCP tools, используй их в первую очередь. Если они недоступны или не дают содержательного результата, используй точечный web-поиск только по официальным доменам OpenAI. Этот skill может дополнительно подключать нужные файлы из `references/` для выбора модели и запросов про GPT-5.4, но источником истины всегда остается актуальная документация OpenAI.

## Быстрый старт

- Если доступны OpenAI docs MCP tools, используй `mcp__openaiDeveloperDocs__search_openai_docs`, чтобы найти наиболее релевантные страницы.
- Если доступны OpenAI docs MCP tools, используй `mcp__openaiDeveloperDocs__fetch_openai_doc`, чтобы получить точные разделы и аккуратно цитировать или пересказывать их.
- `mcp__openaiDeveloperDocs__list_openai_docs` используй только тогда, когда нужно просмотреть структуру документации без точного поискового запроса.
- Если MCP tools недоступны, используй точечный web-поиск по `developers.openai.com` и `platform.openai.com`.
- Загружай только тот файл из `references/`, который реально нужен для вопроса о выборе модели или обновлении до GPT-5.4.

## OpenAI product snapshots

1. Apps SDK: Build ChatGPT apps by providing a web component UI and an MCP server that exposes your app's tools to ChatGPT.
2. Responses API: A unified endpoint designed for stateful, multimodal, tool-using interactions in agentic workflows.
3. Chat Completions API: Generate a model response from a list of messages comprising a conversation.
4. Codex: OpenAI's coding agent for software development that can write, understand, review, and debug code.
5. gpt-oss: Open-weight OpenAI reasoning models (gpt-oss-120b and gpt-oss-20b) released under the Apache 2.0 license.
6. Realtime API: Build low-latency, multimodal experiences including natural speech-to-speech conversations.
7. Agents SDK: A toolkit for building agentic apps where a model can use tools and context, hand off to other agents, stream partial results, and keep a full trace.

## Доступность инструментов

Выбирай первую подходящую ветку:

1. Если OpenAI docs MCP tools доступны, используй их первыми.
2. Если MCP tools недоступны в текущем окружении, сразу переходи к ограниченному web-поиску по официальным доменам OpenAI.
3. Если MCP tools должны быть доступны, но выглядят сломанными, сначала ответь через официальный web-поиск, а уже потом рассматривай восстановление MCP-настройки.

Если явная задача состоит в установке или починке MCP-сервера:

1. Выполни `codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp`.
2. Если команда падает из-за permissions или sandboxing, повтори с escalated permissions и коротким justification.
3. Только если это тоже не сработало, попроси пользователя запустить команду самостоятельно.
4. Попроси пользователя перезапустить Codex.

## Workflow

1. Уточни, о каком продукте идет речь и нужен ли общий lookup по документации, выбор модели, обновление до GPT-5.4 или адаптация prompt-ов под GPT-5.4.
2. Если это запрос на выбор модели, загрузи `references/latest-model.md`.
3. Если это явный запрос на обновление до GPT-5.4, загрузи `references/upgrading-to-gpt-5p4.md`.
4. Если обновление может потребовать изменений prompt-а или workflow research-heavy, tool-heavy, coding-oriented, multi-agent либо long-running, дополнительно загрузи `references/gpt-5p4-prompting-guide.md`.
5. Получи актуальные docs из лучшего доступного источника:
   - через MCP fetch, если MCP tools доступны;
   - иначе через ограниченный web-поиск и прямое чтение страниц на официальных доменах OpenAI.
6. Читай только тот раздел, который реально нужен для ответа.
7. Для ревью обновления до GPT-5.4 всегда делай явный вывод по каждому usage site: target model, starting reasoning recommendation, `phase` assessment при необходимости, prompt blocks и compatibility status.
8. Отвечай кратко и со ссылкой на источник, используя reference-файлы только как вспомогательный контекст.

## Карта reference-файлов

Читай только то, что реально нужно:

- `references/latest-model.md` -> вопросы про выбор модели и "best/latest/current model"; каждую рекомендацию перед ответом сверяй с актуальными OpenAI docs.
- `references/upgrading-to-gpt-5p4.md` -> только для явных запросов на обновление до GPT-5.4 и planning такого обновления; checklist и compatibility guidance обязательно сверяй с актуальными OpenAI docs.
- `references/gpt-5p4-prompting-guide.md` -> для переписывания prompt-ов и изменения prompt-behavior под GPT-5.4; guidance по prompt-ам тоже перепроверяй по актуальным OpenAI docs.

## Правила качества

- Считай OpenAI docs источником истины и не спекулируй там, где подтверждения нет.
- Держи цитаты короткими и в рамках policy; по умолчанию предпочитай пересказ с цитированием.
- Если несколько страниц расходятся, явно укажи различие и процитируй обе.
- Reference-файлы здесь только как convenience-guides; для volatile guidance вроде рекомендуемых моделей, upgrade-инструкций и prompting-advice всегда побеждают текущие OpenAI docs.
- Если docs не покрывают потребность пользователя, прямо скажи об этом и предложи следующий шаг.

## Заметки по инструментам

- Предпочитай MCP doc tools, когда они реально доступны в окружении.
- Не блокируй обычный docs-вопрос из-за отсутствия MCP, если доступны официальные web-источники.
- При использовании web-поиска ограничивайся официальными доменами OpenAI (`developers.openai.com`, `platform.openai.com`) и обязательно цитируй источники.
- Считай bundled `references/` только вспомогательным контекстом; volatile guidance перед ответом перепроверяй по живой официальной документации.
