# Repository-State Workflow

1. Read `AGENTS.md`, `ACTIVE.md`, and the active task.
2. Execute one durable task checkpoint with progressive disclosure.
3. Use V0/V1 during work and V2 once at epoch closure.
4. Update `ACTIVE.md` with evidence and the next transition.
5. Let the RSAW supervisor apply `CONTINUE`, `ROTATE`, `PAUSE`, or `COMPLETE`.

Run manually with `rsaw prompt .`, or supervise Codex automatically with `rsaw run . --agent codex`.
