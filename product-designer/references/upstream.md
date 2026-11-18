# Источники и локальная адаптация

Проверено 2026-11-18 по исходным репозиториям и закреплённым commits. Это единая локальная редакция UI/UX-инструкций с адаптацией приёмов; полные upstream skills, их базы, код, assets, hooks и installers не устанавливались. Методы пересекаются: указание источника ниже показывает, какой акцент использован, а не утверждает, что у остальных этого нет.

| Источник и версия | Что использовано локально |
|---|---|
| [Paul Bakaus — Impeccable](https://github.com/pbakaus/impeccable/blob/d41d9860b0094dcb68030657da63461212835aaa/.claude/skills/impeccable/SKILL.md), `d41d9860b0094dcb68030657da63461212835aaa` | Различение назначения поверхности; сохранение идентичности при доводке; просмотр рендера; согласованность типографики, сетки и состояний; исправления пакетами |
| [Anthropic — Frontend Design](https://github.com/anthropics/skills/blob/e4bb5d960d87126ff3b3a8af1a104b7db67560ba/skills/frontend-design/SKILL.md), `e4bb5d960d87126ff3b3a8af1a104b7db67560ba` | Связь визуального языка с содержанием продукта; компактное направление до реализации; цельная композиция и самокритика выбранных средств |
| [Next Level Builder — UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/7436a6e0b6dc3add7c12d5b6ef1ccd3d410dd7fd/.claude/skills/ui-ux-pro-max/SKILL.md), `7436a6e0b6dc3add7c12d5b6ef1ccd3d410dd7fd` | Согласованный подбор стиля, цвета и типографики под продукт; конкретные tokens; общая система и локальные исключения; проверка уместности рекомендаций |
| [Leonxlnx — Taste Skill](https://github.com/Leonxlnx/taste-skill/blob/f6b76575f949707b4e3c37cd86cb44b0b98643e8/skills/taste-skill/SKILL.md), `f6b76575f949707b4e3c37cd86cb44b0b98643e8` | Показ реального предмета предложения; качество и согласованность изображений; соответствие оформления виду бизнеса; работа с настоящим контентом и проверка браузером |

## Дополнительные изученные материалы

- Impeccable: [craft floor](https://github.com/pbakaus/impeccable/blob/d41d9860b0094dcb68030657da63461212835aaa/.claude/skills/impeccable/reference/craft-floor.md), [polish](https://github.com/pbakaus/impeccable/blob/d41d9860b0094dcb68030657da63461212835aaa/.claude/skills/impeccable/reference/polish.md), [typeset](https://github.com/pbakaus/impeccable/blob/d41d9860b0094dcb68030657da63461212835aaa/.claude/skills/impeccable/reference/typeset.md), [layout](https://github.com/pbakaus/impeccable/blob/d41d9860b0094dcb68030657da63461212835aaa/.claude/skills/impeccable/reference/layout.md), [new visual work](https://github.com/pbakaus/impeccable/blob/d41d9860b0094dcb68030657da63461212835aaa/.claude/skills/impeccable/reference/new-work-world.md).
- Taste Skill: [README](https://github.com/Leonxlnx/taste-skill/blob/f6b76575f949707b4e3c37cd86cb44b0b98643e8/README.md), для проверки текущего расположения и назначения skill.

## Что изменено при адаптации

- Сохранён существующий UX-контракт product-designer; добавлены визуальная проработка и обратная проверка реализации. Код остаётся в зоне frontend-engineer.
- References загружаются по задаче. Не требуется проходить весь процесс для замены отступа или UX-консультации.
- Приоритет имеют запрос пользователя, действующая система и сценарий. Не перенесены абсолютные запреты на шрифты, подписи, карточки и другие приёмы.
- Не перенесены случайный выбор концепта, обязательные согласования через отдельный сервер, фиксированная высота секций и обязательная анимация каждого сайта.
- Не перенесены правила подмены реальных контактов, наборы шаблонных страниц, отраслевые ограничения на темы и эффекты, системные установки и browser/agent launchers. Материалы проекта и продуктовые факты сохраняются.
- База UI UX Pro Max не включена: локальная инструкция задаёт метод подбора и проверки системы, не обещая поиск по отсутствующим данным.
- Удачный build или чистый детектор не доказывают визуальное качество; дизайн-ревью и фактическая проверка взаимодействий отмечаются отдельно.

## Лицензии и авторство

- Impeccable — Copyright 2025 Paul Bakaus, Apache-2.0: [точный LICENSE](../licenses/impeccable-Apache-2.0.txt). Сохранён upstream [NOTICE](../licenses/impeccable-NOTICE.md); упомянутые в нём native-platform references в эту адаптацию не переносились.
- Anthropic Frontend Design — Anthropic, Apache-2.0: [точный LICENSE.txt](../licenses/anthropic-frontend-design-Apache-2.0.txt).
- UI UX Pro Max — Copyright 2024 Next Level Builder, MIT: [точный LICENSE](../licenses/ui-ux-pro-max-MIT.txt).
- Taste Skill — Copyright 2026 Leonxlnx, MIT: [точный LICENSE](../licenses/taste-skill-MIT.txt).

Тексты переработаны для локального workflow; копирования upstream-кода и библиотек оформления нет. Эта заметка фиксирует происхождение адаптированных приёмов и не является оценкой качества модели. Структурная валидация skill сама по себе не доказывает улучшение реального дизайна.
