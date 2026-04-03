---
name: fuzzing-bug-hunter
description: Искать новые баги и скрытые ограничения через matrix fuzzing, grammar fuzzing и targeted bug hunting. Использовать, когда Codex должен системно исследовать failure surface, строить матрицы `construct x context x operand-shape`, отделять реальные дефекты от harness noise, минимизировать воспроизведение и переводить находки в bug artifact, inventory и regression cases. Не использовать для обычного написания детерминированных автотестов без исследовательского слоя, для доказательства root cause уже найденного дефекта или для обычного code review — для этого есть `autotest-engineer`, `systematic-debugging` и `code-review-professional`.
---

# Fuzzing Bug Hunter

Используй этот skill, когда задача не в том, чтобы просто покрыть известный сценарий тестом, а в том, чтобы расширить карту отказов системы и найти новые defect families.

## Когда использовать

- Нужно найти новые defect families, а не только зафиксировать уже известный сценарий.
- Нужно системно продавить поверхность через матрицу `construct x context x operand-shape`.
- Нужно понять, какие границы реально supported, а какие только кажутся supported.
- Нужно перевести исследовательские находки в воспроизводимые declarative cases и bug artifact.

## Когда не использовать

- Если сценарий уже известен и нужен просто стабильный regression test, используй `autotest-engineer`.
- Если дефект уже найден и задача сместилась к доказательству root cause, используй `systematic-debugging`.
- Если нужно оценить качество уже написанных тестов, generators или repro artifacts, используй `code-review-professional`.
- Если речь идет только о ручной exploratory-проверке без автоматизированного генератора, используй `manual-tester`.

## Workflow

1. Определи поверхность поиска:
   - grammar;
   - parser;
   - codegen;
   - runtime;
   - input hygiene;
   - diagnostics quality.
2. Проверь, что уже известно:
   - bug artifact;
   - декларативный inventory в `tests/cases`;
   - существующие matrix-артефакты и generators.
3. Сформулируй матрицу:
   - `construct x context x operand-shape`;
   - минимально достаточный, но комбинаторно полезный набор значений;
   - явная гипотеза, какую границу система может ломать.
4. Запусти исследование так, чтобы signal был правдивым:
   - сначала отдели harness noise от реального дефекта;
   - не считай новый surface найденным, пока не снят representative raw diagnostic;
   - различай parser/codegen/runtime/environment failures.
5. После подтверждения нового сигнала:
   - минимизируй воспроизведение;
   - оформи отдельный declarative case, который сам проходит при своем oracle;
   - обнови отдельный bug artifact и стратегический документ;
   - прогони релевантный baseline suite.
6. Если новых defects нет, зафиксируй это как результат:
   - какая поверхность проверена;
   - какие границы confirmed supported;
   - почему следующий фронт поиска надо смещать.

## Что покрывает этот skill

- Matrix fuzzing и targeted bug hunting.
- Поиск новых defect families, а не только новых примеров старого бага.
- Triage false positives и harness noise.
- Минимизация и формализация repro.
- Синхронизацию `artifact -> inventory -> regression`.

## Границы ответственности

- Этот skill отвечает за расширение знания о failure surface системы.
- Этот skill не отвечает за обычную реализацию продуктового fix.
- Этот skill не заменяет deterministic test engineering после того, как новая граница уже найдена.
- Этот skill не должен подменять root-cause investigation, если поверхность уже найдена и вопрос теперь в механике дефекта.
- Если генератор не открывает новый класс проблемы, результатом должна быть фиксация проверенной поверхности, а не искусственное наращивание кейсов.

## Базовые правила

- Главная цель fuzzing-а здесь не покрытие ради покрытия, а рост правдивого знания о границах системы.
- Не превращай exploratory matrix в набор случайных комбинаций без гипотезы.
- Один новый defect family ценнее десятка почти одинаковых кейсов без новой границы.
- Если новый сигнал оказался noise из harness или setup, сначала почини harness, потом продолжай исследование.
- Не озеленяй результаты за счёт удаления плохих входов или ослабления oracle.
- Не превращай bug reproducer в постоянный `xfail`-кейс. Воспроизводимость дефекта должна подтверждаться отдельно от статуса тестового кейса.
- `xfail` допустим только как краткий переходный режим после воспроизводимого defect artifact; до этого проблема должна считаться открытой находкой, а не оформленным known bug.
- Если reproducер начал проходить, это stale signal, а не повод оставлять старый bug inventory без изменений.
- После подтверждения фикса или невоспроизводимости defect family нужно либо перевести кейс в supported regression, либо убрать его из bug inventory.
- Всегда разделяй:
  - parser failure;
  - codegen failure;
  - runtime failure;
  - environment dependency;
  - diagnostics defect.
- Если поверхность проверена и новых багов нет, это тоже полезный результат и его нужно фиксировать явно.

## Типовые исследовательские оси

- selector/context matrix для control flow
- built-in argument matrix
- placement/context matrix для standard blocks
- input hygiene matrix
- diagnostics normalization matrix
- sequence-level combinations нескольких unsupported forms

## Формат результата

Когда просят заняться fuzzing/bug hunting, возвращай:

1. Какую поверхность исследовал.
2. Какая матрица или гипотеза использовалась.
3. Какие новые defect families найдены, если найдены.
4. Какие зоны confirmed supported.
5. Какие кейсы/артефакты/документы обновлены.
6. Какой следующий фронт исследования рационален.

## Связь с другими skills

- Используй вместе с `autotest-engineer`, если нужно превратить находки в стабильные regression tests.
- Используй вместе с `systematic-debugging`, если задача уже сместилась от поиска поверхности к доказательству root cause.
- Используй вместе с `code-review-professional`, если нужно оценить качество уже созданных fuzz/repro artifacts.
- Используй вместе с `team-engineering-style`, если нужно закрепить новый устойчивый процесс fuzzing или развести зоны ответственности между skills.
