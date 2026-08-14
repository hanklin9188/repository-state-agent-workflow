# Agent Policy

## Source of Truth

Repository state overrides conversation history.

Use this authority order:

1. accepted decisions and immutable contracts;
2. executable schemas, tests, and validation;
3. active task specification;
4. `ACTIVE.md` continuation state;
5. conversation context.

## Minimal Bootstrap

Read only:

1. `AGENTS.md`;
2. `ACTIVE.md`;
3. the active task referenced by `ACTIVE.md`.

Use progressive disclosure for everything else.

## Persistent Workstream

The workstream may span many tasks and context epochs. Every task must still
produce a durable checkpoint before the next task begins.

When the RSAW supervisor is active, do not ask the human to copy a next-session
prompt. Update `ACTIVE.md`; the supervisor applies the next runtime action.

## Runtime Actions

- `CONTINUE`: reuse the current context for a tightly coupled task.
- `ROTATE`: keep the workstream running in a fresh context.
- `PAUSE`: wait for explicit human or external action.
- `COMPLETE`: terminate the workstream.

## Mandatory Rotation

Use a fresh context for:

- Builder → Reviewer, Runner, Analyst, or Decision;
- formal execution → interpretation;
- preregistration → execution;
- independent critical review;
- major architecture/scientific decision;
- closure of a large debugging episode;
- material hypothesis or specification change;
- context pressure beyond the workstream budget.

## Validation

- `V0`: syntax, lint, exact test during editing;
- `V1`: focused task-checkpoint validation;
- `V2`: one relevant epoch or phase closure;
- `V3`: fresh independent review for critical work.

Validation is a gate, not the product. Add new validation only for an observed
threat to the active claim or an explicit contract requirement.

## Runtime Safety

- Do not enable dangerous sandbox/approval bypasses.
- Do not infer authorization, credentials, privilege, or destructive consent.
- Do not automatically retry failed formal or scientific runs.
- Preserve failed evidence and consumed authorizations.
- Ensure `ACTIVE.md` advances after every successful supervised turn.
- Respect transition, turn, and token limits.

## Long-Running Work

Do not busy-poll. Record the job/run ID, revision, configuration/protocol,
expected artifacts, completion condition, and next action, then pause safely.

## Evidence Discipline

Tests establish implementation behavior. Scientific and production claims need
their own protocol, provenance, measured evidence, and interpretation boundary.

Do not rewrite raw evidence or hide negative results.

## Git Safety

Do not use destructive Git commands or modify unrelated work without explicit
authorization. Do not commit secrets, caches, model weights, or runtime logs.

## Handoff

Before a checkpoint, record:

- current state;
- evidence pointers;
- blockers and human gates;
- active and next task;
- next exact action;
- stop condition;
- current and next role;
- continuation decision.

Keep routine narration low.
