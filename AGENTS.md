# Agent Policy

## Source of Truth

Repository state overrides conversation history.

Use this authority order:

1. accepted decisions and immutable contracts;
2. executable schemas, tests, and validation;
3. active task specification;
4. `ACTIVE.md` continuation state;
5. conversation context.

Do not infer project state from an old chat when the repository can answer it.

## Session Bootstrap

A fresh session starts by reading only:

1. `AGENTS.md`;
2. `ACTIVE.md`;
3. the active task spec referenced by `ACTIVE.md`.

Read additional files only when the active task requires them.

Do not preload all decisions, reports, logs, source files, or archived handoffs.

## Bounded Session Rule

One substantial task should normally fit in one session.

Stop and update `ACTIVE.md` when:

- the active task is complete;
- closure validation is complete;
- a major blocker is reached;
- long-running work becomes the only blocker;
- implementation is ready for fresh review;
- a major architecture or scientific decision is required;
- obsolete context has become substantial.

## Progressive Disclosure

Use path and evidence pointers instead of copying large content into handoffs.

Read exact dependencies on demand.

## Validation

Use these engineering tiers:

- `V0`: syntax, lint, and targeted tests during editing;
- `V1`: task-specific suite when the feature is stable;
- `V2`: full relevant repository validation at task closure;
- `V3`: fresh independent review for critical or release work.

Do not confuse engineering validation with scientific or production evidence.

## Roles

### Builder

Default reasoning: Medium.

Implement the active task, run targeted validation, and leave a compact handoff.

### Reviewer

Use a fresh session. Read the spec, diff, tests, and evidence. Do not preload the builder's debugging transcript.

### Decision

For major forks under Medium reasoning, use two passes:

1. evidence and construct decomposition;
2. architecture or decision synthesis.

Record unresolved assumptions explicitly.

## Long-Running Work

Do not repeatedly poll a long-running job when waiting is the only remaining action.

Record its ID, expected output, artifact path, revision, and next exact action in `ACTIVE.md`, then stop when safe.

## Handoff

Before stopping, ensure `ACTIVE.md` contains:

- current state;
- verified prerequisites;
- blockers;
- required reads;
- next exact action;
- stop condition;
- next session role.

## Evidence Discipline

Never rewrite measured evidence or hide failed results.

Tests prove implementation behavior; they do not automatically prove scientific or production claims.

## Git Safety

Do not use destructive Git commands without explicit human authorization.

Do not commit secrets, caches, model weights, or unrelated artifacts.

## Execution Verbosity

Keep routine narration low. Report decisions, evidence, blockers, validation, and handoff state.
