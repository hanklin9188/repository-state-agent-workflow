# Session Lifecycle

RSAW 0.2 separates task checkpoints from context rotation.

```mermaid
flowchart TD
    N[New or continuing context epoch]
    R[Read AGENTS + ACTIVE + active task]
    Q{Need more context?}
    D[Read exact dependency]
    X[Execute task]
    V0[V0/V1 targeted validation]
    K[Durable task checkpoint]
    G{Continuation Gate}
    C[Activate next adjacent task]
    V2[V2 epoch/phase closure]
    S[Stop and rotate]
    H[Stop at human/external gate]

    N --> R --> Q
    Q -->|Yes| D --> X
    Q -->|No| X
    X --> V0 --> K --> G
    G -->|CONTINUE| C --> X
    G -->|ROTATE_REQUIRED| V2 --> S
    G -->|STOP_REQUIRED| H
```

## Checkpoint after every task

Even when the context continues:

- accepted evidence is persisted;
- the current task is closed or updated;
- the next task is activated;
- `ACTIVE.md` is updated;
- `rsaw verify .` and `rsaw next .` run.

## Continue when

The next task shares the role, objective, subsystem, and evidence domain, and no independent review or human gate is required.

## Rotate when

- role changes;
- scientific phase changes;
- major debugging residue exists;
- the specification changed;
- long-running work is the only blocker;
- context pressure is high;
- a human gate is reached.

The boundary is both a quality mechanism and a context-cost mechanism.
