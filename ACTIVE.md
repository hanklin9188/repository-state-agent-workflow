# Active Handoff

## Repository

Branch: main
HEAD: resolve with `git rev-parse HEAD`
Status: RSAW 0.3 runtime-supervisor release candidate

## Workstream

ID: W-003
Spec: docs/workstreams/W-003-runtime-supervisor-release.md

## Context Epoch

ID: E-004-runtime-evaluation
Role: Reviewer

## Active Task

ID: T-004
Spec: docs/tasks/T-004-runtime-supervisor-evaluation.md

## Current State

- RSAW 0.3 implements an optional Codex Runtime Supervisor.
- CONTINUE reuses a thread; ROTATE starts a fresh thread automatically.
- PAUSE is reserved for human/external gates; COMPLETE is terminal.
- Runtime safety, token accounting, failure semantics, tests, and documentation are present.
- Prospective adoption measurement remains the next evidence step.

## Evidence

- Runtime implementation: `src/repo_state_agent/runtime/`
- Runtime tests: `tests/test_runtime_supervisor.py`
- Release notes: `docs/releases/rsaw-v3-runtime-supervisor.md`
- Evaluation method: `docs/runtime-evaluation.md`
- EdgeFlow replay: `docs/case-studies/edgeflow-rsaw-v1-v2.md`

## Required Reads

- AGENTS.md
- ACTIVE.md
- docs/tasks/T-004-runtime-supervisor-evaluation.md

## Do Not Preload

- all historical release reports;
- complete CI logs;
- every example repository;
- archived handoffs;
- raw runtime event streams unless a test fails.

## Human Gate

None.

## Running or Pending External Work

None.

## Blockers

None.

## Next Exact Action

Run a controlled, non-destructive Codex supervisor pilot and record prospective
turn, rotation, token, checkpoint, and quality outcomes.

## Stop Condition

The runtime release candidate is independently reviewed and the prospective
measurement task is ready.

## Continuation Gate

Decision: ROTATE_REQUIRED
Reason: IMPLEMENTATION_TO_PROSPECTIVE_EVALUATION_BOUNDARY

## Next Task

ID: T-005
Spec: docs/tasks/T-005-runtime-supervisor-prospective-study.md

## Next Session Role

Analyst

## Recommended Reasoning

Medium

## Last Updated

2026-08-14 — RSAW 0.3 runtime-supervisor release candidate
