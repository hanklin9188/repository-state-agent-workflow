# Evaluate RSAW

RSAW must be evaluated by more than token counts. Smaller context that produces worse work is not a successful result.

## Current evidence

The first documented adoption measurement is [Desk Code Agent — RSAW 0.1 Bootstrap Context](case-studies/desk-code-agent-rsaw-v1-bootstrap.md).

The deterministic bootstrap estimate changed from **33,348** to **2,967 tokens** under the three-file contract, a **91.1%** reduction.

This is explicitly a `BOOTSTRAP_CONTEXT_ESTIMATE`. It is not provider billing savings, cached-input savings, full-task reduction, or a quality result.

Machine-readable data: [`../data/case-studies/desk-code-agent-rsaw-v1.json`](../data/case-studies/desk-code-agent-rsaw-v1.json).

The first v0.8 matched real-workstream result is
[Desk Code Agent — RSAW v0.8.0 Matched Workflow Evaluation](case-studies/desk-code-agent-rsaw-v080-matched.md).
Its 48-attempt immutable primary result did not pass the preregistered value
gate. A separately labelled post-hoc attribution found safety-classifier and
structural-oracle false negatives; under equal attributed completion, RSAW used
45.39% fewer input tokens per success and eliminated broad discovery, but took
28.87% longer per success. The supported disposition is opt-in use for
retrieval-heavy long workstreams, not default activation.

Machine-readable matched data:
[`../data/case-studies/desk-code-agent-rsaw-v080-matched.json`](../data/case-studies/desk-code-agent-rsaw-v080-matched.json).

## RSAW 0.2 evaluation question

RSAW 0.2 introduces adaptive context epochs. The primary comparison should include:

1. **Always persistent** — one growing conversation or context;
2. **Always fresh / RSAW 0.1** — rotate after every substantial task;
3. **Adaptive epoch / RSAW 0.2** — retain context across adjacent tasks and rotate at explicit gates.

## Primary unit

Use a matched task stream or successfully closed task. Calls within one task are correlated and must not be treated as independent samples.

## Primary efficiency metric

```text
Tokens per successfully closed task
```

This prevents a low-token failed task from appearing efficient.

## Context and cost

Measure where available:

- bootstrap context;
- routine working-set context;
- total input tokens;
- cached and uncached input;
- output tokens;
- tool-output volume;
- repeated file reads;
- repeated investigation;
- monetary cost.

## Quality and continuity

Measure:

- task completion;
- V1/V2 closure;
- independent review findings;
- escaped defects;
- stale-state errors;
- correct active-task and next-action identification;
- fresh handoff success;
- human intervention;
- time to productive work.

## Rotation quality

For RSAW 0.2 record:

- continuation decisions;
- rotation reasons;
- tasks per epoch;
- epoch context estimate;
- false continuation: context retained when rotation was needed;
- false rotation: context discarded when retention would have helped;
- role/scientific boundary compliance.

## Matched-study discipline

Control model, reasoning mode, tools, task complexity, repository revision, and validation requirements as closely as practical. Counterbalance workflow order when possible.

If prompts, budgets, or rotation rules are tuned during development, use separate task streams for confirmation.

## Reporting

Publish:

- RSAW version and commit;
- workflow condition;
- baseline prompt and state strategy;
- task selection;
- excluded and failed tasks;
- token-accounting assumptions;
- quality and continuity results;
- human gates;
- limitations and negative results.

See [Research Methodology](research-methodology.md) and [Case Study Template](case-study-template.md).
