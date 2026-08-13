# Desk Code Agent — RSAW V1 Bootstrap Context Case Study

## Status

**Preliminary V1 adoption evidence.** `rsaw verify` passes and the fresh-session bootstrap footprint has been measured. V2 closure, roadmap/navigation cleanup, and broader continuity/quality evaluation are still pending.

This document reports a `BOOTSTRAP_CONTEXT_ESTIMATE`. It is **not** a provider billing-savings claim and does not claim that cached-input charges, total task context traffic, or end-to-end engineering cost fell by the same percentage.

## Study metadata

- Repository: `hanklin9188/Desk-Code-Agent`
- Project type: local-first software engineering desktop workbench
- Workflow intervention: Repository-State Agent Workflow (RSAW)
- RSAW adoption baseline: repository-backed state with `AGENTS.md`, `ACTIVE.md`, and one bounded active task
- Reasoning mode used for the migration: Medium
- Measurement stage: V1
- V1 verifier: PASS
- V2 closure: pending at time of this measurement

## Research question

How much can Desk Code Agent reduce the mandatory fresh-session bootstrap context by replacing its previous broad global-read policy with the RSAW three-file bootstrap contract?

## Baseline workflow

Before RSAW adoption, the Desk Code Agent agent policy required broad project context to be loaded before substantial work, including the master design, execution planning, relevant documentation, skills, decisions, and other project-wide sources of truth.

For this case study, that old mandatory bootstrap was measured as a **deterministic lower bound** of:

`33,348 estimated tokens`

The number is intentionally described as a lower bound rather than an observed provider-side average. It represents the minimum context implied by the previous bootstrap policy under the same deterministic estimation approach used for the migration analysis.

## Repository-state intervention

The RSAW migration changed the default fresh-session bootstrap to:

1. `AGENTS.md` — stable policy and navigation only;
2. `ACTIVE.md` — compact current continuation state;
3. one active task specification referenced by `ACTIVE.md`.

Everything else is read through progressive disclosure only when the active task requires it.

The migration also separates active bootstrap state from roadmap/history: completed plans, historical validation, release evidence, experiments, and broad documentation remain durable repository evidence but are **not default bootstrap context**.

## V1 context result

| Bootstrap component | Estimated tokens |
|---|---:|
| `AGENTS.md` | 1,639 |
| `ACTIVE.md` | 432 |
| Active task | 896 |
| **RSAW fresh bootstrap** | **2,967** |

Comparison with the prior deterministic lower bound:

| Metric | Previous policy | RSAW V1 | Difference |
|---|---:|---:|---:|
| Fresh bootstrap estimate | 33,348 | 2,967 | -30,381 |
| Relative reduction | — | — | **91.10%** |

Calculation:

```text
33,348 - 2,967 = 30,381 estimated tokens
30,381 / 33,348 = 91.10%
```

### Interpretation

The supported conclusion is narrow:

> Under Desk Code Agent's deterministic bootstrap estimator, replacing the previous mandatory global-read policy with the RSAW three-file bootstrap reduced the estimated fresh-session bootstrap from 33,348 to 2,967 tokens, a reduction of 30,381 tokens (91.10%).

This is useful evidence for RSAW's **context-footprint mechanism**: durable repository state can remain available without being injected into every fresh session.

It does **not** yet establish:

- 91.10% lower provider billing;
- 91.10% lower cached-input usage;
- 91.10% lower total context traffic over a complete task;
- faster task completion;
- non-inferior engineering quality;
- lower repeated-work or stale-state error rates.

Those require additional task-level measurement.

## Why this is meaningful

This measurement is stronger than the illustrative token-economics example in the RSAW documentation because it comes from a real, previously long-running software-engineering repository after an actual workflow migration.

It is still preliminary because it measures **bootstrap footprint**, not the full research objective. RSAW is intended to reduce repeated context while preserving continuity and engineering quality; those claims require V2/V3 and task-level evidence.

## V1 verification result

- `rsaw verify`: PASS
- Fresh bootstrap estimate: 2,967 tokens
- Bootstrap composition:
  - `AGENTS.md`: 1,639
  - `ACTIVE.md`: 432
  - active task: 896
- Previous-policy deterministic lower bound: 33,348 tokens
- Estimated reduction: 30,381 tokens
- Estimated relative reduction: 91.10%
- Measurement label: `BOOTSTRAP_CONTEXT_ESTIMATE`

## Pending V2 closure

At the time of this V1 measurement, the next closure work is:

1. mark roadmap/history material explicitly as non-bootstrap context;
2. finish documentation navigation for the repository-state workflow;
3. run V2 closure validation;
4. preserve the resulting verifier/footprint evidence;
5. confirm that the migration did not weaken project validation rules.

## Future evaluation

A stronger Desk Code Agent study should add matched task-level measurements for:

- fresh-session bootstrap tokens;
- routine working-set tokens;
- cached and uncached input where provider accounting is available;
- total model calls;
- output tokens;
- tool-output volume;
- active-task identification;
- correct next-action identification;
- repeated investigation;
- stale-state errors;
- closure-validation outcome;
- independent-review findings;
- human interventions;
- elapsed time.

Quality should be treated as a constraint: lower context is not a successful result if task continuity or engineering quality degrades.

## Threats to validity

### Baseline is a deterministic lower bound

The 33,348-token baseline is not an observed provider billing record. It is a deterministic lower bound derived from the previous mandatory bootstrap policy.

### Bootstrap is not full-task context traffic

The 2,967-token result measures the fresh-session bootstrap only. Progressive disclosure adds task-specific context later.

### Single-repository adoption

This is one repository and one migration. The result should not be generalized to all repositories, models, or agent systems without replication.

### Workflow and repository changed over time

Desk Code Agent evolved substantially before RSAW adoption. Longitudinal comparisons must separate workflow effects from normal project evolution.

### Provider cache behavior is separate

Cached-input/read volume depends on provider implementation, prefix reuse, number of calls, tool outputs, and session shape. The 91.10% bootstrap reduction must not be presented as a direct cached-token or monetary-savings percentage.

## Conclusion

Desk Code Agent provides preliminary real-world evidence that RSAW can dramatically reduce **mandatory fresh-session bootstrap context** while keeping historical repository evidence available through progressive disclosure.

The V1 measurement is:

- previous deterministic lower-bound bootstrap: **33,348 tokens**;
- RSAW bootstrap: **2,967 tokens**;
- estimated reduction: **30,381 tokens**;
- estimated relative reduction: **91.10%**.

This result supports continuing to V2 closure and matched task-level evaluation. It does not by itself establish provider cost savings or non-inferior engineering quality.

## Reproducibility artifacts

- Machine-readable summary: [`../../data/case-studies/desk-code-agent-rsaw-v1.json`](../../data/case-studies/desk-code-agent-rsaw-v1.json)
- Evaluation framework: [`../evaluation.md`](../evaluation.md)
- Research methodology: [`../research-methodology.md`](../research-methodology.md)
- Case-study template: [`../case-study-template.md`](../case-study-template.md)
