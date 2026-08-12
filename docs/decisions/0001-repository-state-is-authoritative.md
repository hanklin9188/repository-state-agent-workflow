# ADR-0001: Repository State Is Authoritative

- Status: Accepted
- Date: 2026-08-12

## Context

Conversation transcripts are difficult to version, review, reproduce, and transfer between agents.

## Decision

Durable project state lives in repository artifacts. Conversation context may assist but cannot override current repository authority.

## Consequences

- Fresh sessions can continue from a checkout.
- Important conclusions must be written to tasks, decisions, tests, reports, or evidence.
- Unrecorded conversational knowledge is not a reliable dependency.
