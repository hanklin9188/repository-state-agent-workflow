# Company Adoption and Governance

Repository-State Agent Workflow is designed for engineering organizations that want agent productivity without making a model conversation an ungoverned system of record.

## Executive summary

The operating model is simple:

```text
Stable policy        → AGENTS.md
Current handoff      → ACTIVE.md
Current work contract→ task spec
Durable evidence     → Git, tests, ADRs, reports, artifacts
```

This gives teams an inspectable continuity layer that can be reviewed, versioned, secured, and used by multiple agent vendors.

## Business and engineering value

### Reduced hidden state

A long conversation is difficult to audit and difficult to transfer. Repository state is visible to engineers, reviewers, CI, and future agents.

### Vendor and model portability

The workflow does not require one model provider. A team can change agents without losing the project’s continuation contract.

### Bounded operational risk

One substantial task per session makes the intended change surface, validation boundary, and stop condition explicit.

### Cleaner review and accountability

The reviewer receives a task contract, diff, validation evidence, known limitations, and explicit review questions. The builder’s full debugging transcript is intentionally excluded unless needed.

### Lower unnecessary data exposure

Progressive disclosure minimizes broad repository, log, or customer-data loading. This does not replace access control, but it reduces the default context footprint.

## What RSAW does not replace

RSAW complements rather than replaces:

- GitHub Issues, Linear, Jira, or internal trackers;
- code review and branch protections;
- CI/CD;
- security review and secrets management;
- architecture decision records;
- incident management;
- agent orchestration platforms.

The external tracker can remain the planning authority. The active task file becomes the repository-local executable contract for the current agent session.

## Recommended rollout

### Stage 1 — One-repository pilot

Select a repository with:

- recurring agent use;
- several bounded engineering tasks;
- an existing test suite;
- a team willing to maintain `ACTIVE.md` accurately.

Measure a baseline before changing the workflow.

### Stage 2 — Team operating contract

Agree on:

- authority order;
- active task location;
- required validation tiers;
- session stop conditions;
- review responsibilities;
- what information must never enter handoff files.

Add `rsaw verify .` to CI as a fast governance check.

### Stage 3 — Multi-agent or monorepo adoption

Use scoped policy files and independent active-state streams only where teams truly operate independently. Avoid one enormous `ACTIVE.md` for unrelated subprojects.

### Stage 4 — Organization metrics

Track whether the workflow changes:

- repeated investigation;
- context footprint;
- task cycle time;
- review findings;
- escaped defects;
- human intervention;
- stale-state incidents;
- successful handoffs across agents or engineers.

## Governance model

| Layer | Owner | Change control |
|---|---|---|
| Stable policy | Repository maintainers | Reviewed, infrequent |
| Current active state | Active builder/owner | Updated at meaningful boundaries |
| Task contract | Task owner and reviewers | Frozen or versioned during execution |
| ADRs | Architecture owners | Explicit decision process |
| Tests and schemas | Engineering team | Normal code review |
| Raw evidence | Producing system | Immutable or append-only by policy |

## Security and privacy

Do not place these in `ACTIVE.md` or task specs:

- credentials or API keys;
- customer data;
- proprietary raw logs;
- full incident dumps;
- model-provider secrets;
- unrestricted production database output.

Use paths, hashes, redacted evidence, access-controlled systems, or approved secure storage. The workflow defines continuity, not authorization.

## Failure modes to monitor

- `ACTIVE.md` becomes a project diary.
- Multiple documents claim to be current state.
- Agents preload the entire documentation tree anyway.
- Tasks are too broad to close in one session.
- Reviewers inherit the builder’s stale reasoning.
- Validation tiers are used to justify skipping closure tests.
- Long-running jobs are repeatedly polled without productive work.
- Teams optimize token counts while quality deteriorates.

## Adoption success criteria

A pilot is healthy when a fresh authorized engineer or agent can answer, without hidden chat context:

1. What is the active task?
2. What has already been verified?
3. What must be read?
4. What is the next exact action?
5. What stops the session?
6. What evidence closes the task?

If those answers require the prior conversation, the repository-state migration is incomplete.
