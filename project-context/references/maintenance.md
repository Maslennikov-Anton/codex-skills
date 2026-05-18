# Project Context Maintenance

Use this guide when refreshing `project-context` itself. Keep the result compact,
verified, and useful during future local repo work.

## Refresh Flow

1. List local repos shallowly, for example `find /home/ant/IdeaProjects -maxdepth 2 -name .git -type d | sort`.
2. Compare repo names with `references/workspace-map.md`.
3. For each missing or stale repo, inspect executable evidence before prose docs:
   `.gitlab-ci.yml`, `.github/workflows`, `docker-compose*`, Dockerfiles,
   `pyproject.toml`, `pytest.ini`, `requirements*.txt`, `package.json`,
   `Makefile`, `scripts/`, and project-specific test config.
4. Use `README*` for intent and onboarding, but resolve conflicts in favor of CI,
   scripts, Dockerfiles, and commands that actually exist locally.
5. Record only stable facts that help future Codex turns choose safer commands,
   scope edits, avoid generated files, or understand high-impact operations.
6. Keep transient state in memory handoff notes, not in this skill: spike status,
   temporary test names, current pipeline IDs, exact dirty diffs, and unapproved
   experiments do not belong in `workspace-map.md`.

## Entry Shape

Each repository entry should stay short and follow this shape:

- Purpose: one sentence explaining what the repo is for.
- Stack: languages, major frameworks/tools, CI/deployment surface.
- Known workflows: commands used to set up, run, build, start, stop, or inspect.
- Verification commands: commands that prove a typical edit is good.
- Notes: repo-specific hazards, stale docs, generated paths, related skills, or
  external-system boundaries.

Prefer exact commands over descriptions. Include prerequisites only when they
change how Codex should act, for example required artifacts, local services,
credentials, Docker profiles, cloud access, or dangerous infrastructure effects.

## What To Exclude

- Secrets, tokens, passwords, host-specific credential values, or private keys.
- Full logs, large command output, long reports, or copied documentation.
- Generated artifacts, caches, virtualenv contents, Allure output, runtime
  directories, and editor state.
- One-off branches, commit hashes, MR/pipeline numbers, and temporary spikes,
  unless the user explicitly asks for a short-lived handoff memory instead.
- Instructions that duplicate a domain skill; link to the domain skill in notes
  and keep only repo-specific command/context facts here.

## Dirty Worktrees

Before modifying source repos, check `git status --short --ignored`. Use it to
separate tracked project changes from ignored runtime/editor/test artifacts.
Never revert unrelated local changes. For push tasks, stage according to the
repo's `.gitignore` and the user's explicit scope.

## Memory Boundary

Use persistent memory for time-bound handoffs, prior decisions, and recent
session facts that may be useful tomorrow. Use `project-context` for stable repo
facts that should still be true after the current branch, spike, or pipeline is
gone. If a fact is both important and likely to drift, record the command or file
that verifies it instead of recording only the observed value.

## Verification

After changing this skill, run:

```bash
git diff --check
python3 .system/skill-creator/scripts/quick_validate.py project-context
```

Also verify that every relative reference from `SKILL.md` exists. If the update
changed multiple skills or global conventions, validate all affected skills.
