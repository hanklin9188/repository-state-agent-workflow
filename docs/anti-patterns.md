# Anti-Patterns

## AGENTS.md as a diary

Do not put current run IDs, temporary blockers, or dated history into stable policy.

## ACTIVE.md as a compressed encyclopedia

A giant handoff defeats the system. Use evidence pointers and keep only the current frontier.

## One unbounded context for an entire milestone

Multiple adjacent tasks may share one context epoch. An entire milestone without task checkpoints or rotation policy may not.

## Fresh context after every trivial edit

Always-fresh operation can waste bootstrap and re-understanding cost. Group closely coupled tasks, but checkpoint each one.

## Continuation by intuition only

Do not let the model keep going merely because it feels convenient. Record the decision and run `rsaw next .`.

## Continuing across role or scientific boundaries

Builder → Reviewer, Formal Runner → Analyst, and preregistration → execution require fresh contexts.

## Reading the entire repository first

Importance is not relevance. Read exact dependencies on demand.

## Running full validation after every edit

Use V0/V1 during work, V2 once at epoch closure, and V3 only for critical independent review.

## Passing debugging history to the reviewer

Give the reviewer the spec, diff, tests, and evidence—not the exploratory transcript.

## Auto-summarizing everything

A summary can become another stale authority. Prefer canonical artifacts and small pointers.

## Building an orchestration platform inside RSAW

Markdown, Git, task specs, and deterministic checks are the product boundary. Do not replace context bloat with framework bloat.
