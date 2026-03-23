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

Общее правило: если добавлен новый skill или изменен существующий, изменения нужно не только сохранить локально, но и закоммитить с `git push` в GitHub-репозиторий `codex-skills`, если нет явного запрета от пользователя.

Если `~/.codex/skills` указывает на `~/codex-skills` через symlink:

```bash
cd ~/codex-skills
git status
git add .
git commit -m "Update Codex skills"
git push
```

Если `~/.codex/skills` хранится как отдельная копия:

```bash
rsync -a --delete ~/.codex/skills/ ~/codex-skills/
cd ~/codex-skills
git status
git add .
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

## Правило обновления

Если меняется локальный стандарт работы, workflow команды или поведение skills, изменение нужно:

1. внести в соответствующий skill;
2. проверить локально;
3. закоммитить в этот репозиторий;
4. запушить в GitHub.

Это делает skills переносимыми и воспроизводимыми между машинами.
