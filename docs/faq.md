# FAQ

## Is `ACTIVE.md` another project manager?

No. It is a tiny current-frontier pointer. GitHub Issues, Linear, Jira, or another tracker may remain the planning authority.

## Must every task start a fresh context?

No. RSAW 0.2 separates task checkpoints from context rotation. Closely coupled tasks may continue within one Context Epoch when the gate permits it.

## Is this now one long conversation?

No. A Persistent Workstream is long-lived; a Context Epoch is bounded. Role changes, scientific boundaries, human gates, long-running waits, major debugging residue, and context pressure require rotation.

## How does the agent know whether to continue?

`ACTIVE.md` proposes `CONTINUE_ALLOWED`, `ROTATE_REQUIRED`, or `STOP_REQUIRED`. `rsaw next .` applies deterministic checks, including next-task readiness, role changes, and human gates.

## What if I prefer RSAW 0.1 always-fresh behavior?

Keep using `ROTATE_REQUIRED`. Existing 0.1 repositories remain supported.

## Does RSAW automatically open a new agent session?

No. RSAW is not an orchestration platform. It renders prompts and makes repository state sufficient for a human or external tool to start a fresh context.

## What if a task requires broad architecture context?

Use progressive disclosure. Broad context is allowed when the task requires it; it should not be the default preload.

## Does this work only with Codex?

No. RSAW is Markdown- and Git-based. Agent-specific instruction discovery varies, but the state architecture is tool-agnostic.

## Is conversation history useless?

No. It is useful working memory. It simply is not the authoritative project database.

## Does a fresh context lose useful debugging knowledge?

Only when durable conclusions were not checkpointed. Record the accepted mechanism, test, commit, evidence, and next action—not the entire exploratory transcript.

## Will RSAW always save 80–90% of tokens?

No. The measured 91.1% result is a bootstrap estimate from one RSAW 0.1 case study. RSAW 0.2 task-stream token and quality effects remain hypotheses to test.

## Why not learn the rotation decision with a model?

A learned gate may be future research. Version 0.2 deliberately uses explicit repository state and deterministic safety rules so decisions remain inspectable.
