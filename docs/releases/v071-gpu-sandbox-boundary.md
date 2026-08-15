# RSAW v0.7.1 — GPU Sandbox Boundary Repair

v0.7.1 is a safety and operator-semantics patch release derived from a real EdgeFlow GPU sandbox incident.

## Fixed

- Per-turn task sandbox resolution using the current `RSAW_TASK_ID`.
- Automatic fresh rotation across sandbox-class changes.
- Durable task/sandbox/source telemetry.
- Mandatory reasons and content-bound audit records for sandbox set/clear.
- Transactional rollback when an operator audit cannot be written.
- Clean default process exits for expected non-TUI operator states.
- Explicit `rsaw --version` output to diagnose launcher drift.
- Next-phase-based 4/16/64 synthetic lifecycle acceptance.

## Preserved

- Repository default `workspace-write`.
- Explicit task scope for `danger-full-access`.
- Strict machine exit codes through `--strict-exit-codes`.
- Fail-closed experiment readiness and evidence boundaries.
- No conversion of capability smoke into scientific evidence.

See the [incident record](../incidents/2026-08-15-edgeflow-gpu-sandbox.md) and [EdgeFlow deployment guide](../edgeflow-v071-deployment.md).
