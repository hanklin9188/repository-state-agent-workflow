# Live Terminal UI

RSAW 0.4 adds an operator-facing runtime console for interactive terminals,
including the VS Code Integrated Terminal.

The UI is an observability layer. It does not become repository authority and it
does not alter CONTINUE, ROTATE, PAUSE, COMPLETE, verification, checkpoint, token,
or safety semantics.

## Start

```bash
rsaw preview .
rsaw run . --agent codex
```

`rsaw preview` is deterministic and non-destructive. It reads the current
repository authority, simulates representative runtime events, and never launches
Codex or changes project state.

## Selection rules

RSAW automatically enables the Live Terminal UI when:

- stdin and stdout are TTYs;
- the process is not running under `CI`;
- `TERM` is not `dumb`;
- output is not JSON;
- the command is not quiet or dry-run.

Override detection explicitly:

```bash
rsaw run . --tui
rsaw run . --no-tui
```

Redirected output and CI use plain output. RSAW does not emit live-render control
sequences into logs.

## Information hierarchy

The default view is intentionally limited to five operator questions.

### NOW

The latest observable Codex or supervisor activity:

- command execution;
- repository reads or edits;
- tool calls;
- validation;
- repository verification;
- checkpoint acceptance;
- context rotation.

The UI consumes structured Codex JSON events. It does not parse a visual Codex UI.
It never presents hidden chain-of-thought. Reasoning events become a neutral status
such as `Analyzing repository state`.

### PROGRESS

The dashboard shows:

- active task ID and title;
- current role and runtime epoch;
- accepted checkpoint count;
- next lifecycle action in human-readable form;
- next task when declared;
- a phase timeline only when the workstream exposes a bounded phase list and the
  current phase can be matched unambiguously.

RSAW never invents a global completion percentage or a checkpoint denominator.

### CONTEXT PRESSURE

```text
context pressure = latest turn input / configured rotate_input_tokens
```

This is an RSAW operating signal, not a claim about the provider's complete model
context-window utilization.

Health labels are deterministic:

- `GOOD` below 75%;
- `HIGH` from 75% to below 92%;
- `ROTATE SOON` at or above 92%.

The bar is visually interpolated for readability. The underlying telemetry remains
unchanged.

### TOKEN COST

The console shows provider-emitted values already collected by the Codex adapter:

- input;
- cached input;
- output;
- configured rotation threshold.

It derives:

```text
fresh input = max(0, input - cached input)
cache reuse = cached input / input
```

Dashboard rendering is local and never adds these labels or panels to model prompts.

### RECENT

Only the most useful recent events are shown. Validation outcomes, checkpoint
acceptance, failures, transitions, commands, and edits take precedence over raw
protocol noise. Full JSONL remains available under `.rsaw/runtime/`.

## Responsive layouts

The renderer uses the current terminal dimensions on every refresh.

- **Expanded**: full NOW, PROGRESS, CONTEXT PRESSURE, token, recent-event, and
  footer sections.
- **Compact**: current status, activity, phase, checkpoint, next action, context
  pressure, fresh input, and one recent event.

The UI updates in place. It does not append a new dashboard frame for every event.

## Motion policy

Motion communicates lifecycle state:

- heartbeat for active supervisor states;
- one spinner for active work;
- smooth pressure-bar interpolation;
- short ROTATE transition showing the old and new epochs;
- visible checkpoint acceptance;
- static, high-salience PAUSED and FAILED states;
- concise COMPLETE summary.

Animation is intentionally short and non-blocking. It never delays the supervisor
except for a small final-frame settle after terminal completion.

## Human gates

When an interactive gate requires exact input, RSAW:

1. renders `ACTION REQUIRED`;
2. temporarily suspends live rendering;
3. runs the existing exact gate prompt;
4. resumes the console afterward.

The response still flows through the existing gate resolver. The TUI never invents,
normalizes, or auto-approves authority.

## Presentation isolation

Both Supervisor and Codex adapter event sinks are best-effort. Exceptions raised by
the presentation layer are swallowed at the observability boundary so that a
renderer defect cannot fail an otherwise valid agent turn or alter lifecycle
semantics.

Runtime summaries and repository state remain authoritative.

## Testing contract

The TUI test suite covers:

- repository/task/phase snapshot construction;
- structured Codex event projection;
- hidden-reasoning suppression;
- input/cached/fresh/context-pressure calculations;
- expanded and compact rendering;
- narrow terminal widths;
- PAUSED, FAILED, LIMIT_REACHED, and COMPLETE views;
- TTY and non-TTY selection;
- Codex and Supervisor event forwarding;
- event-sink failure isolation.

Use `rsaw preview .` for an operator smoke test after installation.
