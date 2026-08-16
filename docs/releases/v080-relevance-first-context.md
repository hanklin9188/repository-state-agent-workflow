# RSAW v0.8.0 — Relevance-First Context Runtime

v0.8.0 changes RSAW from a runtime that mainly limits context growth into one that prepares
a relevant code working set before the model turn.

## Core model

```text
Truth → Focus → Work → Checkpoint
```

- **Truth:** exact repository authority;
- **Focus:** deterministic structural map and exact excerpts;
- **Work:** bounded Codex execution;
- **Checkpoint:** verified transactional state advancement.

## Added

- content-addressed repository index under `.rsaw/cache/`;
- Python AST and lightweight multi-language symbol extraction;
- explainable file ranking from paths, symbols, Git changes, tests, and imports;
- structural-map and focused-excerpt budgets;
- `rsaw focus` inspection command;
- Focus injection into FRESH / COMPACT / ROTATE contexts;
- unchanged Focus reuse by reference on `CONTINUE`;
- provider-input and cached-input pressure thresholds;
- automatic `COMPACT` before the next coherent turn under provider traffic pressure;
- Focus, cache, reuse, and provider-pressure telemetry in reports and the TUI;
- schema 5 migration preserving `ACTIVE.md`;
- EdgeFlow v0.8.0 deployment guide and deterministic relevance benchmark.

## Simplified defaults

v0.8 deliberately does not add a vector database, embedding API, LLM summarizer, or
whole-repository prompt. Retrieval remains deterministic, local, inspectable, and optional.

## Preserved from v0.7.1

- transactional checkpoint advancement and rollback;
- Supervisor-owned evidence binding;
- audited Human Gate and sandbox operations;
- exact-task sandbox resolution every turn;
- sandbox-boundary rotation;
- operator-safe expected exits;
- live tool and output budgets;
- 4 / 16 / 64-checkpoint lifecycle semantics.

## Validation

The release is gated by the complete Python test suite, Ruff, compileall, repository
verification, 4 / 16 / 64 lifecycle acceptance, Markdown links, package build, isolated
installation, and the deterministic relevance fixture.

The fixture contains one target implementation, one rejecting test, one supporting module,
and 36 distractors. The canonical machine-readable result is generated during release CI.

## Claim boundary

The fixture proves the relevance mechanism can isolate a small correct working set. It does
not prove universal provider-token savings, faster wall time, or higher task success.
Matched evaluation against direct Codex, RSAW v0.7.1, and RSAW v0.8.0 remains required.
