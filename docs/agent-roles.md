# Agent Roles

## Builder

Inputs:

- stable policy;
- active state;
- task spec;
- exact code dependencies.

Outputs:

- implementation;
- targeted validation;
- closure evidence;
- updated handoff.

## Reviewer

Starts fresh. Reads:

- task spec;
- diff or commit;
- test results;
- known limitations;
- exact review questions.

The reviewer should not inherit the builder's entire debugging transcript because that history can bias the review.

## Decision

Used for architecture, scientific, or product forks.

With Medium reasoning:

### Pass A — Evidence decomposition

- observed facts;
- inferred explanations;
- competing options;
- missing evidence;
- constraints.

### Pass B — Synthesis

- decision;
- trade-offs;
- assumptions;
- validation plan;
- explicit human values.

A decision agent should not implement the chosen architecture in the same unbounded session unless the task is trivial.
