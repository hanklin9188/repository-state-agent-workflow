# T-006 — Live Runtime Console Validation

## Objective

Independently validate the RSAW 0.4 Live Terminal Console implementation and its
claim boundaries.

## Required Checks

- `ruff check .`;
- `pytest -q` across supported Python versions;
- `rsaw verify .`;
- `rsaw footprint . --max-tokens 15000`;
- `rsaw run . --dry-run`;
- `rsaw report . --json`;
- Markdown link validation;
- `rsaw preview .` in a VS Code Integrated Terminal;
- explicit `--no-tui` and redirected-output smoke checks.

## Acceptance Criteria

- the dashboard answers NOW, progress, next action, context health, and human-gate
  questions within one view;
- compact and expanded layouts remain legible;
- lifecycle and adapter regression tests pass;
- presentation failures are isolated;
- no hidden reasoning or fabricated global progress appears;
- documentation distinguishes observability from token-efficiency claims.

## Stop Condition

All automated checks pass and the interactive preview matches the documented
operator experience.
