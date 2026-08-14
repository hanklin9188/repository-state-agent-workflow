# W-000 — Bootstrap Workstream

## Goal

Move project continuity from conversation history into versioned repository state.

## Outcome

A stable agent policy, compact active handoff, bounded task contracts, and an explicit context-rotation policy.

## State Machine

```text
T-000 Bootstrap
→ T-001 First real task
→ project-defined phases
```

## Continuation Policy

Continue within one context epoch only when the next task is ready and shares the same role, hypothesis, subsystem, and evidence domain.

Rotate for role changes, scientific execution/analysis boundaries, major debugging residue, long-running waits, human gates, or context pressure.

## Validation Budget

V0 during edits, V1 at task checkpoints, V2 once at epoch closure, and V3 only for critical work.

## Human Gates

- interactive privilege or credentials;
- formal authorization;
- unresolved architecture/scientific fork;
- destructive action.

## Workstream Stop

The project-defined milestone is complete and a new workstream is activated.
