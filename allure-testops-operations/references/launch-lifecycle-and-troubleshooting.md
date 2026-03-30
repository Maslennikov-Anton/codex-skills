# Launch lifecycle и troubleshooting

Основные источники:

- https://docs.qameta.io/allure-testops/briefly/launches/
- https://help.qameta.io/support/solutions/articles/101000544779-understanding-test-case-association-across-projects

## Ключевые продуктовые правила

- Пока launch открыт, Allure TestOps не завершает часть post-processing логики.
- Открытый launch не стоит считать финальным состоянием ingestion.
- Test case в Allure TestOps привязан к project; upload в другой project не всегда создаст новый кейс, если связь уже существует.

## Типовые симптомы

### 1. Launch создан, но статистика выглядит неполной

Проверь:

- закрыт ли launch;
- завершён ли `allurectl watch` / upload flow;
- нет ли задержки post-processing на стороне TestOps.

### 2. Результаты загружены, но test cases не появились там, где ожидалось

Проверь:

- правильный ли `ALLURE_PROJECT_ID`;
- не были ли test cases уже ассоциированы с другим project;
- какой upload policy действует в проекте.

### 3. Launch есть, но job/launch metadata не та

Проверь:

- какие env vars реально были выставлены в CI;
- не переопределены ли launch name/tags/job run параметры;
- не смешаны ли несколько upload flows в один launch.

### 4. API и UI показывают разную картину

Проверь:

- какой endpoint является источником истины для этой сущности;
- завершён ли lifecycle launch;
- не смотришь ли ты на промежуточное состояние до post-processing.

## Практические правила

- Для проблем ingestion сначала проверяй lifecycle launch, а не сразу payload.
- Для проблем project binding сначала проверяй association rules, а не только текущий upload.
- Если поведение кажется нелогичным, явно разделяй:
  - transport/upload;
  - launch lifecycle;
  - project/test case association;
  - UI presentation.
