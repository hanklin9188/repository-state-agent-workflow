# RSAW 0.4 — Live Runtime Console

## Release objective

Make the automatic Runtime Supervisor understandable during normal day-to-day use
without recreating the native Codex UI or weakening the repository-state model.

## User-visible result

```bash
rsaw run . --agent codex
```

Interactive terminals now receive an in-place console showing:

- current observable work;
- task, role, epoch, checkpoint, and next transition;
- context pressure and input/cached/fresh/output usage;
- recent high-value events;
- durable state, human gate, and elapsed runtime;
- explicit rotation, pause, failure, limit, and completion views.

Use `rsaw preview .` for a non-destructive demonstration and `--no-tui` for plain
output.

## Architecture

The release adds best-effort event sinks from the Supervisor and Codex adapter into
a thread-safe presentation model and Rich Live renderer.

```text
repository + supervisor + Codex JSON events
                    ↓
             DashboardSnapshot
                    ↓
        responsive terminal renderer
```

The renderer is downstream from lifecycle authority. Exceptions in the presentation
path are isolated and cannot fail a valid agent turn.

## Compatibility

Preserved:

- Python 3.10–3.13;
- existing CLI commands and default Codex adapter semantics;
- manual agent-neutral mode;
- CONTINUE, ROTATE, PAUSE, COMPLETE;
- verification, token accounting, limits, and single-supervisor locking;
- non-TTY and CI-friendly plain output.

New dependency:

- `rich>=14.2,<16`.

## Claim boundary

The console adds local observability, not a new context-efficiency mechanism. It
intentionally creates no additional Codex turns and never includes dashboard text in
model prompts. Prospective matched evaluation remains required for causal token,
wall-time, or quality claims.
