# Loop Patterns

Этот reference нужен, когда loop длится больше одной-двух итераций или когда нужно явно оформить ledger, evidence report
или stopping rules.

## Что Взято Из Внешних Подходов

- Простые workflows предпочтительнее сложного агента, если задачу можно разложить на понятные шаги. Это соответствует
  подходу Anthropic "Building effective agents": начинать с простых patterns и добавлять agent complexity только когда
  она действительно нужна.
- Полезный loop имеет evaluator/optimizer форму: сгенерировать или изменить slice, проверить его, использовать feedback
  для следующего slice.
- Repair loop должен превращать ошибки в проверяемую обратную связь: failing output, diagnostics, обновленный artifact
  или проверку.
- Human gate нужен там, где автоматизация еще не заслужила доверие: scope change, destructive action, publish, unclear
  repeated failure, production-side effects.

Reviewed sources:

- Anthropic, "Building effective agents": https://www.anthropic.com/engineering/building-effective-agents
- OpenAI Codex, "Agent Skills": https://developers.openai.com/codex/skills
- OpenAI Codex cookbook links from the skills page: "Build an Agent Improvement Loop with Traces, Evals, and Codex" and
  "Build iterative repair loops with Codex".

## Loop Contract Template

```markdown
## Loop Contract

- Goal:
- Scope:
- Max iterations/time/budget from user request:
- Forbidden actions:
- Baseline command:
- Per-iteration command:
- Final verification:
- Ledger/report location:
```

## Iteration Ledger Template

```markdown
| Iteration | Slice | Change | Command | Result | Evidence | Next |
| --- | --- | --- | --- | --- | --- | --- |
| 1/N |  |  |  | passed / failed / blocked / no-signal |  |  |
```

## Failure Evidence Template

```markdown
### Finding: <short name>

- Surface:
- Minimal input:
- Expected:
- Observed:
- Failure layer:
- Repro command:
- Artifact:
- New information:
- Next action:
```

## Slice Selection Heuristics

Prefer a slice when it:

- adds a new fact, boundary, improvement or regression signal;
- is small enough to finish in one iteration;
- has a clear check, review criterion or oracle;
- can produce useful evidence whether it passes or fails;
- does not require broad refactor;
- does not depend on unresolved root cause from a previous slice.

Avoid a slice when it:

- duplicates an already known failure;
- requires weakening an oracle to pass;
- combines too many unknowns;
- depends on external state that cannot be verified;
- would make the loop continue only because the limit has not been reached.

## Result Classification

- `passed`: change passed the intended check and added confirmed capability, improvement or broader explored surface.
- `failed`: check failed and produced useful evidence.
- `blocked`: required dependency, permission, artifact, service or user decision is missing.
- `no-signal`: iteration did not add information; change axis or stop.

For domain-specific policy, switch to the relevant skill. Examples: `autotest-engineer` for test signal policy,
`technical-writer` for docs deliverables, `systematic-debugging` for root cause work, `source-driven-development` for
fresh external sources.

## Stopping Rules

Stop when:

- iteration/time/budget limit is reached;
- same blocker repeats three times;
- next useful step is outside agreed scope;
- failures are duplicates without new information;
- verification cannot distinguish improvement from noise;
- context handoff is needed before continuing;
- the next step requires user/product decision.

## Final Summary Template

```markdown
Loop completed: <done>/<limit>

Findings:
- ...

Artifacts changed:
- ...

Verification:
- `<command>` -> pass/fail

Stopped because:
- ...

Next front:
- ...
```
