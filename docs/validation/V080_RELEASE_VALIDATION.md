# RSAW v0.8.0 Release Validation

## Scope

This record separates deterministic implementation validation from empirical product claims.

## Release implementation gate

The exact release candidate must pass:

- full Python test suite;
- Ruff format and lint;
- compileall;
- `rsaw verify`;
- Focus construction and cache reuse;
- FRESH Context Envelope compilation;
- runtime dry-run and report generation;
- 4 / 16 / 64 lifecycle acceptance;
- Markdown local-link validation;
- source distribution and wheel build;
- isolated wheel installation on the supported Python matrix.

## Deterministic relevance fixture

Fixture composition:

```text
1 target implementation
1 rejecting test
1 supporting process-inventory module
36 distractor modules
```

The canonical machine-readable result is
[`V080_RELEVANCE_BENCHMARK.json`](V080_RELEVANCE_BENCHMARK.json).

## Promotion gate

Do not claim production token superiority until matched real-workstream evidence shows:

- semantic-success parity or improvement;
- lower total input per successful checkpoint;
- lower cached input per successful checkpoint;
- lower fresh input per successful checkpoint;
- fewer broad-discovery commands;
- no increase in manual relay, safety errors, or authority violations.

The deterministic fixture is a mechanism test, not the matched product evaluation.

## Post-release matched evidence

Desk Code Agent subsequently completed a 48-attempt matched comparison of direct
Codex and exact commit-pinned RSAW v0.8.0. The preregistered primary result did
not pass the value gate. A separately labelled post-hoc sensitivity found equal
24/24 attributed completion, 45.39% lower input per success, 24.12% lower
uncached input per success, no broad-discovery commands, and 28.87% higher active
time per success under RSAW.

This supports an opt-in retrieval-heavy long-workstream pilot, not universal
default activation. See the
[full matched case study](../case-studies/desk-code-agent-rsaw-v080-matched.md).
