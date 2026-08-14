# T-003 — Freeze RSAW 0.2 Context-Epoch Evaluation

## Workstream

W-002 — Context Epoch Evaluation

## Goal

Create a prospective matched evaluation for RSAW 0.2.

## Scientific Question

When does retaining context across adjacent tasks improve token efficiency and task closure relative to always-fresh and always-persistent workflows?

## In Scope

- define matched task streams;
- define three workflow conditions;
- freeze rotation rules;
- define token, quality, review, intervention, and time metrics;
- define claim boundaries and result semantics;
- specify machine-readable output.

## Out of Scope

- running the study;
- claiming measured RSAW 0.2 savings;
- building a learned context-rotation model;
- adding an orchestration platform.

## Acceptance Criteria

- unit of analysis is explicit;
- matched conditions are reproducible;
- provider accounting limitations are explicit;
- quality and successful closure are primary constraints;
- analysis and stopping rules are prospective;
- `rsaw verify .` passes.

## Validation

Decision/spec review only. No broad implementation validation is required.

## Stop Condition

The protocol is frozen and T-004 instrumentation is ready.
