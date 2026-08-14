# Live Terminal UI

## Purpose

The Live Runtime Console turns structured Codex and supervisor events into an
operator-facing view inside normal terminals, especially VS Code Integrated Terminal.

## Information hierarchy

1. **NOW** — observable current activity.
2. **PROGRESS** — task, role, epoch, checkpoint, next action.
3. **CONTEXT** — pressure, cached input, fresh input, rotation reason.
4. **RECENT** — three to five high-value events.
5. **FOOTER** — durable state, gate, elapsed runtime.

## Motion

Motion communicates state only: one heartbeat, one activity spinner, smooth pressure
interpolation, checkpoint acceptance, and a brief ROTATE transition. PAUSE, FAILED,
and COMPLETE use stable unambiguous terminal states.

## Responsive behavior

Expanded layout is used when width and height permit. Compact layout keeps NOW,
checkpoint, action, context pressure, fresh input, and the latest event. Non-TTY output
uses plain logs without ANSI control sequences.

## Privacy and authority

The UI never displays hidden chain-of-thought. Reasoning events become a neutral
observable label. The model and renderer cannot decide continuation or change
repository authority.
