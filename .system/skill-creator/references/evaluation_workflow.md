# Skill Evaluation Workflow

Use this reference when a skill needs more than structural validation. The goal is to learn whether the skill changes agent behavior in a useful, generalizable way.

## When to Evaluate

Run lightweight evals when:

- the skill encodes a multi-step workflow;
- the skill enforces discipline under pressure;
- output quality can be judged against concrete expectations;
- the skill includes scripts or references that should change behavior;
- the skill competes with adjacent skills and needs clear trigger boundaries;
- a revision may regress an existing skill.

Skip formal evals when the change is tiny, obvious, and already covered by `quick_validate.py`.

## Eval Set

Create `evals/evals.json` inside the skill:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": "realistic-flow",
      "prompt": "User-like task prompt",
      "expected_output": "Observable result that should be produced",
      "files": [],
      "assertions": [
        "The output includes the required section",
        "The answer cites the specific source file"
      ]
    }
  ]
}
```

Keep prompts realistic. Good prompts include paths, concrete constraints, user intent, and ambiguity that a real task would contain.

## Pressure Scenarios

Use pressure scenarios for skills that prevent shortcuts, rationalizations, or premature claims.

Good pressure prompts combine:

- time pressure or impatience;
- a tempting partial check;
- stale evidence from an earlier run;
- a user asking for speed over rigor;
- ambiguous success language such as "looks fixed" or "should pass";
- delegated-agent reports that still need independent verification.

Success means the agent follows the skill despite the pressure and states actual status from evidence.

## Baseline Comparison

Choose one baseline:

- `without_skill`: for a brand-new skill.
- `old_skill`: for improving an existing skill. Snapshot the old directory before editing.
- `previous_iteration`: when iterating after user feedback.

Compare:

- task completion;
- correctness;
- evidence quality;
- unnecessary work;
- token/time cost when available.

## Workspace Layout

Use a sibling workspace:

```text
example-skill-workspace/
└── iteration-1/
    └── realistic-flow/
        ├── eval_metadata.json
        ├── with_skill/
        │   └── outputs/
        └── baseline/
            └── outputs/
```

Create it with:

```bash
python scripts/init_eval_workspace.py /path/to/example-skill --iteration 1
```

## Running Evals

For each eval, run the task once with the skill and once against the baseline. If subagents are available and the user explicitly allowed parallel agent work, launch both runs in the same round. Otherwise run them serially and keep the prompts identical except for skill access.

With-skill prompt shape:

```text
Use $example-skill at /path/to/example-skill to complete this task.
Task: ...
Save outputs to: .../with_skill/outputs/
```

Baseline prompt shape:

```text
Complete this task without using /path/to/example-skill.
Task: ...
Save outputs to: .../baseline/outputs/
```

When improving an existing skill, point the baseline at the snapshot path instead of saying "without using".

## Grading

Prefer programmatic checks for deterministic artifacts. For qualitative outputs, grade inline using the assertions in `evals/evals.json`.

Record a compact result per run:

```json
{
  "passed": true,
  "assertions": [
    {
      "text": "The output includes the required section",
      "passed": true,
      "evidence": "Found section heading in output.md"
    }
  ],
  "notes": "Short explanation of meaningful differences"
}
```

## Description Trigger Evals

Create a small trigger set when description quality matters:

```json
[
  {
    "query": "casual realistic user prompt",
    "should_trigger": true
  },
  {
    "query": "near-miss prompt that mentions similar words but needs another skill",
    "should_trigger": false
  }
]
```

Use 5-10 positive and 5-10 negative prompts. Negative cases should be near misses, not obviously unrelated tasks.

Revise the description when:

- positive prompts require the skill but the description does not mention the intent, file type, tool, or workflow;
- negative prompts share keywords and would likely over-trigger;
- the description only says what the skill is, but not when to use it.
- the description summarizes process steps that belong in the skill body.

## Iteration Rule

After each eval pass:

1. Fix general failure patterns, not just individual prompts.
2. Move repeated mechanics into `scripts/` when multiple evals reinvent the same code.
3. Move rare details into `references/` when they bloat `SKILL.md`.
4. Re-run the same evals and add one new edge case if the failure exposed a missing boundary.
