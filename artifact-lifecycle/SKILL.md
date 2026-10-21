---
name: artifact-lifecycle
description: "Убирать мусор агента: временные папки, scratch, анализ, прогоны, disposable venv и clones; сохранять отчёт и failure evidence. Use at task completion; not general system/cache cleanup."
---

# Жизненный цикл временных файлов

Используй при создании временных файлов для анализа, пилотов, тестов и benchmarks, а также перед завершением такой задачи. Статус: experimental; helper проверен локально, выбор skill моделью отдельно не доказан.

## Workflow

1. Создай один owned workspace на задачу через [scripts/workspace.py](scripts/workspace.py). Новые disposable venv, clones, загрузки и промежуточные результаты размещай в его `scratch/`. Переиспользуемые установленные утилиты остаются в штатном tool/cache location.
2. В `evidence/` положи компактный `REPORT.md`: команды, версии/хеши артефактов, фактические exit codes и результаты, ограничения. Сохрани минимальный reproducer, сырой failing output и необходимые вложения. Успешный отчёт не заменяет failure evidence.
3. Долгие команды запускай через `run`, чтобы lock защищал папку. Останови только свои процессы перед уборкой. Не убирай workspace во время расследования или при передаче незавершённой задачи.
4. Выполни `finish` без `--apply`: проверь объём и итоговый путь отчёта. После сохранения доказательств и проверки disposable-содержимого заверши через `--apply` в пределах уже разрешённой задачи. Отдельная просьба пользователя для собственных временных промежуточных файлов не нужна.
5. В ответе ссылайся на retained report, а не удалённый scratch. Если workspace оставлен, укажи точный путь, причину и условие следующей уборки. У retained user deliverables нет автоматического срока удаления.

## Commands

```bash
python3 /home/ant/codex-skills/artifact-lifecycle/scripts/workspace.py start --purpose 'skill pilot'
python3 /home/ant/codex-skills/artifact-lifecycle/scripts/workspace.py run RUN_ID -- python3 probe.py
python3 /home/ant/codex-skills/artifact-lifecycle/scripts/workspace.py finish RUN_ID
python3 /home/ant/codex-skills/artifact-lifecycle/scripts/workspace.py finish RUN_ID --apply
```

Default scratch root: `~/.cache/codex-workspaces`. Retained evidence: `~/codex-reports/RUN_ID/`. Подставь ID из `start`; helper не принимает произвольный путь удаления. Python stdlib, Linux. `run` передаёт исходный exit code команды.

## Границы

- Helper удаляет только созданные им marked workspaces. Preview ничего не удаляет. Symlink root/run/evidence, чужой owner, active processes, mount и отсутствие отчёта блокируют уборку. Ссылки внутри scratch удаляются как ссылки, их targets остаются.
- Старые `/tmp/*`, `.work`, caches и другие неучтённые каталоги сначала только инвентаризируй: exact path, owner, size, provenance, active use, retained evidence. Имя, возраст и `.gitignore` не доказывают disposable status. Не «усыновляй» неизвестную папку созданием marker.
- Не трогай исходники, пользовательские данные, product distributions, project `.venv`, IDE, credentials, историю чатов, память, VPN, чужие процессы и managed Git worktrees. Для последних используй штатный lifecycle инструмента.
- Не добавляй cron, общую чистку `/tmp`, системных package caches или Docker volumes как побочный эффект. Не переносить мусор в бессрочную скрытую корзину.
- Перед удалением legacy evidence сохрани минимальное объяснение, воспроизведение и нужные пользователю результаты. Не удаляй доказательства падения ради красивого отчёта.

## Sources

[references/upstream.md](references/upstream.md) — найденные GitHub skills, полезные идеи и причины локальной адаптации.
