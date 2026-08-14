# Agent Policy

## Source of Truth

Repository state overrides conversation history.

Use this authority order:

1. accepted decisions and immutable contracts;
2. executable schemas, tests, and validation;
3. active task specification;
4. `ACTIVE.md` continuation state;
5. conversation context.

## Cache-Aware Bootstrap

Read the ordered context plan produced by `rsaw context .`.

- Stable prefix: policy and other rarely changing authority.
- Dynamic authority: `ACTIVE.md`, the active task, and bounded required reads.
- In a continued epoch, do not reread the stable prefix unless its fingerprint changed.
- Expand context only for evidence required by the current checkpoint.

## Persistent Workstream

The workstream may span many tasks and context epochs. Every task must produce a
durable checkpoint before the next task begins.

When the RSAW supervisor is active, do not ask the human to copy a next-session
prompt. Update `ACTIVE.md`; the supervisor applies the next runtime action.

## Runtime Actions

- `CONTINUE`: reuse the current context for a tightly coupled task.
- `ROTATE`: keep the workstream running in a fresh context.
- `PAUSE`: wait for explicit human or external action.
- `COMPLETE`: terminate the workstream.

## Mandatory Rotation

Use a fresh context for role changes, formal execution/analysis boundaries,
independent review, major decisions, major debugging closure, specification
changes, hard context pressure, fresh-input pressure, or poor cache reuse near the
soft threshold.

## Validation

- `V0`: syntax, lint, exact test during editing;
- `V1`: focused task-checkpoint validation;
- `V2`: one relevant epoch or phase closure;
- `V3`: fresh independent review for critical work.

Validation is a gate, not the product. Add validation only for an observed threat
or explicit contract.

## Runtime Safety

- Do not enable dangerous sandbox or approval bypasses.
- Do not infer authorization, credentials, privilege, or destructive consent.
- Do not automatically retry failed formal or scientific runs.
- Preserve failed evidence and consumed authorizations.
- Ensure `ACTIVE.md` advances after every successful supervised turn.
- Respect transition, turn, context, and token limits.

## Evidence Discipline

Tests establish implementation behavior. Scientific and production claims need a
protocol, provenance, measured evidence, and interpretation boundary. Do not
rewrite raw evidence or hide negative results.

## Handoff

Before a checkpoint, record current state, evidence pointers, blockers, human
gates, active and next task, exact next action, stop condition, current and next
role, and continuation decision. Keep routine narration low.
