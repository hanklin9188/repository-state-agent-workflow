# W-002 — Context Epoch Evaluation

## Goal

Evaluate whether adaptive context epochs reduce task-stream context cost while preserving or improving successful task closure compared with always-persistent and always-fresh workflows.

## State Machine

```text
T-003 protocol design
→ T-004 instrumentation
→ T-005 matched execution
→ T-006 independent analysis
→ T-007 public case study
```

## Primary Unit

A matched task stream or successfully closed task—not an isolated model call.

## Core Metrics

- total input and cached input where available;
- bootstrap and routine working-set estimates;
- repeated reads and repeated investigation;
- tokens per successfully closed task;
- completion and closure validation;
- fresh handoff success;
- reviewer findings and escaped defects;
- human intervention and elapsed time.

## Conditions

- chat-as-memory / always persistent;
- RSAW 0.1 / always fresh;
- RSAW 0.2 / adaptive context epoch.

## Claim Boundary

No RSAW 0.2 token or quality advantage may be claimed before matched evidence exists.

## Workstream Stop

A reproducible case study and machine-readable result are published with limitations.
