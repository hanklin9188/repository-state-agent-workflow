# Evaluate the Workflow

The workflow should be evaluated by more than token counts. A smaller context that produces worse code is not a successful result.

For a preregistration-oriented study design, metrics, statistical considerations, and threats to validity, see [Research Methodology](research-methodology.md). For a reusable report structure, see [Case Study Template](case-study-template.md).

## Current adoption evidence

The first documented real-project adoption measurement is available in [Desk Code Agent — RSAW V1 Bootstrap Context Case Study](case-studies/desk-code-agent-rsaw-v1-bootstrap.md).

At V1, `rsaw verify` passed and the deterministic fresh-session bootstrap estimate changed from a previous-policy lower bound of **33,348 tokens** to **2,967 tokens** under the RSAW three-file bootstrap (`AGENTS.md` 1,639; `ACTIVE.md` 432; active task 896). That is an estimated reduction of **30,381 tokens / 91.10%**.

This result is explicitly labeled `BOOTSTRAP_CONTEXT_ESTIMATE`. It is not provider billing savings, cached-input savings, or a full-task quality result. V2 closure and task-level continuity/quality measurements are still required before broader claims.

Machine-readable data: [`../data/case-studies/desk-code-agent-rsaw-v1.json`](../data/case-studies/desk-code-agent-rsaw-v1.json).

## Before/after measures

### Context footprint

Record approximate fresh-session bootstrap and routine working-set sizes.

```bash
rsaw footprint . --json
```

Where provider accounting is available, distinguish cached input, uncached input, output, and tool-result volume.

### Continuity success

Can a fresh builder answer, without prior chat history:

- What is the active task?
- What is already verified?
- What must be read?
- What exact action is next?
- When should it stop?

### Repeated-work rate

Track whether agents repeat already completed investigation, tests, implementation, or failed approaches without new evidence.

### Stale-state errors

Track defects caused by following obsolete source, decisions, protocols, requirements, or historical task state.

### Handoff quality

Measure whether fresh reviewers and builders can continue without hidden conversational knowledge.

### Engineering quality

Compare:

- task completion rate;
- test failures at closure;
- defect escape rate;
- review findings;
- spec-compliance findings;
- time to recover from interruption;
- human interventions.

## Fresh-session simulation

A practical repository check uses three no-history simulations:

1. **Builder:** identify task, prerequisites, next action, and stop condition.
2. **Reviewer:** identify governing spec, diff, evidence, and review questions without builder history.
3. **Decision:** locate observed facts, constraints, options, and missing evidence without loading all project history.

A workflow that requires hidden conversation context fails the continuity test.

## Suggested case-study structure

1. Project type and size
2. Agent/tool and reasoning mode
3. Original state and session pattern
4. Repository-state migration
5. Task sample and baseline
6. Context before/after
7. Continuity and quality results
8. Failure analysis
9. Limitations and threats to validity
10. Changes made after adoption

Do not claim universal token or quality improvements from one repository. Publish the task mix, assumptions, measurement method, failures, and uncertainty.
