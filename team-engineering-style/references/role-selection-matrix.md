# Матрица выбора ролей

Этот файл помогает быстро понять, какой skill использовать под конкретную задачу. Выбирай самый узкий подходящий skill. Если задача пересекает несколько зон ответственности, комбинируй 2-3 skill'а, но не больше без явной необходимости.

## Базовый принцип выбора

1. Сначала определи, чего от задачи хотят на выходе: решение, код, тест, план, анализ, документ или расследование.
2. Затем выбери главный skill по типу результата.
3. После этого при необходимости добавь один смежный skill для второй важной стороны задачи: архитектура, безопасность, тестирование, доставка или документация.

## Быстрый выбор по ситуации

| Ситуация | Основной skill | Когда добавить второй skill |
| --- | --- | --- |
| Нужно понять требования, рамки решения, критерии приемки | `analyst` | `product-manager`, если нужно принять продуктовый приоритет или scope MVP |
| Нужно решить, что делать в продукте, что брать в MVP и как приоритизировать backlog | `product-manager` | `data-analyst`, если решение должно опираться на метрики; `analyst`, если нужно глубже формализовать требования |
| Нужно спроектировать архитектуру, интеграции и технические компромиссы | `solution-architect` | `security-engineer` для security-sensitive решений; `database-engineer` для выраженного DB-фокуса |
| Нужно подготовить исполнимый план реализации перед кодом | `implementation-planner` | `solution-architect`, если нужно сначала выбрать архитектуру; `subagent-driven-development`, если план будут выполнять агенты |
| Нужно выполнить уже написанный implementation plan | `executing-implementation-plans` | `subagent-driven-development`, если tasks независимы; `verification-before-completion` для финального claim |
| Нужно принять решение по внешнему API, framework/library behavior или версии инструмента | `source-driven-development` | профильный engineering skill для реализации; `security-engineer`, если источник влияет на security default |
| Нужно проверить рискованный claim, irreversible change, migration или спорное решение | `doubt-driven-development` | `code-review-professional` для diff review; `source-driven-development`, если риск связан с внешним API |
| Нужно написать или изменить Python-код | `python-developer` | `database-engineer` для data-layer; `code-review-professional` для сильного review |
| Нужно выполнить сложную реализацию через независимые subtasks или agent workflow | `subagent-driven-development` | профильные engineering skills по областям задач; `code-review-professional` для финального review |
| Нужно разработать frontend | `frontend-engineer` | `product-designer` для сильного UX-фокуса; `autotest-engineer` для UI automation |
| Нужно проверить web-сценарий в браузере, собрать screenshot, DOM или network evidence | `browser-automation` | `frontend-engineer`, если нужно сразу исправлять UI; `autotest-engineer`, если проверку нужно превратить в долгоживущий тест |
| Нужно спроектировать UX, user flow или визуальную концепцию | `product-designer` | `frontend-engineer`, если сразу нужна реализация |
| Нужно сделать мобильный экран, поток или архитектуру клиента | `mobile-engineer` | `product-designer` для UX; `autotest-engineer` для mobile test strategy |
| Нужно проработать схему БД, миграцию, индексы или SQL-производительность | `database-engineer` | `python-developer`, если дальше нужно реализовать data-access слой |
| Нужно провести security review или threat modeling | `security-engineer` | `solution-architect` для архитектурной части; `devops-engineer` для инфраструктурной |
| Нужно настроить CI/CD, деплой или observability | `devops-engineer` | `platform-engineer`, если задача уже про внутреннюю платформу, а не один проект |
| Нужно развивать внутреннюю платформу и developer experience | `platform-engineer` | `devops-engineer`, если есть сильный operational/infrastructure слой |
| Нужно написать автотесты или стабилизировать тестовый контур | `autotest-engineer` | `manual-tester`, если сначала нужен ручной test design; `code-review-professional`, если нужен review тестового решения |
| Нужно подготовить checklist, test cases или вручную проверить поведение | `manual-tester` | `autotest-engineer`, если сценарии затем нужно автоматизировать |
| Нужно провести профессиональное ревью изменений | `code-review-professional` | `security-engineer`, если ревью security-sensitive; `database-engineer`, если изменение тяжелое по DB |
| Нужно спланировать поставку, зависимости и readiness релиза | `delivery-manager` | `product-manager` для приоритетов; `devops-engineer` для release/infra readiness |
| Нужно локализовать инцидент, воспроизвести проблему или подготовить эскалацию | `support-engineer` | `manual-tester` для формального bug report; `devops-engineer` для operational incidents |
| Нужно продолжить длинную задачу, подготовить handoff или сжать историю после compaction | `context-hygiene` | `para-memory-files`, если знание нужно сохранить между сессиями; профильный skill текущей задачи |
| Нужно проанализировать метрики, воронку или влияние фичи | `data-analyst` | `product-manager`, если по результатам нужно принять продуктовое решение |
| Нужно написать README, runbook, guide или release notes | `technical-writer` | профильный skill по содержанию документа |
| Нужно обновить локальные стандарты, skills или ввести новый стек | `team-engineering-style` | профильный skill той области, которую меняем |

## Инструментальные и доменные skills

| Ситуация | Основной skill | Когда добавить второй skill |
| --- | --- | --- |
| Нужно создать или изменить Paperclip agent adapter | `create-agent-adapter` | `security-engineer` для secrets/sandboxing; `frontend-engineer`, если меняется UI config |
| Нужно делегировать работу нескольким subagents | `subagent-driven-development` | `context-hygiene`, если задача длинная; `team-engineering-style`, если меняется сам workflow |
| Нужно подтвердить "готово", "починено", "тесты проходят", build/lint success, commit, push или PR | `verification-before-completion` | профильный skill текущей задачи, чтобы выбрать правильную проверку |
| Нужно обработать review feedback, requested changes или inline comments | `receiving-code-review` | `code-review-professional`, если нужно независимо оценить спорный feedback; GitHub/GitLab skill для thread-level replies |
| Нужно работать с файловой PARA-памятью, daily notes или recall | `para-memory-files` | `context-hygiene`, если сначала нужно сжать длинную сессию |
| Нужно работать с Allure TestOps | `allure-testops-operations` | `autotest-engineer`, если задача связана с test results и reporting strategy |
| Нужно работать с GitLab issues, MRs, pipelines или releases | `gitlab-operations` | `devops-engineer` для CI/CD incidents; `code-review-professional` для MR review |
| Нужно работать с Yandex Tracker | `yandex-tracker-operations` | `analyst` для требований; `delivery-manager` для release coordination |
| Нужно работать с VCont runtime, bootfile, Modbus или HSB | `vcont` | `autotest-engineer`, если нужна автоматизация проверки; `systematic-debugging` для расследования сбоя |

## Как отличать похожие роли

### `analyst` vs `product-manager`

- `analyst` нужен, когда требуется понять, описать и структурировать требования.
- `product-manager` нужен, когда требуется выбрать, что делать в первую очередь и какую ценность это даст.
- `implementation-planner` нужен после требований/дизайна, когда надо разложить реализацию на exact files, steps и verification commands.
- `executing-implementation-plans` нужен после появления written plan, когда надо строго выполнить steps и checkpoints.

### `solution-architect` vs `python-developer`

- `solution-architect` отвечает за высокоуровневую схему и границы решения.
- `python-developer` отвечает за реализацию конкретного кода и модулей.
- `subagent-driven-development` не заменяет инженерный skill: он организует делегирование, ownership, review gates и интеграцию, а профильный skill определяет качество работы в своей области.

### `devops-engineer` vs `platform-engineer`

- `devops-engineer` нужен для CI/CD, инфраструктуры и надежности конкретных систем.
- `platform-engineer` нужен, когда строится внутренняя платформа и reusable capabilities для многих команд.

### `manual-tester` vs `autotest-engineer`

- `manual-tester` нужен для ручной проверки, exploratory, smoke, UAT и bug reports.
- `autotest-engineer` нужен для автоматизации, CI и тестовой архитектуры.
- `browser-automation` нужен для фактического браузерного evidence прямо сейчас; если сценарий должен жить в test suite, добавляй `autotest-engineer`.

### `support-engineer` vs `manual-tester`

- `support-engineer` работает от инцидента, пользовательской проблемы и эксплуатационного сигнала.
- `manual-tester` работает от сценарного тест-дизайна и формальной проверки поведения.

### `database-engineer` vs `solution-architect`

- `database-engineer` углубляется в схему БД, миграции, ограничения и SQL.
- `solution-architect` решает общую архитектуру системы и границы между ее частями.

## Рекомендуемые связки

- Новая feature: `product-manager` + `analyst` + `solution-architect` + `python-developer` + `autotest-engineer` + `code-review-professional`
- Сложная DB-задача: `solution-architect` + `database-engineer` + `python-developer` + `autotest-engineer`
- Подготовка релиза: `delivery-manager` + `devops-engineer` + `manual-tester` + `code-review-professional`
- Инцидент в эксплуатации: `support-engineer` + `devops-engineer` + профильный инженерный skill
- Изменение стандартов команды: `team-engineering-style` + профильный skill по области изменения
- Длинная агентская задача: `context-hygiene` + профильный skill + при необходимости `para-memory-files`
- Большая реализация с независимыми частями: `subagent-driven-development` + профильные engineering skills + `code-review-professional`
- Завершение реализации: профильный engineering skill + `verification-before-completion`
- Работа с review comments: `receiving-code-review` + профильный engineering skill + `verification-before-completion`
- Рискованное изменение внешней интеграции: `source-driven-development` + `doubt-driven-development` + профильный engineering skill

## Антипаттерны выбора

- Не зови `product-manager`, если задача уже сугубо про реализацию конкретного модуля без продуктового выбора.
- Не зови `solution-architect`, если нужно просто написать локальную функцию без архитектурных последствий.
- Не заменяй `manual-tester` автотестами там, где сначала нужно проверить саму идею сценария.
- Не заменяй `support-engineer` обычной разработкой, если сначала непонятно, где именно проблема и как она проявляется у пользователя.
- Не тащи слишком много ролей в одну задачу: если достаточно двух skills, третий уже должен быть явно обоснован.
- Не заменяй `source-driven-development` поиском по памяти модели, если задача зависит от актуальной версии внешнего API.
- Не заменяй `doubt-driven-development` обычным финальным review, если сначала нужно проверить сам claim или план до изменения кода.
