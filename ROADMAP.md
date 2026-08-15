# RSAW Roadmap

## v0.7 — Operator-Hardened Repository Context Runtime

Status: implementation and release validation complete on the release branch; empirical efficiency promotion remains evidence-gated.

### Runtime correctness

- [x] Supervisor-owned evidence binding
- [x] camelCase and snake_case checkpoint-result task references
- [x] canonical ACTIVE rendering
- [x] repository-global checkpoint display in the TUI
- [x] transactional checkpoint/state advancement
- [x] full rollback after post-advance verification failure
- [x] role-aware Human Gate clearing
- [x] deduplicated command/tool event accounting

### Operator experience

- [x] unified top-level CLI
- [x] `rsaw preflight`
- [x] one-command `rsaw start`
- [x] launcher/Python mismatch diagnostics
- [x] audited gate controls
- [x] persistent task sandbox profiles
- [x] operator-safe PAUSE / COMPLETE exits
- [x] redesigned README and terminal visuals
- [x] EdgeFlow deployment and rollback guide

### Context and cost control

- [x] live per-turn tool-call budget
- [x] live total and peak tool-output budgets
- [x] broad-discovery command budget
- [x] tool budgets reset for every turn
- [x] tool-output and budget-abort telemetry
- [x] anti-rediscovery prompt contract
- [ ] matched short-horizon prospective evaluation
- [ ] matched medium-horizon break-even evaluation
- [ ] matched 32–64 checkpoint long-horizon evaluation
- [ ] calibrated project-specific tool-budget study

## Promotion requirements

Do not promote causal efficiency claims until matched evidence shows:

- semantic-success parity versus No-RSAW;
- no short-horizon input/success regression;
- medium-horizon total/cached/fresh input per success improvement;
- long-horizon total/repeated/tool-output separation;
- zero manual relay;
- fresh recovery without stale-state regression;
- no increase in safety false positives or oracle false negatives.

## Next evidence program

1. Freeze matched tasks, model, tool availability, sandbox, and starting revisions.
2. Compare No-RSAW, archived v3, v0.5, v0.6, and v0.7.
3. Run 4-checkpoint short workstreams before spending on 16/64 checkpoint horizons.
4. Adjudicate semantic success independently from RSAW's own checkpoint result.
5. Archive raw provider usage, event streams, tool-output traffic, lifecycle decisions, and recovery evidence.
6. Publish only the claims supported by the matched ledger.

## Later engineering candidates

Only after the matched v0.7 study should later releases consider:

- provider-native context occupancy when available;
- additional agent adapters;
- richer evidence range retrieval;
- automatic project-specific budget calibration;
- team/shared durable-state coordination;
- policy-learning experiments for the Token Governor.

Do not add complexity merely to create another version number. Resolve the v0.7 empirical hypothesis first.
