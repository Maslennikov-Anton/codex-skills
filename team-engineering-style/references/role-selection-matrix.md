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
| Нужно написать или изменить Python-код | `python-developer` | `database-engineer` для data-layer; `code-review-professional` для сильного review |
| Нужно разработать frontend | `frontend-engineer` | `product-designer` для сильного UX-фокуса; `autotest-engineer` для UI automation |
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
| Нужно проанализировать метрики, воронку или влияние фичи | `data-analyst` | `product-manager`, если по результатам нужно принять продуктовое решение |
| Нужно написать README, runbook, guide или release notes | `technical-writer` | профильный skill по содержанию документа |
| Нужно обновить локальные стандарты, skills или ввести новый стек | `team-engineering-style` | профильный skill той области, которую меняем |

## Как отличать похожие роли

### `analyst` vs `product-manager`

- `analyst` нужен, когда требуется понять, описать и структурировать требования.
- `product-manager` нужен, когда требуется выбрать, что делать в первую очередь и какую ценность это даст.

### `solution-architect` vs `python-developer`

- `solution-architect` отвечает за высокоуровневую схему и границы решения.
- `python-developer` отвечает за реализацию конкретного кода и модулей.

### `devops-engineer` vs `platform-engineer`

- `devops-engineer` нужен для CI/CD, инфраструктуры и надежности конкретных систем.
- `platform-engineer` нужен, когда строится внутренняя платформа и reusable capabilities для многих команд.

### `manual-tester` vs `autotest-engineer`

- `manual-tester` нужен для ручной проверки, exploratory, smoke, UAT и bug reports.
- `autotest-engineer` нужен для автоматизации, CI и тестовой архитектуры.

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

## Антипаттерны выбора

- Не зови `product-manager`, если задача уже сугубо про реализацию конкретного модуля без продуктового выбора.
- Не зови `solution-architect`, если нужно просто написать локальную функцию без архитектурных последствий.
- Не заменяй `manual-tester` автотестами там, где сначала нужно проверить саму идею сценария.
- Не заменяй `support-engineer` обычной разработкой, если сначала непонятно, где именно проблема и как она проявляется у пользователя.
- Не тащи слишком много ролей в одну задачу: если достаточно двух skills, третий уже должен быть явно обоснован.
