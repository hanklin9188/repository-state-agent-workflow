# T-000 — Bootstrap Repository-State Workflow

## Workstream

W-000 — Bootstrap

## Goal

Customize RSAW for this repository and define the first real task.

## Why

Long-lived project continuity belongs in the repository; model context should remain bounded.

## Role

Builder

## Blocked By

None.

## Inputs and Authority

- existing repository documentation;
- build and test commands;
- current project priorities.

## In Scope

- customize AGENTS.md;
- update the workstream contract;
- update ACTIVE.md;
- define the first real task;
- choose whether the next checkpoint can continue or must rotate.

## Out of Scope

- implementing the product feature itself;
- rewriting all existing documentation.

## Acceptance Criteria

- AGENTS.md contains stable project policy;
- ACTIVE.md is compact and actionable;
- workstream spec exists;
- active task exists;
- continuation decision is explicit;
- `rsaw verify .` passes.

## Targeted Validation

```bash
rsaw verify .
rsaw status .
rsaw next .
```

## Evidence Expected

A clean diff and verified active handoff.

## Continuation Candidate

Rotate after bootstrap because the next task establishes real project work.

## Stop Condition

The first real task is ready for a fresh builder context.

## Next Dependency if Complete

The first project task.
