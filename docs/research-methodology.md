# Research Methodology

This document treats RSAW benefits as hypotheses to test, not conclusions embedded in the design.

## Research objective

Evaluate whether repository-backed continuity and adaptive context epochs reduce context cost, repeated work, and stale-state failure without degrading successful task closure or independent review quality.

## Research questions

- **RQ1 — Context efficiency:** How do always-persistent, always-fresh, and adaptive-epoch workflows differ in task-stream input cost?
- **RQ2 — Retention value:** Which adjacent tasks benefit from retaining context?
- **RQ3 — Rotation value:** Which boundaries benefit from a fresh context?
- **RQ4 — Continuity:** Can a fresh agent resume correctly from repository state?
- **RQ5 — Reliability:** Does RSAW reduce stale-state errors and repeated investigation?
- **RQ6 — Quality:** Are task completion, closure validation, and review outcomes maintained or improved?
- **RQ7 — Boundary conditions:** Which repository, task, model, and role characteristics predict benefit or harm?

## Required workflow conditions

A strong RSAW 0.2 study should compare:

### A. Always persistent

One growing conversation or context retains all prior task history.

### B. RSAW 0.1 / always fresh

Every substantial task checkpoints and rotates.

### C. RSAW 0.2 / adaptive epoch

Every task checkpoints; adjacent tasks may continue when the explicit gate permits it.

Specify prompts, rotation policy, tool permissions, and hidden state for every condition.

## Falsifiable hypotheses

- **H1:** RSAW 0.2 lowers median total input tokens per successfully closed task relative to always persistent.
- **H2:** RSAW 0.2 lowers bootstrap and repeated-read overhead relative to RSAW 0.1 for closely coupled task streams.
- **H3:** RSAW 0.2 is non-inferior on task completion and closure validation.
- **H4:** Hard rotation rules preserve reviewer and scientific independence.
- **H5:** Adaptive epochs reduce repeated investigation without increasing stale-state errors.
- **H6:** Benefits vary with task coupling, role boundaries, debugging residue, and repository size.

A valid study must allow every hypothesis to be rejected.

## Experimental unit

The primary unit is normally a matched task stream or successfully closed task—not a model call. Repeated calls, tools, and edits within one task are correlated.

## Primary metric

```text
Total input tokens / successfully closed tasks
```

Report failure counts separately. Do not divide only by attempted tasks.

## Secondary metrics

### Context and cost

- bootstrap and routine working-set estimates;
- total input;
- cached and uncached input where available;
- output and tool-result volume;
- monetary cost;
- maximum epoch size;
- tasks per epoch.

### Continuity

- active-task identification;
- next-action identification;
- verified-state recognition;
- unnecessary reads;
- requests for hidden conversation;
- time to productive first edit.

### Engineering quality

- completion;
- V1/V2 results;
- independent review findings;
- escaped defects;
- spec-compliance findings;
- rework after review.

### Rotation quality

- continuation/rotation decisions;
- hard-boundary compliance;
- false continuation and false rotation taxonomy;
- stale-context incidents;
- handoff loss;
- human gates.

## Candidate study designs

### Paired task streams

Use comparable task sequences in one repository and counterbalance workflow order.

### Interrupted continuation

Stop at a preregistered checkpoint. Test whether a fresh context identifies the correct task, evidence, next action, gate, and role.

### Context-retention ablation

Hold the repository state constant while varying context retention across adjacent tasks.

### Cross-agent role handoff

Use separate Builder, Reviewer, Runner, or Analyst agents and record hidden-context requests and review defects.

### Longitudinal case study

Measure one repository before and after adoption. Report task mix and environment changes; do not generalize one case universally.

## Event schema

A task-level record should include:

```text
task_id
workstream_id
epoch_id
repository_revision
workflow_condition
agent_model
reasoning_mode
role
continuation_decision
rotation_reason
context_tokens
cached_tokens
output_tokens
files_read
commands_run
validation_results
completion_state
review_findings
human_interventions
elapsed_time
```

Store only data permitted by project security and privacy policy.

## Development and confirmation

If continuation rules, budgets, prompts, templates, or verifier behavior are tuned on a pilot, use separate task streams or repositories for confirmation.

## Statistical analysis

Prefer:

- paired task-stream differences;
- medians and robust intervals for skewed token/cost data;
- explicit non-inferiority margins for quality;
- bootstrap intervals at the task or task-stream unit;
- failure taxonomy for rare but important stale-state and handoff errors.

Do not treat model calls as independent observations.

## Threats to validity

- task-selection and repository-selection bias;
- learning and ordering effects;
- model/provider drift;
- instrumentation effects;
- public-repository contamination;
- inaccurate token estimates when provider accounting is unavailable;
- workflow noncompliance;
- limited generalizability across languages, agents, and organizations.

## Reporting standard

Publish workflow version, commit, baseline prompts, task selection, excluded tasks, failures, context-accounting assumptions, quality outcomes, rotation decisions, limitations, and negative results.

Use [Case Study Template](case-study-template.md) for a consistent report.
