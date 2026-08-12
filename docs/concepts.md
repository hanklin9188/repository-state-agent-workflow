# Concepts

## Repository-backed memory

The repository stores durable state in human-readable, version-controlled artifacts. Conversation history is useful for interaction, but it is not the authoritative memory system.

## Stable policy

`AGENTS.md` contains global rules that should remain valid across tasks: build commands, safety boundaries, validation expectations, role definitions, and handoff rules.

It should not contain current progress or dated task history.

## Active state

`ACTIVE.md` is a bounded working-memory page. It records the current frontier, not the whole project.

A good `ACTIVE.md` makes a fresh session immediately actionable while remaining cheap to load repeatedly.

## Task contract

A task spec defines one bounded unit of work with in-scope behavior, acceptance criteria, validation, evidence, and a stop condition.

## Evidence pointers

Handoffs reference commits, test reports, ADRs, protocol hashes, and artifacts by path instead of copying large content.

## Stateless-ish agent

The agent is not perfectly stateless—it still sees the current conversation—but project continuity does not depend on retaining that conversation.
