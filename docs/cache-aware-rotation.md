# Cache-Aware Rotation

## Objective

Preserve useful task-local cache reuse without carrying obsolete context indefinitely.

## Decision order

Repository-declared boundaries remain authoritative. When continuation is otherwise
allowed, RSAW evaluates runtime pressure in this order:

1. maximum turns per epoch;
2. hard latest-turn input threshold;
3. maximum fresh/uncached input;
4. soft threshold combined with low cache reuse;
5. continue when cache locality remains acceptable.

## Metrics

```text
fresh_input = max(0, input_tokens - cached_input_tokens)
cache_reuse_ratio = cached_input_tokens / input_tokens
```

Missing usage does not trigger a cache-quality rotation. Hard role, review, safety, and
scientific boundaries still rotate independently of token telemetry.

## Why both soft and hard thresholds

A hard threshold bounds context size. A soft threshold permits continuation when the
prefix is still highly reusable, but rotates earlier when a large input carries little
useful cache reuse.

## Configuration

```json
{
  "runtime": {
    "rotation": {
      "soft_input_tokens": 48000,
      "hard_input_tokens": 60000,
      "max_fresh_input_tokens": 18000,
      "min_cache_reuse_ratio": 0.5
    }
  }
}
```

These are conservative operating defaults, not universal optima. Calibrate them with
matched tasks and report fresh input per successful checkpoint.
