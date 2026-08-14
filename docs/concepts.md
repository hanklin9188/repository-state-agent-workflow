# Concepts

## Repository-backed memory

The repository stores durable state in human-readable, version-controlled artifacts. Conversation history is useful working context, but it is not the project memory system.

## Stable policy

`AGENTS.md` contains rules expected to survive many tasks: build commands, safety boundaries, validation budgets, role definitions, context-rotation rules, and handoff requirements.

It must not become a project diary.

## Workstream

A workstream is a persistent project line with a goal, state machine, human gates, validation budget, and stop condition. It may span days or weeks.

Workstream persistence does not imply persistent model context.

## Active state

`ACTIVE.md` is a bounded working-memory page. It records the current frontier, active task, context epoch, evidence pointers, gate decision, and next action.

It should be cheap to load repeatedly.

## Task contract

A task is one bounded, verifiable unit of work. It defines authority, scope, acceptance, validation, evidence, and a stop condition.

A task always closes durably before the next task begins.

## Context epoch

A context epoch is one bounded model context that may close several adjacent tasks. It retains useful local understanding without allowing an entire milestone to become one unbounded conversation.

## Checkpoint

A checkpoint is the durable task boundary: accepted evidence, state, next task, and continuation decision are written back to the repository.

## Continuation gate

The gate returns `CONTINUE`, `ROTATE_REQUIRED`, or `STOP_REQUIRED`. The repository proposes continuation; deterministic safety rules prevent continuation across missing tasks, role changes, or human gates.

## Evidence pointers

Handoffs reference commits, reports, protocols, test results, and artifacts by path instead of copying large content.

## Stateless-ish agent

The agent is not literally stateless. The goal is that project correctness and continuity never depend on retaining a particular conversation.
