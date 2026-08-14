# Evaluating Context Epochs

Persistent Workstream mode changes the research question from:

> Can fresh sessions reduce bootstrap context?

into:

> When should useful context be retained, and when should it be rotated?

This document defines a matched evaluation for that question.

## Compared workflows

### A. Chat-as-memory

One growing conversation carries project continuity.

### B. RSAW bounded sessions

Every substantial task starts from a fresh three-file bootstrap.

### C. RSAW persistent workstream

Closely coupled tasks may share a bounded context epoch. Rotation follows the
repository continuation policy.

## Primary unit

Use a successfully closed task or matched task stream—not an individual model
call—as the primary unit.

## Required metrics

### Context and cost

- total input tokens;
- cached input tokens where provider accounting is available;
- output tokens;
- bootstrap tokens;
- repeated file reads;
- tokens per successfully closed task.

### Quality

- task completion rate;
- acceptance-test pass rate;
- closure-validation pass rate;
- fresh-reviewer findings;
- escaped defects;
- stale-state errors;
- repeated work.

### Operations

- elapsed time;
- model calls;
- human interventions;
- handoff success;
- rotation count;
- context epoch length.

## Hypotheses

### H1 — Bounded sessions versus chat-as-memory

Repository-backed fresh sessions reduce repeated historical context without
reducing task-closure quality.

### H2 — Persistent workstreams versus always-fresh RSAW

Adaptive context epochs reduce repeated bootstrap and subsystem re-reading for
closely coupled tasks while preserving closure quality.

### H3 — Rotation quality

Hard rotation at role, scientific, debugging, human, and long-running boundaries
reduces stale-state and confirmation-bias errors relative to an always-persistent
context.

## Matched task-stream design

Use task streams that naturally contain adjacent work and hard boundaries, for
example:

```text
design
→ implementation
→ smoke
→ readiness
→ formal execution
→ scientific analysis
```

Hold constant where practical:

- repository revision;
- task specifications;
- model and reasoning mode;
- tool permissions;
- validation requirements;
- time and compute budget.

Randomize workflow assignment across comparable task streams or use a
counterbalanced crossover design.

## Rotation policies

Evaluate at least:

1. always fresh;
2. always persistent;
3. fixed-N task rotation;
4. RSAW continuation gate.

The RSAW gate should remain deterministic for the first study:

```text
role change              → ROTATE_REQUIRED
scientific phase change  → ROTATE_REQUIRED
major debugging residue  → ROTATE_REQUIRED
human gate               → ROTATE_REQUIRED
long-running-only wait   → ROTATE_REQUIRED
context >= hard budget   → ROTATE_REQUIRED
context >= soft budget   → ROTATE_RECOMMENDED
otherwise                → CONTINUE
```

## Reporting

Report distributions and task-stream-level outcomes, not only averages.

At minimum include:

- median and tail input tokens;
- task closure rate;
- reviewer-found defects;
- repeated-read count;
- human interventions;
- elapsed time;
- rotation reasons;
- workload characteristics.

## Claim boundaries

A bootstrap reduction is not automatically:

- provider billing savings;
- cached-input savings;
- total-task savings;
- evidence of higher quality.

Persistent Workstream mode should not claim token savings or quality improvement
until matched task-stream evidence exists.

The preferred efficiency metric is:

```text
successfully closed tasks
─────────────────────────
     token or cost budget
```

rather than token count alone.
