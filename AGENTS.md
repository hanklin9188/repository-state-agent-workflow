# RSAW Agent Contract — v0.8

RSAW is a repository-state runtime for long-lived agent workstreams.

## Authority

Use this order:

1. executable repository contracts and immutable evidence;
2. accepted task and workstream specifications;
3. `.rsaw/state/` durable runtime artifacts;
4. `ACTIVE.md` compatibility pointer;
5. current conversation context.

Repository state wins over remembered chat history.

## Supervised execution

When `RSAW_SUPERVISED=1` is present:

- do **not** edit `ACTIVE.md`;
- do **not** invoke a state-advancement command;
- do semantic engineering work only for the active task;
- inspect the compiled Truth and Focus context before repository discovery;
- use narrow exact queries only for a concrete unresolved question;
- keep tool output bounded and store large output as an artifact;
- run task-relevant validation;
- return exactly one typed `rsaw.checkpoint-result.v1` JSON object;
- never claim validation or artifacts that were not produced;
- never expose hidden chain-of-thought.

The Supervisor owns checkpoint numbering, state advancement, hashes, lifecycle transitions,
evidence sealing, review manifests, and fail-closed gates.

## Context model

```text
Truth → Focus → Work → Checkpoint
```

- **Truth:** exact governance, task contract, state, capsule, and required evidence;
- **Focus:** deterministic structural map and bounded source excerpts;
- **Work:** semantic implementation and validation;
- **Checkpoint:** verified transactional durability.

Do not use broad repository discovery when Focus already answers the question. Do not reread
unchanged files or reintroduce a long tool result merely because it existed earlier.

## Lifecycle

- `CONTINUE` — same role and coherent objective;
- `COMPACT` — same objective, replace an expensive hot context;
- `ROTATE` — fresh cognitive boundary for role, objective, or sandbox change;
- `PAUSE` — a real human, external, privilege, or safety gate;
- `COMPLETE` — the durable stop condition is satisfied.

Checkpoint is a durability boundary. Context epoch is a cognitive boundary.

## Validation and evidence

Validation is a deterministic gate, not narration. Preserve command provenance, exit status,
artifact paths, checksums, source revisions, allowed-write scope, and evidence identifiers.
A fresh reviewer receives bounded evidence and state, not private reasoning history.

## Safety

- Never infer authorization, credentials, privilege, or destructive consent.
- Never bypass the configured sandbox to save time or tokens.
- Never consume one-shot authority before readiness passes.
- Do not busy-poll external work; persist the gate and pause.
- Do not reset, clean, restore, or overwrite unrelated worktree changes.
- Focus selection never promotes code, smoke output, or diagnostics into scientific evidence.

## Optimization target

Persist aggressively. Select relevance before inference. Compact expensive context at safe
boundaries. Optimize total, cached, and fresh input per successful checkpoint while
preserving matched semantic success.
