# Plan Template

```markdown
# <Feature> Implementation Plan

Goal:
- ...

Non-goals:
- ...

Acceptance criteria:
- ...

File map:
- Create: `path/to/new_file.ext` - purpose
- Modify: `path/to/existing_file.ext` - change
- Test: `path/to/test_file.ext` - coverage

## Task 1: <name>

Files:
- Modify: `path/to/file.ext`
- Test: `path/to/test.ext`

Steps:
- [ ] Write failing/targeted test for <behavior>.
  Command: `<test command>`
  Expected: fails with <specific reason>, or passes after setup-only change.
- [ ] Implement <specific change>.
  Details: <function/type/module names and behavior>.
- [ ] Run verification.
  Command: `<verification command>`
  Expected: <specific pass/fail output>.

## Task 2: <name>

...

Final verification:
- Command: `<full relevant command>`
- Expected: <specific pass condition>

Execution mode:
- Inline OR batch checkpoints OR subagent-driven-development

Risks:
- ...
```

## Self-Review Checklist

- Every acceptance criterion maps to a task.
- Every task names exact files.
- Every code-changing task has verification.
- No `TODO`, `TBD`, "etc", "similar", or vague "handle edge cases".
- Names, types and paths are consistent across tasks.
- Plan does not include unrelated refactors.
