# RSAW Roadmap

## v0.8.0 — Relevance-First Context Runtime

Status: implementation and deterministic mechanism validation complete; public release and
matched provider evaluation remain release/evidence gates.

### Context selection

- [x] content-addressed local index
- [x] Python AST and lightweight multi-language structure extraction
- [x] explainable path, symbol, test, change, and import ranking
- [x] retrieve-many / send-few Focus bundle
- [x] component token ceilings
- [x] exact source excerpts and structural map
- [x] sensitive, runtime, evidence, and artifact exclusions

### Context lifecycle

- [x] unchanged Focus reuse by reference on `CONTINUE`
- [x] provider-input pressure triggers checkpoint-boundary `COMPACT`
- [x] live tool and output budgets remain a final brake
- [x] TUI and report Focus telemetry
- [x] schema 5 migration preserving `ACTIVE.md`

### Release validation

- [x] 121 local tests
- [x] deterministic relevance fixture
- [x] 4 / 16 / 64 lifecycle acceptance
- [x] repository and Markdown-link validation
- [ ] Python 3.10 / 3.12 / 3.13 CI on the final release commit
- [ ] wheel / sdist and isolated installation on the final release commit
- [ ] public `v0.8.0` tag and release asset verification

## Matched promotion study

Compare direct Codex, RSAW v0.7.1, and RSAW v0.8.0 with fixed model, tools, sandbox,
starting revision, tasks, and independent semantic adjudication.

Promotion requires:

- semantic-success parity or improvement;
- lower total input per successful checkpoint;
- lower cached input per successful checkpoint;
- lower fresh input per successful checkpoint;
- fewer broad-discovery commands;
- no increase in manual relay, safety failures, or authority violations.

## Later candidates

Only after matched evidence:

- optional embedding or graph backends for repositories where deterministic signals fail;
- calibrated per-project Focus budgets;
- provider-native context occupancy when available;
- additional agent adapters;
- team/shared durable-state coordination.

Do not add complexity merely to create another version number. Preserve the small
`Truth → Focus → Work → Checkpoint` model.
