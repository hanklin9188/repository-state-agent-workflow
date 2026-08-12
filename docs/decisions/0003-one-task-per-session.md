# ADR-0003: One Substantial Task per Session

- Status: Accepted
- Date: 2026-08-12

## Context

Sessions that span multiple unrelated tasks accumulate obsolete context and blur validation boundaries.

## Decision

A session normally owns one substantial task and stops at completion, verification, a major blocker, long-running wait, or decision boundary.

## Consequences

Handoffs become explicit. Reviewers can start fresh. Small related edits may remain together when they share one acceptance boundary.
