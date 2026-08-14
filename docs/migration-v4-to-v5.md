# Migration 0.4 → 0.5

## Compatibility

RSAW 0.5 accepts the 0.4 flat `rotate_input_tokens` configuration. Existing repositories
do not require `rsaw init --force`.

## Recommended update

1. Upgrade the package.
2. Run `rsaw verify .`.
3. Run `rsaw context .` and inspect the plan.
4. Add nested `rotation` and `context` settings when ready.
5. Preview the console.
6. Run a non-destructive pilot before changing production thresholds.

```bash
python -m pip install --upgrade   git+https://github.com/hanklin9188/repository-state-agent-workflow.git

rsaw verify .
rsaw context .
rsaw preview .
rsaw run . --dry-run
```

## Do not

- use `rsaw init --force` on a customized repository;
- enable strict context budgets before measuring existing task sizes;
- assume the default rotation thresholds are optimal;
- hot-upgrade a supervisor process that already owns the repository.
