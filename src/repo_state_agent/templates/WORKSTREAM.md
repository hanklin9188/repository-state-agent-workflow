# W-000 — Bootstrap Workstream

## Goal

Move project continuity from conversation history into versioned repository state.

## Outcome

A stable policy, compact active handoff, bounded task contracts, explicit rotation rules, and an optional runtime supervisor.

## State Machine

```text
T-000 Bootstrap
→ T-001 First real task
→ project-defined phases
→ COMPLETE
```

## Continuation Policy

Continue only for the same role, objective, subsystem, evidence domain, and safety boundary. Rotate for role/scientific boundaries or context pressure. Pause only for human/external gates.

## Validation Budget

V0 during edits, V1 at task checkpoints, V2 once at epoch closure, V3 only for critical work.

## Human Gates

- interactive privilege or credentials;
- formal authorization;
- unresolved architecture/scientific fork;
- destructive action.

## Runtime Limits

The supervisor must enforce bounded turns, token pressure rotation, no automatic retry after agent failure, and single-supervisor locking.

## Workstream Stop

The project-defined milestone is complete and `ACTIVE.md` declares `COMPLETE`.
