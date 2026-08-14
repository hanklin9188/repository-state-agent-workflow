# Company Adoption and Governance

RSAW gives engineering organizations agent continuity without making a model conversation an ungoverned system of record.

## Operating model

```text
Stable policy          → AGENTS.md
Long-range roadmap     → workstream spec
Current frontier       → ACTIVE.md
Bounded work contract  → task spec
Durable evidence       → Git, CI, ADRs, reports, artifacts
Context retention      → explicit continuation gate
```

## Why persistent workstreams help

### Lower hidden-state risk

Project state is visible, reviewable, versioned, and portable across agents and vendors.

### Less unnecessary reboot cost

Closely coupled Builder tasks can share one Context Epoch instead of repeatedly reloading the same subsystem.

### Bounded context growth

Hard rotation boundaries prevent a multi-week workstream from becoming a multi-week model conversation.

### Cleaner accountability

Every task checkpoint records evidence, next action, next task, role, and gate decision.

### Lower default data exposure

Progressive disclosure reduces broad repository and log loading. It complements—but does not replace—access control.

## RSAW does not replace

- GitHub Issues, Linear, Jira, or internal trackers;
- code review and branch protection;
- CI/CD;
- secrets management and security review;
- ADRs and incident management;
- agent orchestration platforms.

## Recommended rollout

### Stage 1 — One workstream pilot

Choose a feature, migration, experiment series, or release train with real tests and multiple adjacent tasks.

### Stage 2 — Conservative rotation

Start with `ROTATE_REQUIRED`. Enable continuation only for tightly coupled Builder tasks.

### Stage 3 — Team contract

Agree on authority order, role boundaries, validation tiers, context budgets, human gates, and prohibited handoff data.

### Stage 4 — Measured evaluation

Track tokens per successfully closed task, repeated reads, stale-state incidents, completion, review findings, human intervention, and elapsed time.

## Governance model

| Layer | Owner | Change control |
|---|---|---|
| Stable policy | Repository maintainers | Reviewed, infrequent |
| Workstream | Workstream owner | Milestone/state-machine changes |
| ACTIVE | Current role owner | Every checkpoint |
| Task contract | Task owner/reviewer | Frozen or versioned during execution |
| Continuation gate | Current role + repository rules | Explicit and auditable |
| Raw evidence | Producing system | Immutable or append-only |

## Security and privacy

Do not place credentials, customer data, proprietary raw logs, incident dumps, provider secrets, or unrestricted production output in workstream, task, or ACTIVE files. Use approved secure storage and reference paths or hashes.

## Failure modes to monitor

- ACTIVE becomes a project diary;
- workstream becomes a duplicate task tracker;
- continuation is always allowed;
- role/scientific boundaries are ignored;
- contexts exceed budget routinely;
- full validation runs after every edit;
- long-running jobs are busy-polled;
- token reduction is optimized while quality declines.

## Adoption success

A fresh authorized engineer or agent should answer:

1. What workstream is active?
2. What task is active?
3. What has been verified?
4. What is next?
5. May the current context continue?
6. What forces rotation or a human stop?
7. What evidence closes the task?

If those answers require hidden chat history, adoption is incomplete.
