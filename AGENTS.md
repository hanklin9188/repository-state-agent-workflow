# Agent Policy

## Source of Truth

Repository state overrides conversation history.

Use this authority order:

1. accepted decisions, registered protocols, and immutable contracts;
2. executable schemas, tests, and validation;
3. active task specification;
4. `ACTIVE.md` current frontier;
5. conversation context.

## Minimal Bootstrap

Read only:

1. `AGENTS.md`;
2. `ACTIVE.md`;
3. the active task referenced by `ACTIVE.md`.

Use progressive disclosure. Do not preload all decisions, reports, logs, examples, source, or archived handoffs.

## Persistent Workstreams

The workstream may persist for days or weeks. The model context may not.

A Context Epoch may complete several adjacent tasks when they share the same role, objective, subsystem, evidence domain, and safety boundary. Every task still closes with a durable checkpoint.

## Continuation Gate

At each task checkpoint:

1. persist evidence;
2. activate the next task;
3. update `ACTIVE.md`;
4. run `rsaw verify .` and `rsaw next .`.

Continue only when the gate returns `CONTINUE`.

Hard rotation boundaries include:

- role change;
- preregistration → formal execution;
- formal execution → scientific analysis;
- major architecture/scientific decision;
- completed large debugging episode;
- long-running work as the only blocker;
- human authorization, credential, or destructive action;
- excessive context pressure.

## Context Budget

Target routine epochs around 20K–40K tokens, rotate around 50K–60K when practical, and treat routine contexts above 80K as a workflow failure unless explicitly justified.

## Validation

- `V0`: syntax, lint, exact targeted test;
- `V1`: focused task checkpoint;
- `V2`: one full relevant check at context-epoch or phase closure;
- `V3`: fresh independent review for critical claims, releases, or major forks.

Validation is a gate, not the product. Add validation only for observed threats to the current claim or explicit contracts.

## Roles

Builder may continue across adjacent engineering tasks. Reviewer, Runner, Analyst, and Decision roles start fresh unless a governing contract explicitly proves otherwise.

## Long-Running Work

Do not busy-wait. Record job ID, revision, protocol/command, expected outputs, artifact path, completion condition, and next role, then stop when waiting is the only action.

## Evidence Discipline

Never rewrite measured evidence or hide failed results. Tests prove software behavior; they do not automatically prove scientific, product, or token-efficiency claims.

## Git Safety

Do not use destructive Git commands without explicit authorization. Do not commit secrets, caches, model weights, or unrelated artifacts.

## Execution Verbosity

Keep routine narration low. Report decisions, evidence, blockers, validation, checkpoint state, and continuation outcome.
