# Active Handoff

## Repository

Branch: resolve with `git branch --show-current`
HEAD: resolve with `git rev-parse HEAD`
Status: RSAW 0.6 compiled-working-memory release candidate

## Workstream

ID: W-006
Spec: docs/workstreams/W-006-compiled-working-memory.md

## Context Epoch

ID: E-010-v06-review
Role: Reviewer

## Active Task

ID: T-010
Spec: docs/tasks/T-010-v06-validation.md

## Current State

- Supervisor-owned bookkeeping is implemented in the v0.6 runtime path.
- Typed checkpoint results, Semantic Capsule, Context Compiler, evidence handles, deterministic gate, and Token Governor are implemented.
- COMPACT and ROTATE have distinct semantics.
- Aggregate provider input is not used as context occupancy.
- v0.5 remains available to unmigrated repositories through the compatibility dispatcher.
- Public causal token/success claims remain unpromoted until matched prospective evaluation.

## Evidence

- Runtime: `src/repo_state_agent/runtime/v6.py`
- Compatibility CLI: `src/repo_state_agent/v6_cli.py`
- Live Console: `src/repo_state_agent/runtime/tui/v6.py`
- Tests: `tests/test_v6_runtime.py`, `tests/test_v6_tui.py`
- Architecture: `docs/v06-context-operating-system.md`
- Migration: `docs/edgeflow-v06-migration.md`

## Required Reads

- AGENTS.md
- ACTIVE.md
- docs/tasks/T-010-v06-validation.md
- docs/v06-context-operating-system.md

## Context Contract

Mode: REVIEW
Stable Prefix: AGENTS.md
Budget: `.rsaw/config.json`

## Do Not Preload

- historical v3/v4/v5 release logs;
- raw CI logs unless a check fails;
- unrelated case-study data;
- complete agent event streams unless investigating a telemetry failure.

## Human Gate

None.

## Running or Pending External Work

GitHub CI and independent release validation after the implementation commit.

## Blockers

None.

## Next Exact Action

Run the full cross-version validation matrix, inspect failures, validate package build and v0.6 CLI/migration behavior, and review documentation/visual surfaces.

## Stop Condition

Ruff, pytest, repository verification, FRESH context compilation, v0.6 dry-run, 4/16/64 lifecycle acceptance, Markdown links, and package build pass on supported CI versions.

## Continuation Gate

Decision: ROTATE_REQUIRED
Reason: IMPLEMENTATION_TO_INDEPENDENT_VALIDATION_BOUNDARY

## Next Task

ID: T-011
Spec: docs/tasks/T-011-v06-prospective-study.md

## Next Session Role

Runner

## Recommended Reasoning

Medium

## Last Updated

2026-08-15 — RSAW 0.6 compiled-working-memory release candidate
