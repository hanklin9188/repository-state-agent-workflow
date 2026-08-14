# W-004 — Live Runtime Console

## Goal

Deliver a terminal-native operator console for RSAW without changing repository
authority, lifecycle semantics, token accounting, or safety boundaries.

## State Machine

```text
Contract
→ Event integration
→ Presentation model
→ Responsive rendering
→ Lifecycle-state views
→ Automated validation
→ Operator preview
→ Prospective pilot
```

## Required Properties

- the Live Console runs directly in interactive terminals, including VS Code;
- non-TTY, CI, redirect, JSON, quiet, and dry-run paths remain plain and stable;
- no dashboard text enters Codex prompts;
- hidden reasoning content is never displayed;
- rendering failure cannot fail an agent turn or change a transition;
- phase/progress visualization is shown only when supported by repository evidence;
- PAUSE, FAILED, LIMIT_REACHED, and COMPLETE remain unambiguous;
- raw runtime evidence remains available under `.rsaw/runtime`.

## Validation Budget

V0/V1 for implementation and focused rendering tests, V2 for release closure, and
V3 only for future causal efficiency or quality claims.

## Human Gates

- release or merge decision;
- destructive changes to published history;
- external credentials or formal authorization.

## Workstream Stop

The UI is cross-version tested, documented, previewed in an interactive terminal,
and ready for a prospective non-destructive adoption pilot.
