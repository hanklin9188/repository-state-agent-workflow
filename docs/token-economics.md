# Token Economics

RSAW optimizes repeated context traffic, not a provider's private caching implementation.

## Context traffic

A simplified task-stream estimate is:

```text
Total input context ≈ Σ input_context_at_call_i
```

An always-persistent context may grow continuously. An always-fresh workflow resets often but repeatedly pays bootstrap and re-understanding cost. RSAW 0.2 attempts to retain context only across tasks where continuity has clear value.

## Three conceptual costs

### Always persistent

```text
low handoff cost
+ high accumulated-history cost
+ stale-context risk
```

### RSAW 0.1 always fresh

```text
low accumulated-history cost
+ repeated bootstrap/re-reading cost
+ possible handoff loss
```

### RSAW 0.2 adaptive epoch

```text
amortized bootstrap across adjacent tasks
+ bounded context growth
+ explicit rotation cost
```

## Illustrative example

Suppose three closely coupled tasks each require a 3K bootstrap.

```text
Always fresh:
3K + 3K + 3K = 9K bootstrap

One context epoch:
3K initial bootstrap + 1K delta + 1K delta = 5K
```

This suggests a 44% bootstrap/handoff reduction for that example. It is not measured RSAW 0.2 evidence.

## Existing measured result

The Desk Code Agent RSAW 0.1 case study reports a deterministic bootstrap estimate of 33,348 → 2,967 tokens, or −91.1%.

That result is not full-task token saving, cached-input saving, or billing saving.

## Recommended evaluation target

Use:

```text
Total input tokens / successfully closed tasks
```

alongside completion, V2 closure, review findings, stale-state errors, human intervention, and elapsed time.

## Real-world caveats

Actual cost depends on provider cache behavior, tool output, retries, model reasoning, task complexity, context retention, and whether rotation triggers are followed.

## Suggested budgets

- `ACTIVE.md`: ≤140 lines and ≤12 KB
- stable `AGENTS.md`: target ≤250 lines
- active task: target ≤200 lines
- fresh bootstrap: preferably ≤5K tokens after project customization
- routine context epoch: 20K–40K
- rotation recommended: 50K–60K
- routine hard ceiling: ~80K unless justified

These are operating hypotheses and local engineering budgets—not universal model limits.
