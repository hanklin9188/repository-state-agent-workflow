# Token Economics

## Productive versus repeated context

RSAW does not minimize tokens indiscriminately. It aims to increase:

```text
useful task reasoning / total context traffic
```

The avoidable portion is repeated history, obsolete debugging, broad preload,
and reorientation after unnecessary fresh starts.

## Three accounting levels

### Repository estimate

`rsaw footprint` estimates UTF-8 characters divided by four. This is useful for
stable bootstrap comparisons but is not provider billing.

### Retrospective workstream replay

Reconstruct which files each workflow condition would load. State assumptions
and do not treat a counterfactual estimate as measured usage.

### Measured runtime usage

`rsaw run` records token usage emitted by Codex JSON events. `rsaw report`
separates input, cached input, cache-write input, output, and reasoning output.

## Cost-quality metric

Prefer:

```text
input tokens / successfully closed task
```

and report completion, validation, reviewer findings, rework, and human
intervention alongside token totals.

## Rotation economics

Always-fresh tasks pay repeated bootstrap and subsystem reconstruction. An
unbounded thread accumulates obsolete context. Bounded epochs seek an operating
point between those costs.

Runtime limits are safety guardrails, not optimized thresholds. Tune on pilot
work and evaluate on separate tasks.

## Existing evidence

- Desk Code Agent v1: 91.1% bootstrap-context estimate reduction.
- EdgeFlow v1/v2 replay: 60.8%–62.9% estimated repository-context reduction.
- RSAW 0.3: prospective provider accounting enabled; no universal improvement
  claimed yet.
