# Implementation Practices

Используй этот reference для прикладных frontend-решений и implementation-first работы.

## Практики реализации

- Держи компонентную границу понятной: presentation отдельно от data/loading orchestration там, где это упрощает код.
- Предпочитай явные props, состояния и data flow скрытой магии.
- Локализуй side effects и не размазывай их по компонентному дереву без необходимости.
- Для сетевых и async сценариев делай очевидными retry, cancellation и stale-state поведение, если это важно для UX.

## Перед завершением

- Проверь, что компонент можно читать без знания скрытого контекста.
- Проверь, что API integration path не смешивает transport errors и domain states.
- Проверь, что изменение не ломает established design system и naming проекта.
