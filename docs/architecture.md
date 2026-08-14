# Architecture

## Design invariant

```text
Repository authority > runtime state > model context > presentation
```

RSAW 0.5 separates six layers:

1. **Repository authority** — `AGENTS.md`, accepted decisions, `ACTIVE.md`, active task.
2. **Context planner** — ordered, fingerprinted, budgeted read manifest.
3. **Continuation engine** — CONTINUE / ROTATE / PAUSE / COMPLETE.
4. **Runtime supervisor** — bounded Codex turns, verification, locks, limits.
5. **Telemetry** — provider usage, checkpoints, transitions, evidence paths.
6. **Live console** — non-authoritative operator presentation.

![RSAW 0.5 architecture](assets/runtime-architecture-v05.svg)

## Data flow

```text
AGENTS + ACTIVE + task
        ↓
ContextPlan
        ↓
Fresh prompt or continuation delta
        ↓
Codex exec / resume
        ↓
Structured events + repository mutation
        ↓
Verification + checkpoint
        ↓
Deterministic rotation evaluation
        ↓
CONTINUE / ROTATE / PAUSE / COMPLETE
```

## Context-plan authority

The planner does not decide project truth. It serializes the files already authorized
by repository state, removes duplicates, verifies repository locality, records hashes,
and checks an operating budget.

## Rotation authority

Mandatory role/scientific boundaries come from repository state. Runtime pressure is
deterministic and uses configured thresholds plus provider-emitted usage. The model
never chooses whether its own context should survive.

## Presentation isolation

Codex and supervisor event sinks are best-effort. Exceptions in the Live Console are
caught and cannot alter the worker, checkpoint verification, or lifecycle result.

## Compatibility

The 0.4 flat `rotate_input_tokens` field remains accepted. New repositories receive
schema version 2 with explicit `context` and `rotation` sections.
