# Active Handoff

## Repository

Branch: main
HEAD: current committed main (resolve with `git rev-parse HEAD`)
Status: validated publication candidate

## Active Milestone

v0.1 — Publish the generalized Repository-State Agent Workflow reference implementation.

## Active Task

ID: T-001
Spec: docs/tasks/T-001-initial-release.md

## Current State

- English and Traditional Chinese first-screen messaging is complete.
- Company adoption, research methodology, and case-study guidance are included.
- The dependency-light `rsaw` CLI, templates, examples, and tests are implemented.
- GitHub CI, issue templates, Dependabot, publication metadata, and social preview are prepared.
- Local validation passes and the complete publication candidate is committed.
- Release archives and a Git bundle can be generated reproducibly.
- The public GitHub repository does not yet exist.

## Verified Preconditions

- Repository name: `repository-state-agent-workflow`.
- Visibility: public.
- License: MIT.
- Primary language: English, with Traditional Chinese README.
- Claims remain evidence-bounded; token reduction is presented as illustrative.

## Required Reads

- AGENTS.md
- ACTIVE.md
- docs/tasks/T-001-initial-release.md
- PUBLISH.md

## Do Not Preload

- every example project file;
- all decision records;
- the full documentation tree;
- archived handoffs;
- test internals unless validation fails.

## Running or Pending External Work

None.

## Blockers

The current connected GitHub integration is read-only and the local environment has no authenticated GitHub CLI, so it cannot create or push the new repository directly.

## Next Exact Action

Publish the committed tree with `./scripts/publish_github.sh` from an authenticated WSL environment, then upload the social preview.

## Stop Condition

The public repository exists, `main` is pushed, CI is green, and the social preview is uploaded.

## Next Session Role

Builder

## Recommended Reasoning

Medium

## Last Updated

2026-08-12 — professional publication candidate
