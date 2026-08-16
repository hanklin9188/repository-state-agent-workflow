# Active Handoff

## Repository

Branch: resolve with `git branch --show-current`
HEAD: resolve with `git rev-parse HEAD`
Status: RSAW v0.8.0 relevance-first runtime release validation

## Workstream

ID: W-007
Spec: docs/workstreams/W-007-relevance-first-context.md

## Context Epoch

ID: E-012-v08-release
Role: Reviewer

## Active Task

ID: T-012
Spec: docs/tasks/T-012-v08-release-validation.md

## Current State

- Relevance-first Focus Context is implemented with deterministic local retrieval.
- Focus uses content-hash caching, structural ranking, and bounded exact excerpts.
- CONTINUE reuses unchanged context by reference.
- Provider-input pressure can force COMPACT at the next checkpoint.
- Transactional checkpoints, audited gates, and task sandboxes remain authoritative.
- Universal provider-token and task-success claims remain evidence-gated.

## Evidence

- Runtime: `src/repo_state_agent/runtime/relevance.py`
- Integration: `src/repo_state_agent/runtime/v6.py`
- CLI: `src/repo_state_agent/v7_cli.py`
- Tests: `tests/test_v8_relevance.py`, `tests/test_v8_supervisor_focus.py`
- Benchmark: `docs/validation/V080_RELEVANCE_BENCHMARK.json`
- Design: `docs/relevance-first-context.md`

## Required Reads

- AGENTS.md
- ACTIVE.md
- docs/tasks/T-012-v08-release-validation.md
- docs/relevance-first-context.md

## Context Contract

Mode: REVIEW
Stable Prefix: AGENTS.md
Budget: `.rsaw/config.json`

## Do Not Preload

- complete repository contents;
- raw runtime or evidence payloads;
- historical release logs unless a validation fails;
- unrelated case-study material.

## Human Gate

None.

## Running or Pending External Work

GitHub CI, clean installation, tag, and release validation.

## Blockers

None.

## Next Exact Action

Complete the release matrix, review the public documentation and assets, and bind the
published v0.8.0 tag to the validated release commit.

## Stop Condition

Ruff, pytest, repository verification, Focus/compile checks, 4/16/64 acceptance, Markdown
links, package build, clean installation, public tag, and release asset verification pass.

## Continuation Gate

Decision: ROTATE_REQUIRED
Reason: IMPLEMENTATION_TO_RELEASE_VALIDATION_BOUNDARY

## Next Task

ID: T-013
Spec: docs/tasks/T-013-v08-prospective-study.md

## Next Session Role

Runner

## Recommended Reasoning

Medium

## Last Updated

2026-08-16 — RSAW v0.8.0 relevance-first release validation
