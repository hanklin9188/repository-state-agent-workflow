# RSAW v2 — Persistent Workstreams and Context Epochs

RSAW v2 keeps repository-backed continuity while allowing several closely
coupled tasks to share one bounded context epoch.

## Added

- persistent workstream roadmaps;
- context epochs;
- durable task checkpoints;
- continuation and rotation gates;
- context-budget policy;
- V0/V1/V2/V3 validation placement by task and epoch;
- zero-config initialization and conservative v1 upgrade;
- deterministic `status`, `checkpoint`, `rotate`, and prompt helpers;
- persistent-workstream templates and example repository;
- matched evaluation methodology for context retention versus rotation.

## Compatibility

The original bounded-session workflow remains supported. Scientific formal
execution, independent review, and post-hoc interpretation remain hard fresh-
context boundaries.

## Claim boundary

The previously reported 91.1% result remains a bootstrap-context estimate from
an RSAW v1 case study. RSAW v2 token and quality improvements remain hypotheses
until matched task-stream evaluation is complete.
