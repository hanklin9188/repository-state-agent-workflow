# FAQ

## Does the Live Console save tokens?

No. It is local presentation. Context efficiency comes from repository-backed state,
minimal ordered reads, bounded epochs, continuation discipline, and rotation.

## Is more cached input always better?

No. Cached context is useful only while it remains relevant. RSAW balances cache reuse
against stale-context carryover and fresh-input pressure.

## What does Context Pressure mean?

It is latest-turn input relative to RSAW's configured hard rotation threshold. It is
not the model's complete context-window utilization.

## Why use both stable and dynamic fingerprints?

They let a continued thread avoid reloading unchanged policy while still refreshing
`ACTIVE.md`, the active task, and bounded evidence.

## Will 0.5 break a 0.4 config?

The flat `rotate_input_tokens` field remains supported. New nested configuration is
recommended but not mandatory.

## Should strict context budgets be enabled immediately?

No. Inspect real task plans first, calibrate the budget, then enable strict enforcement.

## Can two Codex sessions use the same repository?

Read-only inspection is possible, but only one supervisor/writer should own the active
workstream. The runtime lock prevents a second supervisor.
