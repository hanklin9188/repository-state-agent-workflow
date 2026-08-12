# Token Economics

## Repeated context traffic

A simplified estimate for context processed over a sequence of model calls is:

```text
Total context traffic ≈ Σ context_size_at_call_i
```

A long session often grows over time. A bounded-session workflow resets obsolete context at task boundaries.

## Example

```text
Long session:
180,000 tokens × 30 calls = 5.4M context tokens

Bounded task:
25,000 tokens × 30 calls = 0.75M context tokens

Approximate reduction = 86.1%
```

This is an illustrative context-volume calculation, not a provider billing guarantee.

## Real-world caveats

Actual monetary savings depend on:

- cached-input pricing;
- cache-hit rate;
- provider implementation;
- tool-result size;
- output length;
- number of retries;
- task complexity.

## Quality effect

The workflow can also improve reliability by reducing stale information and increasing the ratio of task-relevant context to historical noise.

## Suggested budgets

- `ACTIVE.md`: ≤120 lines and ≤10 KB
- stable `AGENTS.md`: target ≤250 lines
- active task: target ≤200 lines
- base bootstrap: target ≈15k tokens or less
- routine task working set: target ≈20k–40k tokens

These are soft engineering budgets, not universal limits.
