# Session Roles

## Builder

May continue across adjacent engineering tasks when the continuation gate permits it. Every task still checkpoints before the next begins.

## Reviewer

Starts fresh. Reads the task/spec, diff or commit, tests, evidence, and review questions. Does not preload Builder debugging history.

## Runner

Starts fresh for formal or authorized execution. Executes only the registered scope, preserves raw evidence, and stops before analysis.

## Analyst

Starts fresh from sealed evidence and the governing protocol. Recomputes or interprets without mutating evidence.

## Decision

Starts fresh for major architecture or scientific forks. Under Medium reasoning:

1. decompose facts, inferences, constraints, and options;
2. synthesize the decision and record assumptions.

## Rotation rule

Builder may retain context across adjacent Builder tasks. Role changes require rotation unless a governing contract explicitly justifies an exception.
