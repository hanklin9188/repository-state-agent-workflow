# Continuation Gate

The Continuation Gate decides whether the next task may reuse the current context epoch.

## ACTIVE.md contract

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

## Decisions

### `CONTINUE_ALLOWED`

A project-level proposal to keep the context.

The CLI still forces rotation when:

- the next task is missing;
- the role changes;
- a human gate is active.

### `ROTATE_REQUIRED`

Checkpoint and start a fresh context.

Use for role changes, scientific boundaries, major debugging residue, specification changes, or context pressure.

### `STOP_REQUIRED`

The workflow cannot continue autonomously. Typical reasons are interactive privilege, exact formal authorization, destructive action, missing credential, or external work.

## Evaluate the gate

```bash
rsaw next .
```

Example output:

```text
CONTINUE
Reason: SAME_EPOCH
Next task: T-109 (docs/tasks/T-109-readiness.md)
Next role: Builder
```

Or:

```text
ROTATE_REQUIRED
Reason: ROLE_CHANGE
Next role: Reviewer
```

## Deterministic scope

The CLI is intentionally conservative. It does not inspect hidden model context or infer semantic similarity from embeddings. The repository declares the intended continuation; deterministic safety rules constrain it.

A future evaluation may compare explicit gates, fixed-N rotation, always-fresh, and always-persistent workflows. Until then, the gate is an auditable operating contract—not a learned optimizer.
