# Active Handoff

## Repository

Branch: main
HEAD: resolve with `git rev-parse HEAD`
Status: RSAW 0.2 persistent-workstream implementation prepared

## Workstream

ID: W-002
Spec: docs/workstreams/W-002-context-epoch-evaluation.md

## Context Epoch

ID: E-003-evaluation-design
Role: Decision

## Active Task

ID: T-003
Spec: docs/tasks/T-003-context-epoch-evaluation.md

## Current State

- RSAW 0.2 adds persistent workstreams, context epochs, checkpoints, and a deterministic continuation gate.
- The default scaffold is plug-and-play and remains backward compatible with RSAW 0.1 repositories.
- CLI support includes `status`, `next`, `checkpoint`, and automatic role-aware prompts.
- English and Traditional Chinese first-screen documentation now explain setup and operation.
- The next claim must be evidence-based: RSAW 0.2 token and quality effects are not yet measured.

## Evidence

- RSAW 0.1 bootstrap case study: `data/case-studies/desk-code-agent-rsaw-v1.json`.
- RSAW 0.2 design docs: `docs/context-epochs.md` and `docs/continuation-gate.md`.

## Required Reads

- AGENTS.md
- ACTIVE.md
- docs/tasks/T-003-context-epoch-evaluation.md

## Do Not Preload

- all example repositories;
- complete documentation tree;
- publication history;
- archived handoffs;
- unrelated implementation internals.

## Human Gate

None.

## Running or Pending External Work

None.

## Blockers

No matched RSAW 0.2 evaluation has been run.

## Next Exact Action

Freeze a matched evaluation comparing always-persistent, RSAW 0.1 always-fresh, and RSAW 0.2 adaptive context epochs.

## Stop Condition

The evaluation protocol, unit of analysis, quality metrics, token metrics, and claim boundaries are prospectively frozen.

## Continuation Gate

Decision: ROTATE_REQUIRED
Reason: The public implementation boundary is complete; the next task is a fresh scientific design phase.

## Next Task

None.

## Next Session Role

Decision

## Recommended Reasoning

Medium

## Last Updated

2026-08-14 — RSAW 0.2 persistent-workstream redesign
