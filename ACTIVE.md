# Active Handoff

## Repository

Branch: resolve with `git branch --show-current`
HEAD: resolve with `git rev-parse HEAD`
Status: RSAW 0.5 cache-aware runtime release candidate

## Workstream

ID: W-005
Spec: docs/workstreams/W-005-token-efficient-runtime.md

## Context Epoch

ID: E-008-token-runtime-review
Role: Reviewer

## Active Task

ID: T-008
Spec: docs/tasks/T-008-token-efficient-runtime-validation.md

## Current State

- Ordered context manifests and stable/dynamic fingerprints are implemented.
- Fresh and continued prompts use different read contracts.
- Deterministic rotation includes hard, fresh-input, and low-cache-reuse pressure.
- Runtime reports expose fresh input and checkpoint-normalized efficiency.
- Live Console visuals and public documentation reflect the 0.5 architecture.
- Causal token and quality claims remain unpromoted pending matched evaluation.

## Evidence

- Context planner: `src/repo_state_agent/runtime/context.py`
- Rotation policy: `src/repo_state_agent/runtime/rotation.py`
- Supervisor integration: `src/repo_state_agent/runtime/supervisor.py`
- CLI/report integration: `src/repo_state_agent/cli.py`, `src/repo_state_agent/runtime/report.py`
- Tests: `tests/test_context_plan.py`, `tests/test_rotation_policy.py`
- Design: `docs/token-efficient-runtime.md`

## Required Reads

- AGENTS.md
- ACTIVE.md
- docs/tasks/T-008-token-efficient-runtime-validation.md

## Context Contract

Mode: BOUNDED
Stable Prefix: AGENTS.md
Budget: `.rsaw/config.json`

## Do Not Preload

- archived release reports;
- raw CI logs unless a check fails;
- all case-study data;
- full Codex event streams.

## Human Gate

None.

## Running or Pending External Work

GitHub CI and operator preview after the implementation commit.

## Blockers

None.

## Next Exact Action

Run cross-version CI, inspect failures, preview the console in a real VS Code Terminal,
and review context/rotation defaults without making causal efficiency claims.

## Stop Condition

Ruff, pytest, repository verification, strict context plan, dry-run, report, and link
checks pass; the release candidate is ready for an operator pilot.

## Continuation Gate

Decision: ROTATE_REQUIRED
Reason: IMPLEMENTATION_TO_INDEPENDENT_VALIDATION_BOUNDARY

## Next Task

ID: T-009
Spec: docs/tasks/T-009-token-efficient-runtime-prospective-study.md

## Next Session Role

Runner

## Recommended Reasoning

Medium

## Last Updated

2026-08-15 — RSAW 0.5 cache-aware runtime release candidate
