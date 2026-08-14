# Codex Runtime Adapter

The first RSAW Runtime adapter targets the local Codex CLI.

## Requirements

- `codex` available on `PATH` or supplied with `--codex-bin`;
- authenticated Codex CLI;
- a Git repository with valid RSAW state;
- Codex support for `exec`, JSON output, resume, and last-message output.

Check compatibility:

```bash
rsaw doctor . --agent codex
```

## Fresh and continued turns

Fresh epoch:

```text
codex exec --json --output-last-message ... -
```

Continued epoch:

```text
codex exec --json --output-last-message ... resume <thread-id> -
```

Prompts are passed through stdin. RSAW captures the thread ID from `thread.started`
and usage from `turn.completed`.

## Live observability

RSAW 0.4 forwards parsed structured events to an optional presentation sink while
preserving the raw JSONL event stream.

The Live Terminal Console projects observable events into human-readable activity:

- command execution;
- file reads and edits;
- tool calls and searches;
- validation and checkpoint state;
- turn completion and usage;
- errors.

The adapter does not expose hidden chain-of-thought. Reasoning event payloads are not
rendered. Non-JSON diagnostics may be shown as concise diagnostics and remain stored
in the raw log.

Event-sink exceptions are ignored at the observability boundary. Presentation can
never change turn success, timeout handling, process ownership, or lifecycle state.

## Sandbox policy

Default:

```text
workspace-write
```

RSAW never passes Codex's dangerous approval/sandbox bypass. Automatic approval
review is available only through explicit `--approve-for-me` opt-in.

## Model and profile

```bash
rsaw run . --model <model>
rsaw run . --profile <profile>
```

RSAW does not silently select a stronger model at role boundaries. Model and profile
policy must remain explicit in the command, user Codex config, or repository runtime
policy.

## Events and usage

The adapter stores JSONL and aggregates:

- input tokens;
- cached input tokens;
- cache-write input tokens;
- output tokens;
- reasoning-output tokens.

The dashboard derives fresh input locally. It does not add UI text to prompts or
create extra model turns.

## What the adapter does not do

- create ChatGPT web conversations;
- bypass repository authorization;
- infer human approval;
- retry failed formal runs;
- expose hidden chain-of-thought;
- replace Codex authentication or sandbox policy;
- recreate the native Codex TUI.
