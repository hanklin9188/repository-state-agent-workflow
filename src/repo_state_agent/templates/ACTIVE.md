# Active Handoff

## Repository

Branch: resolve with `git branch --show-current`
HEAD: resolve with `git rev-parse HEAD`
Status: Bootstrap workstream

## Workstream

ID: W-000
Spec: docs/workstreams/W-000-bootstrap.md

## Context Epoch

ID: E-000-bootstrap
Role: Builder

## Active Task

ID: T-000
Spec: docs/tasks/T-000-bootstrap.md

## Current State

- Repository initialized for RSAW.
- v0.6 supervised mode delegates durable advancement to the Supervisor.

## Evidence

None yet.

## Required Reads

- AGENTS.md
- ACTIVE.md
- docs/tasks/T-000-bootstrap.md

## Context Contract

Mode: FRESH
Stable Prefix: AGENTS.md
Budget: `.rsaw/config.json`

## Human Gate

None.

## Running or Pending External Work

None.

## Blockers

None.

## Next Exact Action

Execute the bootstrap task through its acceptance criteria.

## Stop Condition

Bootstrap task is validated and a durable checkpoint can be sealed.

## Continuation Gate

Decision: ROTATE_REQUIRED
Reason: BOOTSTRAP_FRESH_CONTEXT

## Next Task

ID: T-000
Spec: docs/tasks/T-000-bootstrap.md

## Next Session Role

Builder

## Recommended Reasoning

Medium

## Last Updated

Initialized by RSAW v0.6.
