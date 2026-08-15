# RSAW v0.7.1 — GPU Sandbox Boundary Repair

v0.7.1 is a safety and operator-semantics patch release derived from a real EdgeFlow GPU sandbox incident.

## Fixed

- Per-turn task sandbox resolution using the current `RSAW_TASK_ID`.
- Exact-task scoping for repository profiles and explicit CLI `--sandbox` overrides.
- Automatic fresh rotation across sandbox-class changes, including same-role task transitions.
- Durable task/sandbox/source telemetry and Live Runtime Console visibility.
- Mandatory non-empty reasons and confirmations for sandbox set/clear.
- Operator identity, before/after hashes, and content-bound audit records.
- `rsaw verify` rejection of tampered v2 operator actions, with compatibility warnings for legacy v1 records.
- Transactional rollback when verification or audit persistence fails.
- Clean default shell exits for expected TUI and non-TUI operator states.
- Strict machine exit codes through `--strict-exit-codes`.
- Explicit `rsaw --version` output to diagnose launcher drift.
- Next-phase-based 4/16/64 synthetic lifecycle acceptance.

## Preserved

- Repository default `workspace-write`.
- Explicit task scope for `danger-full-access`.
- Fail-closed experiment readiness and interference checks.
- No conversion of capability smoke into scientific evidence.
- No authorization of an E04 retry or nonce reuse.

## Validation

- Python 3.10, 3.12, and 3.13 CI.
- 107 tests per matrix entry.
- Ruff, compileall, repository/context/CLI/preflight gates.
- 4/16/64 lifecycle acceptance.
- 121 Markdown files checked.
- Isolated wheel, exact-main, and public-tag installation.
- Wheel, source distribution, and SHA-256 manifest published with the GitHub Release.

See the [incident record](../incidents/2026-08-15-edgeflow-gpu-sandbox.md) and [EdgeFlow v0.7.1 deployment guide](../edgeflow-v071-deployment.md).
