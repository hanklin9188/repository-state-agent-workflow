# Runtime Supervisor

RSAW Core decides whether repository work should continue, rotate, pause, or
complete. The Runtime Supervisor executes that decision for a local agent.

## Why it exists

RSAW 0.2 could generate a fresh prompt, but a human still had to create the next
agent session. That made `ROTATE_REQUIRED` a manual relay even though the
workstream itself was not blocked.

RSAW 0.3 separates:

```text
Persistent supervisor   long-lived, deterministic, no conversational memory
Agent thread             bounded, replaceable working context
Repository               durable authority
```

## Start

```bash
rsaw doctor . --agent codex
rsaw run . --agent codex
```

## Runtime actions

| Action | Workstream | Agent context | Human action |
|---|---|---|---|
| CONTINUE | running | resume current thread | none |
| ROTATE | running | start fresh thread | none |
| PAUSE | paused | close/wait | required |
| COMPLETE | terminal | close | none |

Repository metadata remains backward compatible:

- `CONTINUE_ALLOWED` maps to CONTINUE when deterministic safety rules pass;
- `ROTATE_REQUIRED` maps to ROTATE;
- `STOP_REQUIRED` or a Human Gate maps to PAUSE;
- `COMPLETE` maps to COMPLETE.

## One checkpoint per turn

The supervisor asks each model turn to complete one durable repository
checkpoint. After the turn it verifies:

1. Codex exited successfully;
2. `ACTIVE.md` changed;
3. `rsaw verify` passes;
4. the next runtime action is valid.

A turn that returns success but leaves repository state unchanged fails closed.

## Automatic rotation

ROTATE starts a new `codex exec` thread. CONTINUE uses `codex exec resume` with
the thread ID emitted by the preceding JSON event stream.

The supervisor also forces rotation when:

- `max_turns_per_epoch` is reached;
- the latest turn's input usage reaches `rotate_input_tokens`;
- a human gate was just resolved;
- repository state requests a role/scientific boundary.

## Human gates

In an interactive terminal, PAUSE prints the exact gate and accepts a human
response. RSAW runs a fresh gate-resolution turn whose only job is to apply or
reject the response through existing repository governance. The response is not
stored in plaintext in runtime telemetry; only its SHA-256 is logged.

Non-interactive mode exits with a PAUSED status instead of inventing approval.

## Failure semantics

RSAW does not automatically retry a failed agent turn. It records a terminal
summary and leaves repository evidence untouched. The next action must come from
repository governance or a human decision.

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

These files are ignored by default. Runtime summaries contain usage and
transition metadata, not hidden chain-of-thought.

## Limits

Configure `.rsaw/config.json` or CLI flags:

```bash
rsaw run . \
  --max-transitions 50 \
  --max-turns-per-epoch 4 \
  --rotate-input-tokens 50000 \
  --max-total-input-tokens 2000000
```

Limits protect the project from an unbounded controller loop; they are not
claims about an optimal context size.
