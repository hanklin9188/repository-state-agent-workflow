# T-000 — Bootstrap task

## Objective

Replace this bootstrap objective with one bounded engineering or research task.

## Acceptance Criteria

- The requested semantic change is complete.
- Required validation has actually executed.
- Durable evidence is available for the checkpoint.

## Allowed Writes

- src/**
- tests/**
- docs/**

Adjust this list before execution. The deterministic Supervisor gate enforces it when present.

## Forbidden Operations

- destructive Git cleanup of unrelated work;
- credential/authorization inference;
- bypassing the configured sandbox;
- model-owned edits to `ACTIVE.md` while supervised execution is active;
- model invocation of `advance.py` while supervised execution is active.

## Required Reads

Use the compiled Context Envelope first. Add only exact files needed by this task.

## Validation

- `python -m pytest -q`

Replace the example with deterministic commands appropriate for the task. RSAW can verify that configured validation commands appeared in the agent event stream.

## Artifacts

Record required artifact paths and checksums in the typed checkpoint result.

## Next Task

The supervised agent reports `nextTask` and optional `followingTask` in `rsaw.checkpoint-result.v1`; the Supervisor validates readiness before advancing.

## Stop Condition

Acceptance criteria and deterministic gate pass.
