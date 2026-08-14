# Agent Policy

## Source of Truth

Repository state overrides conversation history.

## Minimal Bootstrap

Read only:

1. `AGENTS.md`
2. `ACTIVE.md`
3. the active task referenced by `ACTIVE.md`

Use progressive disclosure for everything else.

## Persistent Workstreams

A workstream may last days or weeks. The model context must not.

Work through bounded context epochs. A context epoch may close several adjacent tasks when they share the same role, hypothesis, subsystem, and evidence domain.

Every task still ends with a durable checkpoint before the next task begins.

## Continuation Gate

At each task checkpoint, run `rsaw next .`.

- `CONTINUE`: activate the ready next task and continue in the same context epoch.
- `ROTATE_REQUIRED`: update `ACTIVE.md`, stop, and resume in a fresh context.
- `STOP_REQUIRED`: preserve state and wait for the human gate or external work.

Never continue across a role change, scientific execution/analysis boundary, major debugging residue, long-running-only wait, or explicit human gate.

## Context Budget

Prefer 20K–40K working contexts. Rotate around 50K–60K when practical. Treat routine contexts above 80K as a workflow failure unless explicitly justified.

## Validation

- V0: syntax, lint, exact targeted test during editing
- V1: focused task checkpoint
- V2: one full relevant check at context-epoch or phase closure
- V3: fresh independent review only for critical claims, releases, or major forks

Validation is a gate, not the product. Do not add defensive validation for hypothetical failures.

## Roles

Builder may continue across adjacent engineering tasks. Reviewer, Runner, Analyst, and Decision roles start fresh unless the repository explicitly proves otherwise.

## Safety

Do not use destructive Git commands or modify unrelated user work without explicit authorization.

## Handoff

Before a checkpoint or rotation, record current state, evidence pointers, blockers, next action, continuation decision, next task, and next role in `ACTIVE.md`.
