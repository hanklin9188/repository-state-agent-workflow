# Research Methodology

This document defines a conservative evaluation framework for Repository-State Agent Workflow. It treats claimed benefits as hypotheses to test, not conclusions embedded in the design.

## Research objective

Evaluate whether explicit repository-backed continuity and bounded coding-agent sessions can reduce repeated context and stale-state failure without degrading engineering quality or task continuity.

## Research questions

- **RQ1 — Context efficiency:** How much does the workflow reduce fresh-session and repeated-call context traffic?
- **RQ2 — Continuity:** Can a fresh agent resume the correct task without hidden conversational state?
- **RQ3 — Reliability:** Does the workflow reduce stale-state errors and repeated work?
- **RQ4 — Quality:** Are task completion, tests, and review outcomes maintained or improved?
- **RQ5 — Handoff:** Can builders, reviewers, humans, and different agent systems exchange work successfully?
- **RQ6 — Boundary conditions:** Which task and repository characteristics make the workflow useful or costly?

## Falsifiable hypotheses

- **H1:** Median repeated context traffic is lower under repository-state sessions than under long-conversation sessions for matched tasks.
- **H2:** Fresh-session continuation success is non-inferior under the repository-state workflow.
- **H3:** Repeated investigation and stale-state errors occur less frequently.
- **H4:** Closure-validation success and independent-review findings do not degrade.
- **H5:** Benefits are larger for multi-ticket, long-running, or role-separated work than for small one-shot tasks.

A valid study must allow these hypotheses to be rejected.

## Experimental unit

The primary unit should normally be a task or matched task stream, not an individual model call. Repeated calls within one task are correlated and should not be treated as independent samples.

## Candidate study designs

### Paired within-repository comparison

Match similar tasks in one repository and alternate workflows. Control model, reasoning mode, tool permissions, test environment, and task complexity as closely as practical.

### Interrupted continuation test

Stop a builder at a preregistered boundary. Start a fresh agent with only repository state and measure whether it identifies the correct task, evidence, next action, and stop condition.

### Cross-agent handoff

Use one agent as builder and another as reviewer or continuation agent. Record hidden-context requests and handoff failures.

### Longitudinal case study

Measure one repository before and after migration. Report task mix and environmental changes; do not interpret a single case as universal evidence.

## Required baselines

At minimum compare against one clearly specified baseline:

- a continuous long conversation;
- a conversation plus manually written summary;
- an issue-tracker-only workflow;
- another persistent-memory system.

Do not label a baseline “standard agent workflow” without specifying its context, prompts, and handoff process.

## Metrics

### Context and cost

- bootstrap tokens;
- average and maximum active-context tokens per call;
- total repeated context traffic;
- cached and uncached inputs where available;
- output tokens;
- tool-output volume;
- monetary cost where provider accounting is available.

### Continuity

- active-task identification accuracy;
- next-action identification accuracy;
- verified-state recognition;
- unnecessary file reads;
- requests for hidden prior-conversation information;
- time to productive first edit.

### Engineering quality

- task completion;
- targeted and closure test results;
- independent review findings;
- escaped defects;
- regression rate;
- spec-compliance findings;
- rework after review.

### Process quality

- repeated investigation rate;
- stale-state incidents;
- session count;
- human interventions;
- blocker-handling quality;
- long-running polling volume;
- handoff document size and freshness.

## Suggested event schema

A study should preserve task-level records containing:

```text
task_id
repository_revision
workflow_condition
agent_model
reasoning_mode
tool_permissions
session_id
session_role
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

Store only data permitted by project privacy and security policy.

## Development and evaluation separation

If prompts, templates, context budgets, or verifier rules are tuned during a pilot, use separate tasks or repositories for confirmation. Do not tune the workflow and report the same tasks as untouched evaluation.

## Statistical analysis

The exact analysis depends on task count and pairing. Prefer:

- paired task-level differences;
- medians and robust intervals for skewed token/cost data;
- explicit non-inferiority margins for quality metrics;
- bootstrap confidence intervals where assumptions are appropriate;
- qualitative failure taxonomy for low-frequency but important continuity errors.

Do not treat every model call as an independent observation.

## Threats to validity

### Selection bias

Teams may adopt the workflow on unusually difficult projects. Report repository and task characteristics.

### Learning effects

Agents or maintainers may improve over time independent of the workflow. Counterbalance task order where possible.

### Model drift

Model versions and provider behavior change. Pin or record exact versions and dates.

### Instrumentation effects

Measuring tokens, files, or tool calls may alter behavior. Document instrumentation.

### Contamination

A model may have seen public issues or repository content during training. Use fresh private or held-out tasks where appropriate.

### Generalizability

Results from one language, repository, organization, or agent should not be generalized without replication.

## Reporting standard

Publish:

- workflow version and commit;
- baseline prompt and state strategy;
- task selection procedure;
- excluded/failed tasks;
- raw or redacted aggregate data as policy permits;
- context accounting assumptions;
- quality and continuity outcomes;
- negative results and limitations.

Use [Case Study Template](case-study-template.md) for a consistent report.

## Related motivation

Long-context research has shown that access to relevant information can degrade with context placement and length, while repository-level software tasks require coordinated reasoning across many files and execution steps. RSAW tests an engineering response: keep the default context small, explicit, and task-relevant, then expand it on demand. See [References](references.md).
