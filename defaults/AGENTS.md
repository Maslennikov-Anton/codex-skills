# Local working agreements

## Truthful tests

- Before writing/changing tests, investigating a failing test, or changing test selection/CI reporting, read `/home/ant/codex-skills/autotest-engineer/references/test-integrity.md`. Preserve the agreed contract, artifact identity, original exit codes and failed/broken statuses.
- A supported product defect must leave its positive test failed. Do not weaken assertions/inputs, remove coverage, add skip/xfail/quarantine, mock the tested boundary, swallow errors or introduce a green wrapper to obtain a passing result. Repo exception mechanisms do not grant permission to hide a new defect.
- A wrong test/harness may be fixed with independent contract evidence and an explicit before/after explanation. Testing can be complete with defects found; report product results, run completeness and CI/publication health separately. Do not claim a product fix without evidence on the fixed artifact.
- Before edits in an existing test project, snapshot the working-tree test/CI surfaces with the helper from that reference; review every reported change and the full relevant diff. Do not replace the baseline after changing the checks.

## Temporary artifacts

- Before creating disposable analysis/pilot/test files, read `/home/ant/codex-skills/artifact-lifecycle/SKILL.md`. Use one owned workspace per task, put intermediates in scratch and compact reports/minimal repro/raw failure evidence in evidence.
- At task completion, preview and clean only that task's disposable files after retaining evidence. This is the user's default; a separate cleanup request is unnecessary within that scope. Preserve incomplete investigations and user deliverables, and state the path/reason for retained runs.
- Name, age and `.gitignore` do not prove safe deletion. Do not clean arbitrary `/tmp`, project environments/products, user data, credentials, chat history, memories, VPN state or another task's resources. Managed worktrees use their native lifecycle.
