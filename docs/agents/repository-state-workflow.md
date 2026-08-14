# Repository-State Workflow

Use the repository as the persistent memory system.

## Bootstrap

Read only `AGENTS.md`, `ACTIVE.md`, and the active task.

## Work

Use progressive disclosure and execute the bounded task.

## Checkpoint

Persist evidence, update the task and ACTIVE, activate the next task, and run:

```bash
rsaw verify .
rsaw next .
```

## Gate

- `CONTINUE`: stay in the current context epoch.
- `ROTATE_REQUIRED`: stop and resume fresh.
- `STOP_REQUIRED`: preserve state and wait for the hard gate.

Never continue across a role change, formal execution/analysis boundary, major decision, or long-running-only wait.
