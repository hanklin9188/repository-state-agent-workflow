# RSAW Agent Contract — v0.6

RSAW is a repository-state runtime for long-lived agent workstreams.

## Authority

Use this order:

1. executable repository contracts and immutable evidence;
2. accepted task/workstream specifications;
3. `.rsaw/state/` durable runtime artifacts;
4. `ACTIVE.md` compatibility pointer;
5. current conversation context.

Repository state wins over remembered chat history.

## v0.6 supervised execution

When `RSAW_V6=1` or `RSAW_SUPERVISED=1` is present:

- do **not** edit `ACTIVE.md`;
- do **not** run `advance.py` or another state-advancement command;
- do semantic engineering work only for the active task;
- use the compiled context envelope before broad repository rediscovery;
- run task-relevant validation;
- return exactly one typed `rsaw.checkpoint-result.v1` JSON object in the final message;
- never claim a validation or artifact that was not actually produced;
- never expose hidden chain-of-thought.

The Supervisor owns checkpoint numbering, ACTIVE advancement, state hashes, lifecycle transitions, evidence sealing, review manifests, and fail-closed gates.

## Lifecycle

The runtime distinguishes:

- `CONTINUE` — same role, same coherent objective, working context still useful;
- `COMPACT` — same role/objective, preserve semantic state but replace an expensive hot context;
- `ROTATE` — cognitive separation is required, especially Builder → Reviewer and Runner → Analyst;
- `PAUSE` — a real human/external gate blocks progress;
- `COMPLETE` — the workstream stop condition is satisfied.

Checkpoint is a durability boundary. Context epoch is a cognitive boundary. They are not the same thing.

## Context discipline

Use the compiler tiers:

- Tier A: exact objective, acceptance criteria, allowed/forbidden operations, safety constraints, critical source ranges;
- Tier B: Semantic Capsule facts, decisions, exclusions, risks, validation state;
- Tier C: immutable evidence handles for long logs, diffs, transcripts, and historical material.

Prefer read-if-changed and delta context. Do not reintroduce a long tool result merely because it existed in an earlier turn.

## Validation and evidence

Validation is a deterministic gate, not narration. Preserve:

- command provenance;
- actual exit status when available;
- artifact paths and checksums;
- source revision bindings;
- allowed-write scope;
- evidence identifiers.

A fresh reviewer receives a bounded Review Manifest and evidence, not the Builder's private reasoning history.

## Safety

- Never infer authorization, credentials, privilege, or destructive consent.
- Never bypass the configured sandbox to save time or tokens.
- Never consume a one-shot scientific/execution authority before its readiness gate passes.
- Do not busy-poll external work; persist the gate and pause.
- Do not reset, clean, restore, or overwrite unrelated worktree changes.

## Optimization target

Persist aggressively. Infer sparingly. Rotate selectively.

Optimize total provider input per successful checkpoint while preserving matched semantic success. Cache hits are telemetry, not proof of efficiency; aggregate provider input is never used as actual context occupancy.
