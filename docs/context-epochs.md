# Context Epochs

A **Context Epoch** is one bounded model context that completes one or more closely related tasks.

It is the middle ground between two expensive extremes:

- **always persistent**: context grows until stale history dominates;
- **always fresh**: every small task pays bootstrap and re-understanding cost.

## Task boundary versus context boundary

A task boundary always creates a durable checkpoint.

A context boundary is a rotation decision.

```text
Task complete
→ checkpoint
→ ACTIVE update
→ continuation gate
   ├─ continue in current epoch
   └─ rotate to a fresh epoch
```

Therefore:

```text
Task ≠ Context Epoch
```

## Good multi-task epochs

- design → implementation → targeted integration → smoke;
- migration step → focused verification → readiness;
- dataset preparation → training setup → smoke;
- experiment analysis → next experiment specification, when no independence rule is crossed.

## Hard rotation boundaries

- Builder → Reviewer;
- Builder → Formal Runner;
- Formal Runner → Scientific Analyst;
- Preregistration → Formal Execution;
- measured result → follow-up scientific redesign;
- large debugging episode completed;
- human gate;
- long-running work is the only remaining blocker;
- governing specification changed materially.

## Context budget

RSAW cannot read provider-private context accounting automatically. Projects should use explicit operating budgets and honest human/agent estimates.

Recommended starting policy:

| Level | Guidance |
|---|---|
| 20K–40K | Healthy routine epoch |
| 50K–60K | Rotate unless continuity has clear value |
| >80K | Treat as a workflow failure unless justified |

Role and scientific boundaries override token budgets: rotate even when the context is small.

## Checkpoint discipline

Continuing in the same context does not permit hidden state to become authority. Before the next task:

- update the task state;
- record evidence pointers;
- update `ACTIVE.md`;
- make the next task independently executable;
- run `rsaw verify .` and `rsaw next .`.

A later fresh agent should be able to resume without the current conversation.
