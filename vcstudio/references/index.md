# Карта reference-файлов VCStudio

Открывай только минимальный набор файлов для текущего вопроса. Не загружай большие snapshots целиком.

## Архитектура и пользовательская работа

- `studio-vcont-contract.md` — граница ответственности Studio/VCont, lifecycle, object mapping, load/runtime commands и HSB boundary.
- `project-workflow.md` — `.vcsys`, workspace, иерархия, задачи, ФБ, связи, порядок выполнения и event-loop authoring.
- `loading-monitoring.md` — full/online load, ST/Lua instance creation, framing, Watch, live write, forcing и `TriggerEvent`.
- `communications.md` — настройка Modbus/OPC UA в Studio и соответствие generated/runtime artifacts.

## Structured Text

- `st-language.md` — основной compatibility contract: editor и translator grammar, Studio wrapper, interface indexes, ограничения с обходами, codegen и test guardrails. Открывай перед генерацией, исправлением или оценкой ST-теста.

## Библиотека и исходники

- `fb-typelibrary.md` — формат `.fbt`, проверенные свойства typelibrary, runtime mapping и guardrails.
- `source-repo-map.md` — Tycho build, plugins/features/tests, EMF/DTO, packaging, CI/release и карта локального исходного репозитория.

## Руководство VC024SA.B

- `vc024sa-key-facts.md` — плотная база для большинства вопросов по актуальному руководству.
- `vc024sa-section-map.md` — навигация по полному тексту; для разделов `6.7+` точнее устаревшего оглавления PDF.
- `vc024sa-complete.md` — полный embedded extract для точных формулировок, подписей и редких таблиц. Сначала найди раздел по карте, затем читай только нужный диапазон.

## Большой generated-каталог

- `fb-typelibrary-catalog.md` — snapshot 473 интерфейсов `.fbt`. Сначала ищи блок командой `rg -n 'имя_блока' references/fb-typelibrary-catalog.md`, не открывай файл целиком.

Для фактического runtime execution, логов, bootfile, HSB или тестовых oracle переходи через `studio-vcont-contract.md` к skill `vcont`.
