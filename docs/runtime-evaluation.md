# Runtime Evaluation

RSAW 0.3 turns context rotation from a design estimate into an observable
runtime process.

## Conditions to compare

1. Chat-as-memory / long conversation
2. RSAW 0.1 always-fresh tasks
3. RSAW 0.2 bounded context epochs with manual rotation
4. RSAW 0.3 automatic Runtime Supervisor

## Primary unit

Use a matched task stream or workstream, not individual model calls. Turns
inside one task are correlated.

## Runtime metrics

`rsaw report --json` supplies:

- workstream and final status;
- agent turns;
- fresh and resumed turns;
- runtime epochs;
- checkpoints observed;
- CONTINUE / ROTATE / PAUSE / COMPLETE counts;
- provider-emitted token usage;
- input tokens per successful checkpoint.

Add project metrics:

- task closure;
- focused and closure validation;
- reviewer findings;
- escaped defects;
- repeated investigation;
- stale-state incidents;
- human interventions;
- elapsed time.

## Important outcome

The most useful cost measure is not minimum tokens in isolation:

```text
input tokens / successfully closed task
```

A workflow that uses fewer tokens but creates more defects is not an
improvement.

## Matched evaluation

Pin:

- repository revision;
- task selection procedure;
- Codex version and model;
- sandbox and permissions;
- validation policy;
- hardware and external services where relevant.

Separate pilot tuning from untouched evaluation tasks.

## Claim boundary

Runtime telemetry supports prospective token and transition accounting. It does
not, by itself, establish causal quality improvement. Report quality and token
outcomes separately, including failed and paused workstreams.
