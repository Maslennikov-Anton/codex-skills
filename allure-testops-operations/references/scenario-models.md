# Модели сценария в Allure TestOps 5.23.0

На этом инстансе у manual scenario есть как минимум две разные API-модели, и они ведут себя по-разному.

## 1. Write-модель manual scenario

Источник:

- `GET /api/testcase/{id}/scenario`
- `POST /api/testcase/{id}/scenario`

Форма шага:

- `name`
- `expectedResult`
- `steps`

Этот endpoint используется для записи сценария, но `GET` у него deprecated.

`GET /api/testcase/{id}/scenario` по-прежнему возвращает шаги в виде:

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

Не используй этот `GET` как единственный источник истины для того, что реально покажет карточка кейса в UI.

## 2. Overview-модель карточки test case

Источник:

- `GET /api/testcase/{id}/overview`

На этом инстансе именно `overview` подтвержденно возвращает:

```json
{
  "scenario": {
    "steps": [
      {
        "name": "Шаг",
        "expectedResult": "Ожидаемый результат шага"
      }
    ]
  }
}
```

Для финальной проверки того, что backend отдает карточке кейса ожидаемый результат шага, используй именно `overview`.

## 3. Low-level модель дерева шагов

Источник:

- `GET /api/testcase/{id}/step`
- `PATCH /api/testcase/step/{id}`

Форма узла:

- `body`
- `expectedResultId`
- дочерние узлы сценария

Эта модель полезна для редактора и внутренних узлов дерева, но не является надежным источником истины для того, что именно покажет UI manual scenario в Allure 5.23.0.

## Подтвержденное поведение на живом инстансе

1. `POST /api/testcase/{id}/scenario` с шагами `name + expectedResult` корректно обновляет сценарий.
2. После этого `GET /api/testcase/{id}/overview` возвращает нужные шаги и expected result в `scenario.steps`.
3. `GET /api/testcase/{id}/scenario` тоже может возвращать нужные шаги, но этот endpoint deprecated.
4. При этом low-level дерево `GET /api/testcase/{id}/step` может:
   - потерять текст шага в `body`, либо
   - перестроить шаги и их внутренние id.
5. Поэтому после записи сценария нужно отдельно проверять `overview`, а затем low-level дерево.

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

3. После записи перепроверь `overview` и low-level модель:

```bash
scripts/allure_testops_api.sh testcase-overview-get 1811
scripts/allure_testops_api.sh testcase-scenario-get 1811
scripts/allure_testops_api.sh testcase-step-tree 1811
```

## Практическое правило

- Для ручных тест-кейсов Allure TestOps 5.23.0 сначала обновляй write-модель `scenario`.
- Затем проверяй `overview`, потому что он ближе к реальному backend-представлению карточки кейса.
- Затем синхронизируй low-level `step`-дерево, чтобы редактор и вспомогательные API не теряли `body`.
- Не пытайся использовать только `PATCH /api/testcase/{id}` с `scenario` V2 как единственный способ обновления manual scenario: это может оставить расхождения между `overview` и low-level представлениями.
