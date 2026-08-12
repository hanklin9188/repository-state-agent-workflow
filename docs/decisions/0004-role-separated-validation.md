# ADR-0004: Separate Builder, Reviewer, and Decision Roles

- Status: Accepted
- Date: 2026-08-12

## Context

A builder's debugging history can bias review, and major decisions require different reasoning from routine implementation.

## Decision

Use fresh reviewer sessions and distinct decision sessions. Under Medium reasoning, major decisions use evidence-decomposition and synthesis passes.

## Consequences

Review context is smaller and more independent. Decision artifacts become explicit repository state.
