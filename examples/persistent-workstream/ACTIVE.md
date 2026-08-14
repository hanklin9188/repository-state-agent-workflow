# Active Handoff

## Workstream
ID: W-001
Spec: docs/workstreams/W-001-checkout.md

## Context Epoch
ID: E-001-checkout-build
Role: Builder

## Active Task
ID: T-001
Spec: docs/tasks/T-001-checkout-implementation.md

## Current State
- Checkout contract is frozen.
- Implementation has not started.

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/T-001-checkout-implementation.md

## Next Exact Action
Implement the checkout service and focused tests.

## Stop Condition
The implementation task is checkpointed and T-002 is active.

## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: T-002 remains in the same Builder role and checkout subsystem.

## Next Task
ID: T-002
Spec: docs/tasks/T-002-checkout-smoke.md

## Human Gate
None.

## Next Session Role
Builder

## Recommended Reasoning
Medium
