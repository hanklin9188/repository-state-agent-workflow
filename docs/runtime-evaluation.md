# Runtime Evaluation

## Question

Does repository-backed, cache-aware context lifecycle improve long-running execution
without reducing checkpoint quality or weakening governance?

## Matched conditions

Hold constant:

- repository revision and starting state;
- model/profile;
- task and permissions;
- sandbox and human-gate policy;
- validation oracle;
- hardware and external services where relevant.

Compare conditions such as chat-as-memory, always-fresh execution, bounded epochs, and
RSAW 0.5 cache-aware runtime.

## Primary metrics

1. attempted checkpoints;
2. successful checkpoints and success rate;
3. total input tokens;
4. cached input tokens;
5. fresh input tokens;
6. input tokens per successful checkpoint;
7. fresh input tokens per successful checkpoint;
8. output tokens;
9. context epochs and rotations;
10. manual relays;
11. true human gates;
12. wall time per successful checkpoint.

## Protocol discipline

Freeze policy thresholds before formal comparison. Keep the validator independent from
the runtime condition. Seal raw usage, event, checkpoint, and timing evidence before
analysis.

## Claim boundary

Implementation tests establish behavior, not causal efficiency. A successful pilot does
not establish universal gains. Report negative and neutral results.
