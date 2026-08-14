# Runtime Supervisor

RSAW supervises a persistent repository workstream while Codex contexts remain bounded.

## Start

```bash
rsaw verify .
rsaw context .
rsaw doctor . --agent codex
rsaw run . --agent codex
```

## Per-turn contract

Each supervised turn must complete exactly one durable checkpoint. RSAW then verifies:

1. adapter success;
2. `ACTIVE.md` advancement;
3. repository validity;
4. context-plan validity/warnings;
5. the next continuation action;
6. runtime rotation pressure.

## Context lifecycle

- Fresh epoch: full ordered minimal bootstrap.
- Continued epoch: reread dynamic authority; reuse unchanged stable policy.
- Rotation: clear the thread and begin another fresh epoch.

## Failure semantics

RSAW fails closed. It does not retry failed agent or formal turns automatically, invent
approval, or let presentation errors affect execution.

## Runtime evidence

`.rsaw/runtime/<run-id>/` contains summary JSON, supervisor JSONL, Codex events, and the
last message. `rsaw report .` derives checkpoint-normalized context metrics.
