# Active Handoff

## Repository
Branch: migration/events-v3
HEAD: 789abc
Status: clean

## Active Milestone
Events schema v3

## Active Task
ID: D-018
Spec: docs/tasks/D-018-dual-write.md

## Current State
- New schema validated.
- Dual-write code not implemented.

## Verified Preconditions
- Migration plan accepted.

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/D-018-dual-write.md

## Do Not Preload
- historical warehouse dumps;
- unrelated pipeline logs.

## Running or Pending External Work
None.

## Blockers
None.

## Next Exact Action
Implement idempotent dual-write with a feature flag.

## Stop Condition
Focused integration and full pipeline tests pass.

## Next Session Role
Builder

## Recommended Reasoning
Medium

## Last Updated
2026-08-12 — 789abc
