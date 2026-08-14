# Runtime Supervisor

RSAW Core decides whether repository work should continue, rotate, pause, or
complete. The Runtime Supervisor executes that decision for a local agent. RSAW 0.4
adds a Live Terminal Console downstream from the same deterministic lifecycle.

## Separation of responsibility

```text
Repository                 durable authority
Persistent supervisor      deterministic lifecycle owner
Agent thread               bounded, replaceable working context
Live Terminal Console      operator observability only
```

The UI may observe runtime events. It never decides the next action or mutates
repository authority.

## Start

```bash
rsaw doctor . --agent codex
rsaw preview .
rsaw run . --agent codex
```

Interactive terminals receive the live console. Use `--no-tui` for plain output.
Non-TTY, CI, JSON, quiet, and dry-run execution falls back automatically.

## Runtime actions

| Action | Workstream | Agent context | Human action |
|---|---|---|---|
| CONTINUE | running | resume current thread | none |
| ROTATE | running | start fresh thread | none |
| PAUSE | paused | close or wait | required |
| COMPLETE | terminal | close | none |

Repository metadata remains backward compatible:

- `CONTINUE_ALLOWED` maps to CONTINUE when deterministic safety rules pass;
- `ROTATE_REQUIRED` maps to ROTATE;
- `STOP_REQUIRED` or a Human Gate maps to PAUSE;
- `COMPLETE` maps to COMPLETE.

## One checkpoint per turn

The supervisor asks each model turn to complete one durable repository checkpoint.
After the turn it verifies:

1. Codex exited successfully;
2. `ACTIVE.md` changed;
3. `rsaw verify` passes;
4. the next runtime action is valid.

A turn that returns success but leaves repository state unchanged fails closed.

The supervisor emits presentation events before and after observable lifecycle
steps, including turn start, repository verification, checkpoint acceptance,
rotation scheduling, and terminal state. Those events are also stored in the normal
runtime event log.

## Automatic rotation

ROTATE starts a new `codex exec` thread. CONTINUE uses `codex exec resume` with the
thread ID emitted by the preceding JSON event stream.

The supervisor also forces rotation when:

- `max_turns_per_epoch` is reached;
- the latest turn's input reaches `rotate_input_tokens`;
- a human gate was just resolved;
- repository state requests a role, review, or scientific boundary.

The Live Console briefly visualizes the transition, but does not delay or authorize
it.

## Human gates

In an interactive terminal, PAUSE displays the exact gate and accepts a human
response. RSAW temporarily releases live rendering, then runs a fresh gate-resolution
turn whose only job is to apply or reject the response through existing repository
governance.

The response is not stored in plaintext in runtime telemetry; only its SHA-256 is
logged. Non-interactive mode exits with PAUSED rather than inventing approval.

## Failure semantics

RSAW does not automatically retry a failed agent turn. It records a terminal summary
and leaves repository evidence untouched. The FAILED console state shows the concise
reason and evidence path; it never hides or replaces the underlying failure.

Presentation errors are isolated. A TUI event sink cannot cause an agent turn or
supervisor transition to fail.

## Runtime files

```text
.rsaw/runtime/
├── latest.json
└── rsaw-<timestamp>-<id>/
    ├── summary.json
    ├── supervisor-events.jsonl
    ├── turn-0001.jsonl
    └── turn-0001-last-message.txt
```

These files are ignored by default. Runtime summaries contain usage and transition
metadata, not hidden chain-of-thought.

## Limits

Configure `.rsaw/config.json` or CLI flags:

```bash
rsaw run . \
  --max-transitions 50 \
  --max-turns-per-epoch 4 \
  --rotate-input-tokens 50000 \
  --max-total-input-tokens 2000000
```

Limits protect the project from an unbounded controller loop; they are not claims
about an optimal context size.
