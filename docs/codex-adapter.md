# Codex Runtime Adapter

The first RSAW Runtime adapter targets the local Codex CLI.

## Requirements

- `codex` available on `PATH` or supplied with `--codex-bin`;
- authenticated Codex CLI;
- a Git repository with valid RSAW state;
- Codex version supporting `exec`, JSON output, resume, and last-message output.

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

Prompts are passed through stdin. RSAW captures the thread ID from
`thread.started` and usage from `turn.completed`.

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

RSAW does not silently select a stronger model at role boundaries. Model and
profile policy should be explicit in the command, user Codex config, or a future
repository runtime policy.

## Events and usage

The adapter stores JSONL events and aggregates:

- input tokens;
- cached input tokens;
- cache-write input tokens;
- output tokens;
- reasoning output tokens.

Non-JSON diagnostics are preserved in the raw event log but ignored by the
usage parser.

## What the adapter does not do

- create ChatGPT web conversations;
- bypass repository authorization;
- infer human approval;
- retry failed formal runs;
- expose hidden chain-of-thought;
- replace Codex authentication or sandbox policy.
