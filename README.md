# codex-skills

Локальный репозиторий skills для Codex.

Репозиторий нужен для:

- хранения и версионирования локальных skills;
- переноса skills между машинами;
- командного review изменений через git;
- быстрого восстановления каталога `~/.codex/skills`.

## Что здесь хранится

- обычные локальные skills, например `analyst`, `python-developer`, `team-engineering-style`;
- системные skills из `.system/`;
- дополнительные skills, которые в исходной локальной установке могли быть symlink'ами.

В этом репозитории такие symlink'и уже развернуты в обычные файлы, чтобы содержимое было переносимым на другую машину.

## Быстрый старт на новой машине

### 1. Клонировать репозиторий

```bash
git clone git@github.com:Maslennikov-Anton/codex-skills.git ~/codex-skills
```

### 2. Развернуть skills в Codex

```bash
mkdir -p ~/.codex
rm -rf ~/.codex/skills
cp -r ~/codex-skills ~/.codex/skills
```

После этого перезапустите Codex, чтобы он подхватил новые skills.

## Рекомендуемый способ работы

Удобнее считать `~/codex-skills` каноническим git-репозиторием, а в `~/.codex/skills` хранить его копию или symlink.

Вариант с symlink:

```bash
mkdir -p ~/.codex
rm -rf ~/.codex/skills
ln -s ~/codex-skills ~/.codex/skills
```

Плюсы этого подхода:

- все правки сразу делаются в git-репозитории;
- проще коммитить и пушить изменения;
- нет риска забыть синхронизировать две копии.

## Как обновлять skills после изменений

Commit и `git push` выполняются только по явному запросу пользователя. Обычное обновление skill заканчивается локальной проверкой и обзором diff.

Если `~/.codex/skills` указывает на `~/codex-skills` через symlink:

```bash
cd ~/codex-skills
git status --short --ignored
git add <явный-список-измененных-путей>
git diff --cached --check
git commit -m "Update Codex skills"
git push
```

Если `~/.codex/skills` хранится как отдельная копия:

```bash
rsync -a --exclude '.git/' ~/.codex/skills/ ~/codex-skills/
cd ~/codex-skills
git status --short --ignored
git add <явный-список-измененных-путей>
git diff --cached --check
git commit -m "Update Codex skills"
git push
```

## Как подтянуть обновления на другой машине

```bash
cd ~/codex-skills
git pull
rm -rf ~/.codex/skills
ln -s ~/codex-skills ~/.codex/skills
```

Если symlink не нужен, вместо этого можно просто скопировать файлы:

```bash
rm -rf ~/.codex/skills
cp -r ~/codex-skills ~/.codex/skills
```

## Что обычно не стоит хранить вместе со skills

В этот репозиторий не нужно складывать runtime-данные Codex, например:

- `~/.codex/auth.json`;
- `~/.codex/history.jsonl`;
- `~/.codex/sessions/`;
- `~/.codex/logs_*.sqlite`;
- `~/.codex/state_*.sqlite`;
- `~/.codex/tmp/`.

Если нужно переносить не только skills, но и конфигурацию, отдельно можно версионировать:

- `~/.codex/config.toml`;
- `~/.codex/memories/`.

## Локальный аудит Codex-сессий

Для быстрой проверки workflow-антипаттернов есть read-only утилита:

```bash
python3 scripts/audit_codex_sessions.py --days 30
```

Она читает `~/.codex/sessions/**/*.jsonl` и строит отчет по практичным правилам, адаптированным из AI Engineering Coach:

- слишком длинные сессии и drift между типами задач;
- повторяющиеся промпты и слабая структура старта задачи;
- низкое использование ограничений, verbose output и тяжелые tool-сессии.

Markdown-отчет можно сохранить так:

```bash
python3 scripts/audit_codex_sessions.py --days 30 --format markdown --output reports/codex-session-audit.md
```

## Проверка skills

```bash
python3 scripts/audit_skills.py --strict --require-smoke-coverage
python3 -m unittest discover -s scripts -p 'test_*.py'
git diff --check
```

Статический аудит не измеряет фактический выбор skill моделью. Fixtures, scorer JSONL traces и сравнение before/candidate описаны в [поведенческих проверках](team-engineering-style/references/behavior-evaluations.md). Runtime intermediates сохраняй в owned workspace через `artifact-lifecycle`, итоговые отчёты и evidence — в `~/codex-reports/`.

## Временные файлы и честные тесты

- [artifact-lifecycle](artifact-lifecycle/SKILL.md) создаёт один owned scratch на задачу, проверяет preview/активные процессы и сохраняет компактные evidence до удаления intermediates. Старые неучтённые папки не чистит по маске/возрасту.
- [Test integrity](autotest-engineer/references/test-integrity.md) закрепляет contract oracle и baseline/change alarm для test/CI surfaces. Любая правка проверок требует review; helper не доказывает семантическую силу теста. Продуктовый defect остаётся failed, завершение qualification не требует зелёного продукта.
- [defaults/AGENTS.md](defaults/AGENTS.md) — краткие user-wide правила, устанавливаемые в `~/.codex/AGENTS.md` после проверки существующих defaults/override. Не заменяй чужой файл вслепую. Они загружаются в новых запусках согласно [официальной документации](https://developers.openai.com/codex/guides/agents-md).

Helpers используют Python >=3.11 stdlib; lifecycle helper предназначен для Linux. Новые зависимости и фоновые очистители не нужны. Локальные проверки helpers не являются модельным A/B benchmark.

## Экспериментальные дополнения

- [property-based-testing](property-based-testing/SKILL.md): свойства контракта, генераторы и минимальные контрпримеры; Python/Hypothesis reference.
- [variant-analysis](variant-analysis/SKILL.md): поиск других проявлений известного дефекта с проверкой кандидатов.
- [requirements-coverage-audit](requirements-coverage-audit/SKILL.md): документ → сценарий → исполнимый assertion; статическое покрытие отдельно от результата продукта.
- [test-results-analysis](test-results-analysis/SKILL.md): локальный адаптер Allure JSON и история результатов с разделением retry, rerun и версий окружения.
- [semgrep-rule-creator](semgrep-rule-creator/SKILL.md): проверяемый guard для известного bug pattern, включая safe controls.
- [performance-benchmark](performance-benchmark/SKILL.md): CPU/memory profiling и консервативное сравнение одинаковой нагрузки before/after.
- [mutation-testing](mutation-testing/SKILL.md): mutmut, surviving mutants и доказанная чувствительность Python-тестов к изменениям поведения.
- [dependency-updates](dependency-updates/SKILL.md): changelog, runtime/constraints, точный кандидат и проверенное обновление пакетов.
- В [code-review-professional](code-review-professional/SKILL.md) добавлены методы test gap audit и поиска скрытых ошибок; отдельные роли для них не создаются.
- В [gitlab-operations](gitlab-operations/SKILL.md) добавлены проверка compiled CI config, границы lint simulation, rules/needs, artifacts и диагностика capacity.
- В [systematic-debugging](systematic-debugging/SKILL.md) добавлены Linux/native/Python stack, syscall и crash recipes из The Art of Debugging.
- В [security-engineer](security-engineer/SKILL.md) добавлен аудит зависимостей с collector/renderer и явным assessed/unassessable coverage.

Источники закреплены по commit и описаны в `references/upstream.md` соответствующего skill. `property-based-testing`, `variant-analysis`, `requirements-coverage-audit` и `semgrep-rule-creator` адаптированы из Trail of Bits по CC-BY-SA-4.0. Для Microsoft/Anthropic сохранены Apache-2.0 и применимый NOTICE, для GitHub Awesome Copilot и perf-benchmark — MIT. Полные license texts лежат рядом с адаптациями. Статус `experimental` не задает обязательный workflow для всех задач.

Для offline helpers дополнительно выполняются contract tests в общем unittest discovery. Semgrep нужен только для его пилота/реальной работы с rules; остальные новые helpers используют stdlib. Проверка инструкций и fixtures не является модельным A/B benchmark.

Для пяти дополнений следующей партии сохранены MIT (`kpatryk/skills`, `beeyev/skills`), BSD-3-Clause (`mitodl/agent-kit`) и CC-BY-SA-4.0 (Stas Bekman и Trail of Bits); attribution и точные commits находятся в новых provenance references. Upstream collector/renderer, их модули и четыре pytest-файла сохранены без изменений.

Дополнительная проверка vendored dependency-audit helpers:

```bash
codex-tools-pytest security-engineer/scripts/supply_chain -q -p no:cacheprovider
```

Runtime collector использует stdlib Python >=3.11. Для тестов нужен pytest. `mutmut 3.8.0` установлен отдельным постоянным `uv tool`; для целевого проекта его окружению нужны зависимости и pytest-плагины проекта. На этой машине также доступны постоянные `codex-tools-python`/`codex-tools-pytest`, gdb, strace и shellcheck. Наличие инструментов не означает, что проект мигрирован на них.

## Правило обновления

Если меняется локальный стандарт работы, workflow команды или поведение skills, изменение нужно:

1. внести в соответствующий skill;
2. проверить локально;
3. по явному запросу закоммитить в этот репозиторий;
4. по явному запросу запушить в GitHub.

Это делает skills переносимыми и воспроизводимыми между машинами.
