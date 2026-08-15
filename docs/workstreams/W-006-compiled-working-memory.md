# W-006 — Compiled Working Memory Runtime

## Objective

Deliver RSAW v0.6 as the full architectural response to the v3 matched-evaluation failure mechanisms while preserving v0.5 compatibility and keeping empirical claims evidence-gated.

## State Machine

```text
Design → Implement → Validate → Release → Prospective Study
```

## Required capabilities

1. Supervisor-owned bookkeeping.
2. Typed checkpoint result.
3. Immutable checksummed checkpoint.
4. Semantic Capsule.
5. Context Compiler.
6. Evidence handles and read-if-changed.
7. Delta-oriented continuation.
8. Deterministic gate.
9. Token Governor with CONTINUE / COMPACT / ROTATE / PAUSE / COMPLETE.
10. Bounded independent reviewer.
11. Model/tool/repeated/evidence/occupancy telemetry.
12. Live terminal observability for the v0.6 semantics.
13. Worktree-safe v0.5 migration.
14. Short / medium / long evaluation infrastructure.

## Claim boundary

Implementation validation and synthetic lifecycle tests do not prove causal token or semantic-success improvement. Real promotion requires matched prospective evidence.
