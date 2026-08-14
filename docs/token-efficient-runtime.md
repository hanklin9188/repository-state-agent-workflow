# Token-Efficient Runtime Design

## Product goal

Provide more operator visibility while reducing unnecessary model context traffic.

## Mechanisms

- repository-backed durable state;
- explicit context manifests;
- stable-prefix and dynamic-authority separation;
- continuation prompts that avoid rereading unchanged policy;
- deterministic cache-aware rotation;
- checkpoint-normalized token reporting;
- local TUI rendering with zero intentional model-token overhead.

## Primary KPI

```text
fresh input tokens / successful checkpoint
```

Supporting metrics:

- successful checkpoint rate;
- total input;
- cached input;
- fresh input;
- output;
- turns and epochs;
- rotations;
- manual relays;
- wall time per successful checkpoint.

## Non-goals

- maximizing cache hit rate regardless of relevance;
- replacing provider token accounting;
- weakening role/scientific boundaries;
- inferring human authorization;
- claiming a causal improvement before a matched prospective study.

## Evaluation

Compare the same task, model, repository revision, permissions, validation oracle, and
starting state. Separate implementation correctness from causal efficiency claims.
