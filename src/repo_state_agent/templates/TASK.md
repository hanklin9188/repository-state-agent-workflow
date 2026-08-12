# T-000 — Bootstrap Repository-State Workflow

## Goal

Customize the workflow for this repository and define the first real task.

## Why

Fresh agent sessions need explicit policy, current state, and a bounded task contract.

## Blocked By

None.

## Inputs and Authority

- existing repository documentation;
- build and test commands;
- current project priorities.

## In Scope

- customize AGENTS.md;
- update ACTIVE.md;
- choose the canonical task location;
- define the first real task.

## Out of Scope

- implementing the product feature itself;
- rewriting all existing documentation.

## Acceptance Criteria

- AGENTS.md contains stable project policy;
- ACTIVE.md is compact and actionable;
- active task exists;
- `rsaw verify .` passes.

## Targeted Tests

```bash
rsaw verify .
```

## Full Closure Validation

Project-defined.

## Evidence Expected

A clean diff and verified active handoff.

## Stop Condition

The first real task is ready for a fresh builder session.

## Next Dependency if Complete

The first project task.
