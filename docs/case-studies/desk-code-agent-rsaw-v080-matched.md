# Desk Code Agent — RSAW v0.8.0 Matched Workflow Evaluation

## Status

**Post-release matched evidence with a separately labelled post-hoc sensitivity
analysis.** The preregistered primary result remains authoritative and is not
rewritten by the later failure attribution.

## Study metadata

- Repository: `hanklin9188/Desk-Code-Agent`
- RSAW release: `v0.8.0`
- RSAW commit: `b9759c40532689d91606b5643d4be8c809f4598d`
- Baseline: direct Codex (`NO_RSAW`)
- Treatment: exact commit-pinned `RSAW_V080`
- Model: `gpt-5.6-sol`
- Reasoning: Medium
- Formal attempts: 48
- Study date: 2026-08-17

## Research question

Does commit-pinned RSAW v0.8.0 improve successful-work efficiency or continuity
without materially reducing semantic success or safety versus direct Codex?

## Matched design

The study used six repository-disjoint workflow fixtures. Each workstream had
four checkpoints:

1. repository map;
2. change plan;
3. implementation;
4. readiness review.

Every checkpoint was executed once under both conditions, producing 24 attempts
per condition. Condition order alternated by workstream. Model, reasoning,
checkpoint text, fixture bytes and Git revision, sandbox, timeout, semantic
oracle, focused validation, host, and safety audit were held constant. The
model-promotion holdout was excluded.

The 48-attempt formal run completed with zero harness failures.

## Implementation validation

Before the matched run, the exact v0.8.0 install resolved to the pinned commit
and passed:

- 121/121 upstream tests;
- Ruff;
- the deterministic relevance benchmark.

The deterministic relevance fixture reduced model-visible context from 36,712
to 252 tokens (99.31%) while retaining the target implementation, rejecting
test, and support evidence. The second index build reused 43/43 cached entries.
That result validates the mechanism; it is not the matched product result.

## Immutable primary result

| Metric | NO_RSAW | RSAW v0.8.0 |
|---|---:|---:|
| Successful checkpoints | 22/24 | 17/24 |
| Success rate | 91.67% | 70.83% |
| Input tokens / success | 242,400 | 171,296 |
| Uncached input tokens / success | 25,429 | 24,970 |
| Active seconds / success | 32.71 | 54.55 |
| Broad-discovery commands | 12 | 0 |
| Raw tool calls | 196 | 214 |

The preregistered decision was:

`RSAW_V080_VALUE_NOT_DEMONSTRATED`

McNemar had five control-only successes, zero RSAW-only successes, and a
two-sided exact `p = 0.0625`. The workstream-bootstrap RSAW-minus-control success
delta was -20.83 percentage points, with a 95% interval from -37.50 to -4.17
points.

Formal attempts SHA-256:

`1650e6346c38006303fade819aa3984dc226d14736551a52644e028d287ce84b`

Primary comparison SHA-256:

`1c57a7a607ef07933e07088d3233f546444dcabd9ccf5139d8d89521c038d0ce`

## Why the primary result looked worse

A later independent inspection found two measurement defects. The original
record remains unchanged.

### Safety-classifier false positives

Twelve findings across both conditions were repository-local, read-only
validation commands rejected by the fail-closed command classifier. Eleven
were counted against RSAW's primary safety gate and one occurred in the control.
The commands were local Python JSON/assertion checks or fixed-string grep against
the checkpoint's allowed artifact; they performed no network, external-path,
destructive, secret, or authority-bypass action.

### Equivalent implementation rejected by a structural oracle

Both conditions implemented SHA-256 verification with:

- an exact 64-character requirement;
- a lowercase hexadecimal character whitelist;
- SHA-256 `hexdigest`;
- `hmac.compare_digest`.

The frozen oracle accepted a regex form but not the equivalent character
whitelist. Fresh focused validation passed 20/20 tests in both conditions.

Because these dispositions were made after formal results were observed, the
recalculation below is a **post-hoc sensitivity analysis**. It does not replace
the primary result.

## Equal-quality sensitivity result

| Metric | NO_RSAW | RSAW v0.8.0 | RSAW relative change |
|---|---:|---:|---:|
| Successful checkpoints | 24/24 | 24/24 | equal |
| Total input tokens | 5,332,809 | 2,912,039 | 45.39% lower |
| Uncached input tokens / success | 23,310 | 17,687 | 24.12% lower |
| Output tokens / success | 2,604 | 2,014 | 22.68% lower |
| Broad-discovery commands | 12 | 0 | 100% lower |
| Active seconds / success | 29.99 | 38.64 | 28.87% higher |
| Raw tool calls | 196 | 214 | 9.18% higher |
| Fresh contexts | 6 | 17 | 183.33% higher |

RSAW runtime checkpoint validity was 24/24 and Focus target recall was 100%.
However, the runtime performed 24 Focus builds with zero Focus reuse, five
context compactions, six role rotations, and 17 fresh contexts. These lifecycle
costs are the most plausible source of the elapsed-time regression despite the
large input-token reduction.

## Decision

The study supports:

`OPT_IN_RETRIEVAL_HEAVY_LONG_WORKSTREAM_PILOT_ONLY`

RSAW v0.8.0 has demonstrated value when the dominant cost is repeated repository
discovery or provider input. It has not demonstrated universal default-workflow
value for short four-checkpoint workstreams. The 28.87% active-time regression
exceeds the preregistered 20% compensating-regression limit.

Broader adoption should first reduce lifecycle overhead by reusing Focus/index
state across checkpoints and avoiding unnecessary compactions and rotations.
A confirmation study should use new fixtures, independently validated action
classification and semantic oracles, and separate short-task from
retrieval-heavy strata.

## Threats to validity

- The sensitivity attribution is post-hoc and cannot replace the primary result.
- Six workstreams provide bounded operational evidence, not a universal claim.
- The study compared direct Codex with v0.8.0; v0.7.1 was not included.
- Workflow instrumentation itself may influence elapsed time and tool behavior.
- Aggregate evidence is published here; raw model event streams and outputs are
  retained by the source study and are not included in this repository.

## Reproducibility artifacts

- [Machine-readable aggregate](../../data/case-studies/desk-code-agent-rsaw-v080-matched.json)
- [Evaluation framework](../evaluation.md)
- [Research methodology](../research-methodology.md)
- [Case-study template](../case-study-template.md)
