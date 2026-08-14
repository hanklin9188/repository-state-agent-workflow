# T-004 — Runtime Supervisor Evaluation

## Goal

Independently review the RSAW 0.3 supervisor against the ideal workstream
contract before prospective adoption.

## In Scope

- CONTINUE / ROTATE / PAUSE / COMPLETE semantics;
- Codex fresh and resume command construction;
- human-gate handling;
- repository state advancement;
- no-retry failure behavior;
- token/transition accounting;
- context and transition limits;
- CI and documentation consistency.

## Out of Scope

- claiming universal token savings;
- production deployment without a pilot;
- additional agent adapters;
- bypassing Codex sandbox or approval policy.

## Acceptance

- cross-version CI passes;
- deterministic supervisor tests pass;
- `rsaw run . --dry-run` succeeds;
- documentation matches executable behavior;
- unresolved risks are recorded.

## Stop Condition

The release candidate is reviewable and T-005 is ready.
