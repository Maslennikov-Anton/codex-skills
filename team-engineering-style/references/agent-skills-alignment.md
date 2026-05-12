# Alignment с addyosmani/agent-skills

## Статус источника

`https://github.com/addyosmani/agent-skills` принят как достоверный внешний baseline для agentic engineering practices. Используй его как ориентир по lifecycle, gates и anti-rationalization patterns, но не как замену локальным правилам команды.

Локальная база skills остается source of truth для Ant workspace. Если upstream-практика конфликтует с системными инструкциями, локальными VCont/HSB правилами или sandbox constraints, применяй более строгий локальный вариант.

## Mapping

| Upstream skill | Локальный skill |
| --- | --- |
| `idea-refine`, `spec-driven-development` | `analyst`, `product-manager`, `solution-architect` |
| `planning-and-task-breakdown` | `implementation-planner` |
| `incremental-implementation` | `executing-implementation-plans`, профильный engineering skill |
| `test-driven-development` | `autotest-engineer`, профильный engineering skill |
| `source-driven-development` | `source-driven-development` |
| `doubt-driven-development` | `doubt-driven-development`, `code-review-professional` |
| `debugging-and-error-recovery` | `systematic-debugging`, `support-engineer` |
| `code-review-and-quality` | `code-review-professional` |
| `code-simplification` | профильный engineering skill + `code-review-professional` |
| `browser-testing-with-devtools` | `browser-automation`, `frontend-engineer`, `autotest-engineer` |
| `frontend-ui-engineering` | `frontend-engineer`, `product-designer`, `browser-automation` |
| `api-and-interface-design` | `solution-architect`, `python-developer`, `database-engineer` |
| `security-and-hardening` | `security-engineer` |
| `performance-optimization` | профильный engineering skill, `devops-engineer`, `database-engineer` |
| `ci-cd-and-automation` | `devops-engineer`, GitHub/GitLab skills |
| `deprecation-and-migration` | `solution-architect`, `database-engineer`, `delivery-manager` |
| `documentation-and-adrs` | `technical-writer`, `architecture-decision-records` |
| `shipping-and-launch` | `delivery-manager`, `devops-engineer`, `verification-before-completion` |
| `context-engineering` | `context-hygiene`, `para-memory-files` |
| `git-workflow-and-versioning` | GitHub/GitLab skills, `verification-before-completion` |

## Что заимствуем как стандарт

- Lifecycle gates: refine/spec -> plan -> tasks -> implement -> test -> review -> verify -> ship.
- Source-driven rule: для внешних API, версий библиотек и framework behavior сначала определить текущую версию и официальный источник.
- Doubt-driven rule: high-risk claim должен пройти adversarial/fresh review до того, как станет основанием для изменения.
- Incremental implementation: маленькие завершенные slices с локальной проверкой, а не большой diff без checkpoints.
- Prove-it pattern: баг считается исправленным только после воспроизведения симптома или regression coverage.
- Five-axis review: correctness, simplicity/readability, architecture, security, performance.
- Anti-rationalization checks: “потом допишем тесты”, “и так понятно”, “это маленькое изменение”, “документация не нужна”, “проверять не обязательно” считаются red flags.

## Что не переносим напрямую

- Slash-command naming и англоязычный UX как обязательный формат.
- Инструкции, завязанные на конкретный агентский runtime, если они конфликтуют с текущими tool/sandbox правилами.
- Массовое создание новых skills при наличии локального более узкого аналога.
- Большие manual-разделы в `SKILL.md`; редкие детали должны идти в `references/`.

## Правило обновления

При следующем изменении любого lifecycle skill проверяй, не нужно ли добавить в него один из upstream-gates: source evidence, doubt review, incremental slice, prove-it test, five-axis review или final verification.
