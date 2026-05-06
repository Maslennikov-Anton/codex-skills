# Execution Checklist

## Before Starting

- [ ] Plan file or plan text read completely.
- [ ] Exact tasks identified.
- [ ] File ownership and risky shared files understood.
- [ ] Verification commands found.
- [ ] Placeholders scanned: `TODO`, `TBD`, "etc", "similar", vague "handle edge cases".
- [ ] Critical gaps raised before implementation.

## Per Task

```markdown
Task: <name>
Status: pending/in_progress/done/blocked
Files:
- ...
Verification:
- Command: `<command>`
- Result: pass/fail/not run
Notes:
- ...
```

## Blocker Report

```markdown
Blocked at task <N>: <name>.

Reason:
- ...

Evidence:
- Command/output/path.

Needed decision:
- ...
```

## Completion Report

```markdown
Plan:
- ...

Completed tasks:
- ...

Verification:
- `<command>` -> pass/fail/not run

Not verified:
- ...

Residual risks:
- ...
```
