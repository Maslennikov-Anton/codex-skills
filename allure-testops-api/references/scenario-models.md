# Модели сценария в Allure TestOps 5.23.0

На этом инстансе у manual scenario есть как минимум две разные API-модели, и они ведут себя по-разному.

## 1. UI-модель manual scenario

Источник:

- `GET /api/testcase/{id}/scenario`
- `POST /api/testcase/{id}/scenario`

Форма шага:

- `name`
- `expectedResult`
- `steps`

Именно эта модель подтвержденно возвращает шаги в виде:

```json
{
  "steps": [
    {
      "name": "Шаг",
      "expectedResult": "Ожидаемый результат шага"
    }
  ]
}
```

Для отображения шага и expected result в UI manual scenario считай эту модель основной.

## 2. Low-level модель дерева шагов

Источник:

- `GET /api/testcase/{id}/step`
- `PATCH /api/testcase/step/{id}`

Форма узла:

- `body`
- `expectedResultId`
- дочерние узлы сценария

Эта модель полезна для редактора и внутренних узлов дерева, но не является надежным источником истины для того, что именно покажет UI manual scenario в Allure 5.23.0.

## Подтвержденное поведение на живом инстансе

1. `POST /api/testcase/{id}/scenario` с шагами `name + expectedResult` корректно обновляет UI-модель сценария.
2. После этого `GET /api/testcase/{id}/scenario` возвращает нужные шаги и expected result.
3. При этом low-level дерево `GET /api/testcase/{id}/step` может:
   - потерять текст шага в `body`, либо
   - перестроить шаги и их внутренние id.
4. Поэтому после записи UI-модели нужно отдельно проверять low-level дерево.

## Рекомендуемый порядок записи сценария

1. Сформируй canonical scenario как список шагов:

```json
{
  "steps": [
    {
      "name": "Открыть карточку тест-кейса.",
      "expectedResult": "Карточка тест-кейса открыта."
    },
    {
      "name": "Проверить обязательные поля.",
      "expectedResult": "Обязательные поля отображаются и заполнены."
    }
  ]
}
```

2. Запиши его в UI-модель:

```bash
scripts/allure_testops_api.sh testcase-scenario-get 1811
scripts/allure_testops_api.sh testcase-sync-scenario 1811 /tmp/scenario.json
```

3. После записи перепроверь обе модели:

```bash
scripts/allure_testops_api.sh testcase-scenario-get 1811
scripts/allure_testops_api.sh testcase-step-tree 1811
```

## Практическое правило

- Для ручных тест-кейсов Allure TestOps 5.23.0 сначала обновляй UI-модель `scenario`.
- Затем синхронизируй low-level `step`-дерево, чтобы редактор и вспомогательные API не теряли `body`.
- Не пытайся использовать только `PATCH /api/testcase/{id}` с `scenario` V2 как единственный способ обновления manual scenario: это может оставить расхождения между UI и low-level представлениями.
