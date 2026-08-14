# Continuation and Runtime Actions

`ACTIVE.md` declares repository intent. RSAW applies deterministic safety rules
and derives one runtime action.

## Repository decisions

- `CONTINUE_ALLOWED`
- `ROTATE_REQUIRED`
- `STOP_REQUIRED`
- `COMPLETE`

## Runtime actions

| Action | Meaning |
|---|---|
| `CONTINUE` | resume the current agent thread |
| `ROTATE` | keep the workstream running in a fresh thread |
| `PAUSE` | wait for explicit human/external action |
| `COMPLETE` | terminate the workstream |

## Example

```markdown
## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: Same role, subsystem, objective, and evidence domain.

## Next Task
ID: T-109
Spec: docs/tasks/T-109-readiness.md

## Next Session Role
Builder
```

`CONTINUE_ALLOWED` still rotates when the next task is missing or the role
changes. A Human Gate always pauses.

## Manual inspection

```bash
rsaw next .
```

## Automatic execution

```bash
rsaw run . --agent codex
```

ROTATE is not a workstream stop. The Runtime Supervisor creates the fresh
context. Only PAUSE requires human/external intervention.

## Deterministic scope

RSAW does not use embeddings or hidden model state to guess semantic similarity.
The repository declares intent; deterministic safety constraints and runtime
budgets limit continuation.
