# FAQ

## Does a workstream still stop at every rotation?

No. In 0.3, ROTATE means the workstream stays running while the supervisor
starts a fresh Codex thread. PAUSE is the only ordinary human/external stop.

## Does RSAW create a new ChatGPT web conversation?

No. Automatic runtime mode controls local Codex CLI threads through
`codex exec`. Manual prompt mode remains available for web or other agents.

## Must every task use a fresh context?

No. Closely coupled same-role tasks may share one bounded epoch. Every task still
writes a durable checkpoint.

## Will the supervisor approve commands or experiments for me?

No. Human gates remain explicit. RSAW never invents authorization, credentials,
privilege, destructive consent, or scientific judgment.

## Is automatic approval enabled by default?

No. The Codex adapter defaults to `workspace-write` sandboxing. `--approve-for-me`
is an explicit opt-in. Dangerous sandbox/approval bypass is never enabled by
RSAW.

## What happens if an agent fails?

The supervisor records a terminal failure and does not retry automatically. The
repository or a human must authorize the next action.

## How is context bounded?

Repository rotation rules, maximum turns per epoch, per-turn input pressure,
maximum total input, and transition limits all constrain the runtime.

## Is runtime telemetry committed?

No. `.rsaw/runtime/` is ignored by default. Publish only intentionally selected,
reviewed aggregate results.

## Does 0.3 prove more token savings than 0.2?

Not yet. It records prospective provider usage needed to evaluate that question.
Existing v1/v2 numbers remain scoped case-study estimates.

## Does RSAW replace an issue tracker or CI?

No. It is a repository-local continuity and runtime contract that complements
planning, review, CI, access control, and experiment infrastructure.
