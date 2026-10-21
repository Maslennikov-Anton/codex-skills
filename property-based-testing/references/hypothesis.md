# Python / Hypothesis

Читай при разработке или разборе Python property tests. Основные API: [`given`, strategies, examples](https://hypothesis.readthedocs.io/en/latest/quickstart.html) и [настройки](https://hypothesis.readthedocs.io/en/latest/reference/api.html#hypothesis.settings).

## Стратегии и oracle

- Ограничения домена выражай через `min_value`, `max_value`, `min_size`, `max_size`, `unique` и составные стратегии.
- Для зависимых полей используй `st.composite`, `flatmap` или `data`: индекс должен указывать на сгенерированный список, длина — соответствовать payload.
- Не повторяй алгоритм реализации. Для разбиения сравни сохранность элементов, отсутствие лишних/повторных назначений и требуемый порядок, а не вычисляй вторую копию разбиения.
- Не выключай health checks для сокрытия слишком сильной фильтрации или утечки состояния. Устрани причину либо зафиксируй конкретное обоснование.

## Минимальный пример

Ниже шаблон для чистой функции сортировки; здесь контракт обещает сохранение элементов и неубывающий порядок. Подставь функцию проекта, не добавляй копию реализации в тест.

```python
from collections import Counter
from hypothesis import example, given, settings, strategies as st

@settings(max_examples=100)
@example([])
@example([1, 1])
@given(st.lists(st.integers(), max_size=50))
def test_sort_contract(values):
    original = list(values)
    actual = sort_values(values)
    assert Counter(actual) == Counter(original)
    assert all(left <= right for left, right in zip(actual, actual[1:]))
```

`sort_values` — функция под тестом, не API Hypothesis. Для standalone-функции вызови тест из Python или запусти его принятым в проекте pytest runner.

## Время и состояние

- Подбери `max_examples` по реальной цене теста. Небольшой pilot budget не равен полноценной qualification.
- Для медленного I/O проверь применимость PBT; если `deadline=None` обоснован, сохрани внешний timeout всего прогона.
- В pytest function-scoped fixture обычно живет весь запуск property test, а не один generated example. Создавай/сбрасывай изменяемое состояние внутри тела каждого примера.
- Сохрани минимальный контрпример как `@example(...)` или обычный regression test. Example database — полезный кэш локальных находок, а не единственное хранилище regression evidence.
- Для повторяемого локального smoke можно использовать `derandomize=True` и записать версию; это не гарантирует одинаковую последовательность после обновления Hypothesis.

## Разбор падения

1. Проверь, входит ли уменьшенный вход в обещанный домен.
2. Найди конкретное основание свойства. Например, идемпотентность не следует из одного имени `normalize`.
3. Если контракт нарушен, зафиксируй expected/actual и воспроизведение на том же коде. Если нарушена предусловие, исправь стратегию; если контракт неоднозначен, явно отметь нерешенный вопрос.
4. При проверке тестов намеренно измененной реализацией укажи, что это seeded mutation, а не вновь найденный дефект проекта. Такой контроль полезен для oracle, но не обязателен для каждого теста.
