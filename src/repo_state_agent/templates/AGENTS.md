# Agent Policy

## Source of Truth

Repository state overrides conversation history.

## Session Bootstrap

Read only:

1. `AGENTS.md`
2. `ACTIVE.md`
3. the active task referenced by `ACTIVE.md`

Use progressive disclosure for additional context.

## Bounded Sessions

One substantial task per session. Update `ACTIVE.md` and stop at completion, verification, a major blocker, long-running wait, review handoff, or decision boundary.

## Validation

- V0: syntax/lint/targeted test
- V1: task-specific suite
- V2: full closure validation
- V3: fresh independent review

## Roles

Builder implements. Reviewer starts fresh. Decision sessions decompose evidence before synthesizing a choice.

## Safety

Do not use destructive Git commands or modify unrelated user work without explicit authorization.

## Handoff

Before stopping, record current state, blockers, required reads, next exact action, stop condition, and next role in `ACTIVE.md`.
