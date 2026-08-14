# Agent Policy

## Source of Truth

Repository state overrides conversation history.

## Bootstrap

Read only `AGENTS.md`, `ACTIVE.md`, and the active task. Expand context on demand.

## Persistent Workstream

The workstream may run for days or weeks. Model contexts remain bounded. Every task closes with durable repository state before the next task begins.

## Runtime Actions

- `CONTINUE`: same context may execute the next closely coupled task.
- `ROTATE`: the workstream continues in a fresh context.
- `PAUSE`: human or external action is required.
- `COMPLETE`: the workstream is terminal.

Do not print or relay next-session prompts when the RSAW supervisor is active. Update `ACTIVE.md`; the supervisor performs continuation or rotation.

## Mandatory Fresh Boundaries

Rotate for role changes, Builder→Runner, Runner→Analyst, formal execution→interpretation, fresh review, major decisions, and major debugging closure.

## Validation

- V0: syntax/lint/exact test during editing
- V1: focused task checkpoint
- V2: one relevant epoch or phase closure
- V3: independent critical review

Validation is a gate, not the product. Add validation only for an observed threat or explicit contract.

## Long-Running Work

Record job ID, revision, expected artifacts, completion condition, and next action. Do not busy-poll.

## Safety

Do not bypass authorization, approvals, sandboxing, or destructive-action gates. Preserve failed evidence and consumed authorizations.

## Handoff

Before a checkpoint, update current state, evidence pointers, next task, next action, role, human gate, and continuation decision.
