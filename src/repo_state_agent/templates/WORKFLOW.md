# Repository-State Workflow

## Authority

`AGENTS.md`, `ACTIVE.md`, the active task, accepted decisions, schemas, tests, and raw
evidence are durable repository authority. Conversation history is not.

## Context Plan

Use `rsaw context .` to inspect the ordered bootstrap:

```text
stable prefix → dynamic authority → bounded required reads
```

Fresh epochs read the full minimal plan. Continued epochs reread dynamic authority and
reuse stable policy only while its fingerprint is unchanged.

## Runtime

Every supervised turn closes one durable checkpoint. Verification then derives
CONTINUE, ROTATE, PAUSE, or COMPLETE. Runtime pressure may force a fresh context, but
must never weaken human, review, or scientific boundaries.

## Measurement

Track total input, cached input, fresh input, output, checkpoints, epochs, rotations,
and wall time. Prefer fresh input per successful checkpoint over cache hit rate alone.
