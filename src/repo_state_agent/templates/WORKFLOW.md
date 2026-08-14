# Repository-State Workflow

1. Read `AGENTS.md`, `ACTIVE.md`, and the active task.
2. Expand context only when the task requires exact evidence.
3. Execute the bounded task and run V0/V1 validation.
4. Persist a durable checkpoint and update `ACTIVE.md`.
5. Run `rsaw next .`.
6. Continue only when the gate returns `CONTINUE`; otherwise rotate or stop.
7. Use V2 once at context-epoch closure and V3 only for critical independent review.

A workstream is long-lived. A model context is not. Formal execution, scientific analysis, fresh review, human gates, and long-running-only waits are hard rotation boundaries.
