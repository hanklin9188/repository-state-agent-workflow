# T-005 — Prospective Runtime Supervisor Study

## Goal

Run RSAW 0.3 on a controlled, non-destructive multi-task workstream and measure
actual Codex usage, rotations, checkpoints, task closure, and quality.

## Conditions

Compare, where practical:

1. RSAW 0.2 manual bounded epochs;
2. RSAW 0.3 automatic supervisor.

## Metrics

- provider input/cached/output/reasoning tokens;
- fresh and resumed turns;
- runtime epochs and transition counts;
- tokens per successfully closed task;
- task completion and validation;
- repeated reads and rework;
- human interventions;
- reviewer findings;
- elapsed time.

## Safety

Use a non-destructive repository or isolated worktree. Keep dangerous bypasses
disabled. Stop at human gates. Preserve failed runs.

## Acceptance

Publish the exact RSAW/Codex revisions, task stream, permissions, raw aggregate
metrics, failures, quality outcomes, and limitations.
