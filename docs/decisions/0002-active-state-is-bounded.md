# ADR-0002: Active State Is Bounded

- Status: Accepted
- Date: 2026-08-12

## Context

A handoff that contains the full project history recreates context bloat in Markdown form.

## Decision

`ACTIVE.md` is a compact current-state pointer with a default limit of 120 lines and 10 KB.

## Consequences

Large details live in canonical artifacts. Meaningful old handoffs may be archived, but are not preloaded.
