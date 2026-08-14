# Migration from RSAW 0.1 to 0.2

RSAW 0.2 is backward compatible. Existing repositories continue to behave as always-fresh workflows because missing continuation metadata defaults to `ROTATE_REQUIRED`.

## Minimal migration

### 1. Add a workstream spec

```text
docs/workstreams/W-001-current.md
```

Record the long-range goal, state machine, human gates, validation budget, and stop condition.

### 2. Add workstream and epoch fields to ACTIVE.md

```markdown
## Workstream
ID: W-001
Spec: docs/workstreams/W-001-current.md

## Context Epoch
ID: E-001-build
Role: Builder
```

### 3. Add the continuation gate

```markdown
## Continuation Gate
Decision: ROTATE_REQUIRED
Reason: Start conservatively; enable continuation after the next task is ready.
```

### 4. Add a next task when continuation is allowed

```markdown
## Next Task
ID: T-002
Spec: docs/tasks/T-002.md
```

### 5. Verify

```bash
rsaw verify .
rsaw status .
rsaw next .
```

## Recommended rollout

1. Keep `ROTATE_REQUIRED` for critical, review, and scientific boundaries.
2. Enable `CONTINUE_ALLOWED` first for tightly coupled Builder tasks.
3. Measure repeated reads, context size, task completion, and review defects.
4. Expand only when the observed workflow remains reliable.

## What not to migrate

Do not copy project history into the workstream or `ACTIVE.md`. Existing ADRs, Issues, reports, and Git history should remain canonical and be referenced by path.
