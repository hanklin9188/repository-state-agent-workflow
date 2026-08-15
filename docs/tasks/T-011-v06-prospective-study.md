# T-011 — RSAW v0.6 matched prospective study

## Objective

Measure whether the released v0.6 runtime resolves the v3 failure mechanisms on matched real agent workstreams.

## Allowed Writes

- data/**
- docs/evaluation/**
- docs/validation/**
- .rsaw/state/**

## Validation

- `rsaw acceptance . --horizon all`

## Treatments

At minimum compare:

1. No RSAW;
2. RSAW v3/current archived baseline where available;
3. RSAW v0.5;
4. RSAW v0.6.

## Horizons

- short: 4 checkpoints;
- medium: 12–16 checkpoints;
- long: 32–64 checkpoints with interruption/recovery and review boundaries.

## Required metrics

Attempted/successful checkpoints, semantic success, total/cached/fresh input, input per success, output, fresh contexts, model/tool calls, compactions, rotations, repeated input, evidence resend, manual relay, true human gates, wall time per success, recovery rediscovery commands, safety false positives, and oracle false negatives.

## Promotion gate

No token win is accepted if matched semantic success regresses materially. Medium-horizon targets are at least 20% lower total/cached input per success and at least 15% lower uncached input per success with zero manual relay. Long horizon must show clear total/repeated-input separation while preserving recovery and stale-state safety.

## Stop Condition

Matched evidence is archived with a deterministic adjudication ledger and claims are limited to what the evidence supports.
