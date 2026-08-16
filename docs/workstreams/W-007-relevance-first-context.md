# W-007 — Relevance-First Context

## Objective

Reduce model-visible repository context before the agent turn while preserving exact
repository authority, transactional checkpoints, and safety boundaries.

## Design

```text
Truth → Focus → Work → Checkpoint
```

The default implementation is deterministic and local: content-hash index, structural map,
explainable ranking, exact excerpts, live budgets, and safe checkpoint compaction.

## Release boundary

v0.8.0 is promoted only after implementation, lifecycle, package, documentation, and clean
installation gates pass. Universal provider-token claims remain blocked until matched
real-workstream evaluation.
