# Active Handoff

## Repository

Branch: main
HEAD: UNKNOWN
Status: inspect before work

## Workstream

ID: W-000
Spec: docs/workstreams/W-000-bootstrap.md

## Context Epoch

ID: E-000
Role: Builder

## Active Task

ID: T-000
Spec: docs/tasks/T-000-bootstrap.md

## Current State

- RSAW has been initialized.
- Project policy and the first real workstream task still need review.

## Evidence

- Repository root identified.

## Required Reads

- AGENTS.md
- ACTIVE.md
- docs/tasks/T-000-bootstrap.md

## Do Not Preload

- full repository tree;
- historical logs;
- all decisions;
- archived handoffs.

## Human Gate

None.

## Running or Pending External Work

None.

## Blockers

None.

## Next Exact Action

Customize policy, define the real workstream, and activate the first real task.

## Stop Condition

Project policy, workstream, and first task are actionable and `rsaw verify .` passes.

## Continuation Gate

Decision: ROTATE_REQUIRED
Reason: Bootstrap policy changes should hand off to a fresh project context.

## Next Task

None.

## Next Session Role

Builder

## Recommended Reasoning

Medium

## Last Updated

INITIALIZED
