# Active Handoff

## Repository

Branch: resolve with `git branch --show-current`
HEAD: resolve with `git rev-parse HEAD`
Status: RSAW 0.4 Live Runtime Console release candidate

## Workstream

ID: W-004
Spec: docs/workstreams/W-004-live-runtime-console.md

## Context Epoch

ID: E-006-live-console-review
Role: Reviewer

## Active Task

ID: T-006
Spec: docs/tasks/T-006-live-runtime-console-validation.md

## Current State

- RSAW 0.4 adds an interactive Live Terminal Console for VS Code and normal TTYs.
- Codex remains a headless structured-event execution engine.
- CONTINUE, ROTATE, PAUSE, COMPLETE, verification, token accounting, and safety
  semantics remain unchanged.
- Compact/expanded layouts, context pressure, token/cache telemetry, transitions,
  terminal states, non-TTY fallback, and preview mode are implemented.
- Presentation errors are isolated from agent execution and lifecycle decisions.
- Prospective adoption measurement remains a separate evidence task.

## Evidence

- TUI implementation: `src/repo_state_agent/runtime/tui/`
- Runtime event integration: `src/repo_state_agent/runtime/supervisor.py`
- Codex event integration: `src/repo_state_agent/runtime/codex.py`
- CLI integration: `src/repo_state_agent/cli.py`
- TUI tests: `tests/test_runtime_tui_model.py`, `tests/test_runtime_tui_renderer.py`
- Observability isolation tests: `tests/test_codex_adapter_observability.py`,
  `tests/test_runtime_supervisor_observability.py`
- Product documentation: `README.md`, `docs/live-terminal-ui.md`

## Required Reads

- AGENTS.md
- ACTIVE.md
- docs/tasks/T-006-live-runtime-console-validation.md
- docs/live-terminal-ui.md

## Do Not Preload

- all historical release reports;
- complete CI logs unless a check fails;
- archived handoffs;
- raw Codex event streams unless an observability test fails;
- unrelated case-study data.

## Human Gate

None.

## Running or Pending External Work

GitHub CI and operator TTY preview after the implementation commit.

## Blockers

None.

## Next Exact Action

Run cross-version CI, inspect any failures, execute `rsaw preview .` in a VS Code
Integrated Terminal, and review the final README/console presentation.

## Stop Condition

Ruff, pytest, repository verification, link checks, non-TTY fallback, and the
interactive console preview pass; the pull request is ready for merge review.

## Continuation Gate

Decision: ROTATE_REQUIRED
Reason: IMPLEMENTATION_TO_INDEPENDENT_VALIDATION_BOUNDARY

## Next Task

ID: T-007
Spec: docs/tasks/T-007-live-runtime-console-pilot.md

## Next Session Role

Runner

## Recommended Reasoning

Medium

## Last Updated

2026-08-14 — RSAW 0.4 Live Runtime Console release candidate
