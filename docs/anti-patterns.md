# Anti-Patterns

## AGENTS.md as a diary

Bad:

- yesterday's failures;
- current run IDs;
- temporary blockers;
- complete project history.

Keep stable policy in `AGENTS.md`; put current state in `ACTIVE.md`.

## ACTIVE.md as a compressed encyclopedia

A 2,000-line handoff defeats the purpose. Use pointers.

## One session for an entire milestone

Long sessions retain obsolete context and blur task boundaries. Split at meaningful closure points.

## Reading the entire repository first

Importance is not the same as relevance. Read exact dependencies on demand.

## Running full validation after every edit

Use V0/V1 during iteration and V2 at closure.

## Passing debugging history to the reviewer

Give the reviewer the spec, diff, tests, and evidence. Let the reviewer start fresh.

## Auto-summarizing everything

A summary can become another stale authority. Prefer canonical artifacts and small current-state pointers.

## Building a large orchestration platform

Markdown, Git, task specs, and deterministic checks are often sufficient. Do not replace context bloat with framework bloat.
