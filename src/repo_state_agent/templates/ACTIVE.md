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

- RSAW workstream files have been initialized.
- Project-specific policy and the first real task still need review.

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

Customize AGENTS.md, define the real workstream, and replace T-000 with the first real task.

## Stop Condition

Project policy, workstream, and the first real task are actionable and `rsaw verify .` passes.

## Continuation Gate

Decision: ROTATE_REQUIRED
Reason: Bootstrap changes repository policy and should hand off to a fresh project task.

## Next Task

None.

## Next Session Role

Builder

## Recommended Reasoning

Medium

## Last Updated

INITIALIZED
